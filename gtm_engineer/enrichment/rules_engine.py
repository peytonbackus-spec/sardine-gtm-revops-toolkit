import asyncio
import logging
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)

class AttributeDict(dict):
    def __getattr__(self, attr):
        val = self.get(attr)
        if isinstance(val, dict) and not isinstance(val, AttributeDict):
            return AttributeDict(val)
        return val

    def __getitem__(self, item):
        val = super().__getitem__(item)
        if isinstance(val, dict) and not isinstance(val, AttributeDict):
            return AttributeDict(val)
        return val

    def __setattr__(self, attr, value):
        self[attr] = value

class WaterfallEnrichmentEngine:
    def __init__(self, config_path: str):
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
        
        self.settings = self.config.get("engine_settings", {})
        self.waterfalls = self.config.get("waterfalls", {})

    async def _call_provider(
        self, provider: str, action: str, params: Dict[str, Any], payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        await asyncio.sleep(0.01)
        
        if provider == "zerobounce" and payload.get("email"):
            return {"status": "valid", "score": 98}
        elif provider == "clay" and payload.get("email"):
            return {"contact": {"email": payload["email"], "title": "VP of Revenue Operations"}}
        elif provider == "clearbit" and payload.get("domain"):
            return {"account": {"employee_count": 250, "industry": "Software"}}
            
        return {}

    def _evaluate_condition(self, condition: str, state: Dict[str, Any]) -> bool:
        if condition == "always" or not condition:
            return True
            
        try:
            attr_state = AttributeDict(state) if not isinstance(state, AttributeDict) else state
            return bool(eval(condition, attr_state))
        except Exception as e:
            logger.warning(f"Condition evaluation failed for '{condition}': {e}")
            return False

    def _check_success(self, success_criteria: Optional[str], step_result: Dict[str, Any]) -> bool:
        if not success_criteria or not step_result:
            return bool(step_result)
            
        try:
            attr_result = AttributeDict(step_result) if not isinstance(step_result, AttributeDict) else step_result
            return bool(eval(success_criteria, attr_result))
        except Exception:
            return False

    async def execute_waterfall_stage(
        self, stage_name: str, input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        stage_config = self.waterfalls.get(stage_name)
        if not stage_config:
            raise ValueError(f"Waterfall stage '{stage_name}' not defined in config.")

        pipeline_state = input_data.copy()
        stop_on_first = stage_config.get("stop_on_first_match", self.settings.get("stop_on_first_match", True))

        for step in stage_config.get("sequence", []):
            provider = step["provider"]
            action = step["action"]
            condition = step.get("condition", "always")
            success_criteria = step.get("success_criteria")
            params = step.get("params", {})

            if not self._evaluate_condition(condition, pipeline_state):
                continue

            try:
                result = await self._call_provider(provider, action, params, pipeline_state)
            except Exception as e:
                logger.error(f"Provider {provider} execution failed: {e}")
                continue

            if result:
                pipeline_state[provider] = result
                pipeline_state.update(result)

            if result and self._check_success(success_criteria, result):
                if stop_on_first:
                    break

        return pipeline_state

    async def execute_full_pipeline(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        current_state = input_data.copy()
        for stage_name in self.waterfalls.keys():
            current_state = await self.execute_waterfall_stage(stage_name, current_state)
        return current_state

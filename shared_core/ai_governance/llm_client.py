"""Provider-agnostic LLM client with a deterministic offline mode.

Every AI workflow in the repo calls `complete_json()`. In the default `mock` mode
the caller supplies a deterministic responder, so the whole repo runs, tests and
evaluates with no API key and no data leaving the machine. Set
GTM_LLM_MODE=anthropic (plus ANTHROPIC_API_KEY and ANTHROPIC_MODEL) to run the
same prompts against a live model. The guardrails are identical in both modes:

  * input passes through pii_guard.sanitize_record (allow-list + redaction)
  * output must be JSON with the declared keys or it is rejected
  * every call is logged to outputs/ai_audit_log.jsonl (prompt id, version, mode, keys, PII audit)
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from shared_core.ai_governance.pii_guard import sanitize_record
from shared_core.config import OUTPUT_DIR, ROOT

PROMPT_DIR_NAMES = ("prompts",)


class OutputContractError(ValueError):
    """Model output was not valid JSON or was missing required keys."""


def load_prompt(path: str | Path) -> tuple[str, str]:
    """Load a prompt markdown file. Returns (prompt_id@version, system_prompt_text).

    Prompt files carry a front-matter style header:  id: x / version: y
    and the system prompt after a line containing only '---'.
    """
    text = Path(path).read_text(encoding="utf-8")
    header, _, body = text.partition("\n---\n")
    meta = dict(line.split(":", 1) for line in header.splitlines() if ":" in line)
    pid = f"{meta.get('id', Path(path).stem).strip()}@{meta.get('version', '0').strip()}"
    return pid, body.strip()


class LLMClient:
    def __init__(self, mode: str | None = None):
        self.mode = (mode or os.getenv("GTM_LLM_MODE", "mock")).lower()
        self._client = None
        if self.mode == "anthropic":
            import anthropic  # optional dependency, only needed for live mode

            self._client = anthropic.Anthropic()
            self.model = os.environ["ANTHROPIC_MODEL"]  # set explicitly; no silent default

    def complete_json(self, *, prompt_id: str, system: str, record: dict, required_keys: list[str],
                      mock_responder: Callable[[dict], dict], task: str = "") -> dict:
        clean, pii_audit = sanitize_record(record)
        if self.mode == "mock":
            out = mock_responder(clean)
        else:
            msg = self._client.messages.create(
                model=self.model, max_tokens=1200, system=system,
                messages=[{"role": "user", "content": f"{task}\n\nRECORD (JSON):\n{json.dumps(clean, default=str)}\n\n"
                                                      f"Respond with JSON only, keys: {required_keys}"}],
            )
            raw = msg.content[0].text.strip().removeprefix("```json").removesuffix("```").strip()
            try:
                out = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise OutputContractError(f"{prompt_id}: non-JSON output") from exc
        missing = [k for k in required_keys if k not in out]
        if missing:
            raise OutputContractError(f"{prompt_id}: missing keys {missing}")
        self._audit(prompt_id, clean, pii_audit, out)
        return out

    def _audit(self, prompt_id: str, clean: dict, pii_audit: list[str], out: dict) -> None:
        OUTPUT_DIR.mkdir(exist_ok=True)
        entry = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "prompt": prompt_id, "mode": self.mode,
                 "input_fields": sorted(clean), "pii_actions": pii_audit, "output_keys": sorted(out)}
        with open(OUTPUT_DIR / "ai_audit_log.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")


def repo_path(*parts: str) -> Path:
    return ROOT.joinpath(*parts)

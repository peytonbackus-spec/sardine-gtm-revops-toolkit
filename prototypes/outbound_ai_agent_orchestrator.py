"""
---
type: resource
category: code
tags:
  - resource
  - python
  - ai-agents
  - outbound
status: active
last_updated: 2026-08-21
---
"""

from typing import Any, Dict


class OutboundResearchAgent:
    """AI Agent framework to generate personalized outbound messaging based on firmographic signals."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key

    def synthesize_account_signals(self, company_data: Dict[str, Any]) -> str:
        """Extracts core GTM pain points from company firmographic metadata."""
        company_name = company_data.get("name", "Target Account")
        growth_rate = company_data.get("headcount_growth_yo_y", 0.0)
        crm_stack = company_data.get("crm_stack", [])

        if "Salesforce" in crm_stack and growth_rate > 0.20:
            return f"{company_name} is scaling rapidly ({int(growth_rate*100)}% YoY) on Salesforce, creating Lead-to-Account routing and data sync overhead."
        elif "HubSpot" in crm_stack:
            return f"{company_name} relies on HubSpot, requiring front-to-back RevOps pipeline attribution models."
        return f"{company_name} is optimizing GTM architecture and revenue efficiency."

    def generate_personalized_prompt(self, prospect: Dict[str, Any], signal_summary: str) -> str:
        """Generates structured LLM prompt for outreach customization."""
        return f"""
System: You are an expert RevOps and GTM Engineer.
Context: {signal_summary}
Target Prospect: {prospect.get("name")}, {prospect.get("title")} at {prospect.get("company")}.
Task: Draft a concise 3-sentence outreach email referencing their current stack and operational scaling bottlenecks.
""".strip()

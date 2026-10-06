import json


class GTMAgent:
    def __init__(self, crm_api_key: str, llm_api_key: str):
        self.crm_api_key = crm_api_key
        self.llm_api_key = llm_api_key

    def evaluate_icp_fit(self, lead_data: dict) -> dict:
        emp_count = lead_data.get("employee_count", 0)
        title = lead_data.get("title", "").lower()
        is_icp = emp_count >= 50 and any(k in title for k in ["revops", "sales", "gtm", "operations", "engineering"])
        return {"contact_id": lead_data.get("id"), "icp_fit": is_icp, "route_to": "AE_Tier_1" if is_icp else "Self_Serve_Nurture", "confidence_score": 0.95 if is_icp else 0.40}

if __name__ == "__main__":
    sample_lead = {"id": "cnt_99812", "first_name": "Alex", "company": "ScaleWorks", "title": "Head of Revenue Operations", "employee_count": 120}
    agent = GTMAgent("demo", "demo")
    print("Agent Qualification Result:", json.dumps(agent.evaluate_icp_fit(sample_lead), indent=2))

"""
---
type: resource
category: code
tags:
  - resource
  - python
  - apollo
  - ai-agents
status: active
last_updated: 2026-08-21
---
"""

import os

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
HUBSPOT_ACCESS_TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN")

@app.route("/webhooks/enrich-lead", methods=["POST"])
def enrich_lead():
    data = request.json
    email = data.get("email")
    hs_object_id = data.get("hs_object_id")
    
    if not email or not hs_object_id:
        return jsonify({"status": "error", "message": "Missing email or object ID"}), 400

    apollo_url = "https://api.apollo.io/v1/people/match"
    headers = {"Cache-Control": "no-cache", "Content-Type": "application/json"}
    payload = {"api_key": APOLLO_API_KEY, "email": email}
    
    response = requests.post(apollo_url, headers=headers, json=payload)
    if response.status_code != 200 or not response.json().get("person"):
        return jsonify({"status": "failed", "reason": "Person not found in Apollo"}), 404
    
    person = response.json()["person"]
    org = person.get("organization", {})

    employee_count = org.get("estimated_num_employees", 0)
    industry = org.get("industry", "Unknown")
    title = person.get("title", "")
    
    tier = "Tier 3"
    if employee_count >= 250 and ("Director" in title or "VP" in title or "Head" in title):
        tier = "Tier 1"
    elif employee_count >= 50:
        tier = "Tier 2"

    hs_update_url = f"https://api.hubapi.com/crm/v3/objects/contacts/{hs_object_id}"
    hs_headers = {
        "Authorization": f"Bearer {HUBSPOT_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    hs_payload = {
        "properties": {
            "numemployees": str(employee_count),
            "industry": industry,
            "jobtitle": title,
            "target_account_tier": tier
        }
    }
    
    hs_response = requests.patch(hs_update_url, headers=hs_headers, json=hs_payload)
    
    return jsonify({
        "status": "success",
        "email": email,
        "assigned_tier": tier,
        "hubspot_status": hs_response.status_code
    }), 200

if __name__ == "__main__":
    app.run(port=5000)

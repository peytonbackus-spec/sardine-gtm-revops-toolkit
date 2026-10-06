import os

import requests

HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY")

def route_lead(contact_id, territory):
    """Routes HubSpot contact to appropriate rep based on territory rules."""
    rep_mapping = {
        "AMER_EAST": "owner_123",
        "AMER_WEST": "owner_456",
        "EMEA": "owner_789"
    }
    
    owner_id = rep_mapping.get(territory, "owner_default")
    url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
    headers = {"Authorization": f"Bearer {HUBSPOT_API_KEY}", "Content-Type": "application/json"}
    payload = {"properties": {"hubspot_owner_id": owner_id}}
    
    response = requests.patch(url, json=payload, headers=headers)
    return response.status_code

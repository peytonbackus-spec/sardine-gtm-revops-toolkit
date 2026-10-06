from fastapi.testclient import TestClient

from gtm_engineer.integrations.webhook import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "engine_loaded": True}

def test_enrich_lead_valid_payload():
    payload = {
        "email": "pat@stripe.com",
        "domain": "stripe.com"
    }
    response = client.post("/api/v1/enrich", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"
    assert data["input_payload"]["email"] == "pat@stripe.com"
    assert "zerobounce" in data["enriched_data"]
    assert data["enriched_data"]["zerobounce"]["status"] == "valid"

def test_enrich_lead_invalid_email():
    payload = {
        "email": "invalid-email-format",
        "domain": "stripe.com"
    }
    response = client.post("/api/v1/enrich", json=payload)
    assert response.status_code == 422  # Unprocessable Entity (Pydantic validation failure)

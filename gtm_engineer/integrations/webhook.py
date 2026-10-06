from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

from gtm_engineer.enrichment.rules_engine import WaterfallEnrichmentEngine

app = FastAPI(
    title="GTM Waterfall Enrichment API",
    description="Asynchronous engine for signal-based GTM enrichment cascades.",
    version="1.0.0",
)

engine = WaterfallEnrichmentEngine("config/waterfall_rules.yaml")

class EnrichmentRequest(BaseModel):
    email: EmailStr
    domain: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class EnrichmentResponse(BaseModel):
    status: str
    input_payload: Dict[str, Any]
    enriched_data: Dict[str, Any]

@app.get("/health")
async def health_check():
    return {"status": "healthy", "engine_loaded": True}

@app.post("/api/v1/enrich", response_model=EnrichmentResponse)
async def enrich_lead(payload: EnrichmentRequest):
    try:
        input_data = payload.model_dump(exclude_none=True)
        enriched_result = await engine.execute_full_pipeline(input_data)
        
        return EnrichmentResponse(
            status="success",
            input_payload=input_data,
            enriched_data=enriched_result,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Waterfall enrichment failed: {e!s}") from e

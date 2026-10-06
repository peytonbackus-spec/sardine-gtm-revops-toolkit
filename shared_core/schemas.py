from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, model_validator


class MatchConfidence(str, Enum):
    EXACT = "exact"
    FUZZY_HIGH = "fuzzy_high"
    FUZZY_LOW = "fuzzy_low"
    MANUAL_REVIEW = "manual_review"

class Contact(BaseModel):
    id: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    job_title: Optional[str] = None
    domain: Optional[str] = None
    raw_payload: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def extract_domain(self) -> "Contact":
        if self.email and not self.domain:
            domain_part = self.email.split("@")[-1].lower()
            if domain_part not in {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com"}:
                self.domain = domain_part
        return self

class Account(BaseModel):
    id: str
    name: str
    primary_domain: str
    secondary_domains: List[str] = Field(default_factory=list)
    tax_id: Optional[str] = None
    employee_count: Optional[int] = None
    industry: Optional[str] = None

class Deal(BaseModel):
    id: str
    account_id: str
    amount: float
    stage: str
    meddpicc_score: Optional[Dict[str, Any]] = None

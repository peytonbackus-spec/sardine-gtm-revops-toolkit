"""PII guard: strip identity and financial data before anything reaches a model.

If the company's customers send it sensitive data (identity documents, financial
records, health data), a GTM workflow has to be stricter about what reaches a prompt
than a typical SaaS company. That's the reason for this file: it is the enforcement
point for "apply governance for data security and responsible AI use".
Tighten PROMPT_SAFE_FIELDS to match your data.

Two layers:
  1. Field allow-list: only named CRM fields may enter a prompt (deny by default).
  2. Pattern redaction on free text (notes, emails, call summaries).
"""
from __future__ import annotations

import re

# Fields that may be sent to a model. Anything else is dropped.
PROMPT_SAFE_FIELDS = {
    "account_name", "company", "segment", "region", "employees", "title", "persona",
    "lead_source", "product_interest", "intent_signals", "is_existing_customer", "products_owned",
    "type", "product_line", "amount", "stage", "forecast_category", "close_date", "stage_entered_date",
    "last_activity_date", "contacts_engaged", "economic_buyer_engaged", "poc_status", "security_review",
    "next_step", "competitor", "arr", "renewal_date", "volume_trend_90d_pct", "utilization_pct",
    "sev1_tickets_90d", "exec_sponsor_active", "competitor_signal", "notes", "partner", "source",
    # region-level forecast aggregates (no contact data)
    "quarter", "quota", "commit", "high_risk_count", "high_risk_amount", "high_risk_commit", "top_deals",
}

PATTERNS = [
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("CARD", re.compile(r"\b(?:\d[ -]?){13,19}\b")),
    ("ROUTING_OR_ACCOUNT", re.compile(r"\b\d{9,17}\b")),
    ("PHONE", re.compile(r"(?:\+?1[ .-]?)?\(?\d{3}\)?[ .-]?\d{3}[ .-]?\d{4}\b")),
    ("DOB", re.compile(r"\b(?:DOB|date of birth)[:\s]*\d{1,4}[/-]\d{1,2}[/-]\d{1,4}\b", re.I)),
]


def redact_text(text: str) -> tuple[str, list[str]]:
    """Return (redacted_text, list_of_pii_types_found)."""
    found = []
    for label, pattern in PATTERNS:
        if pattern.search(text):
            found.append(label)
            text = pattern.sub(f"[{label}_REDACTED]", text)
    return text, found


def sanitize_record(record: dict) -> tuple[dict, list[str]]:
    """Allow-list the fields, then redact any free text. Returns (clean_record, audit_log)."""
    audit = []
    clean = {}
    for key, value in record.items():
        if key not in PROMPT_SAFE_FIELDS:
            if value not in ("", None):
                audit.append(f"dropped field '{key}'")
            continue
        if isinstance(value, str):
            value, found = redact_text(value)
            audit += [f"redacted {t} in '{key}'" for t in found]
        clean[key] = value
    return clean, audit


def contains_pii(text: str) -> bool:
    return bool(redact_text(text)[1])

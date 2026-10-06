"""🟪 Shared core: config, data quality, PII guard, HITL, SQL/Python parity."""
from datetime import date

import pytest

from shared_core.ai_governance.hitl import HITLPolicy
from shared_core.ai_governance.llm_client import LLMClient, OutputContractError
from shared_core.ai_governance.pii_guard import contains_pii, sanitize_record
from shared_core.config import dedupe_leads, fiscal_quarter, load_config, read_csv
from shared_core.data_quality.dq_monitor import run as run_dq
from shared_core.metrics.run_sql import load_warehouse


def test_config_is_complete_and_internally_consistent():
    cfg = load_config()
    assert {"compliance", "fraud"} <= set(cfg["product_lines"])
    for key in ("crm", "forecasting", "sales_engagement", "enrichment_orchestration"):
        assert cfg["stack"][key]
    assert abs(sum(cfg["renewals"]["health_weights"].values()) - 1.0) < 1e-9
    # every segment/persona referenced by routing and alignment rules must exist
    for rule in cfg["lead_routing"]["pods"].values():
        assert all(s == "*" or s in cfg["segments"] for s in rule["segments"])
    assert cfg["current_fiscal_quarter"] in cfg["quota"]
    # every bracketed variable token the docs use must be defined
    assert {"COMPANY_NAME", "CRM", "FORECAST_TOOL", "SEQUENCER"} <= set(cfg["variables"])


def test_fiscal_quarter_follows_configured_start_month():
    assert fiscal_quarter(date(2026, 10, 1), 10) == "FY27-Q1"
    assert fiscal_quarter(date(2026, 9, 30), 10) == "FY26-Q4"
    assert fiscal_quarter(date(2026, 1, 15), 10) == "FY26-Q2"
    assert fiscal_quarter(date(2026, 10, 1), 1) == "FY26-Q4"   # calendar-year company
    assert fiscal_quarter(date(2027, 1, 1), 1) == "FY27-Q1"


def test_fiscal_quarter_python_and_sql_agree():
    con = load_warehouse()
    rows = con.execute("SELECT close_date, close_fiscal_quarter FROM v_opportunities").fetchall()
    assert rows
    for close_date, fq in rows:
        assert fiscal_quarter(date.fromisoformat(close_date)) == fq


def test_dq_monitor_catches_planted_issues():
    out = run_dq()
    failed = {r["rule"]: r["failed"] for r in out["results"]}
    for rule in ("L01", "L03", "O03", "O05", "R01"):
        assert failed[rule] > 0, f"planted issue for {rule} not caught"
    assert all(f["owner_role"] for f in out["failures"])


def test_dq_rule_on_clean_record_passes():
    clean_opp = {"opportunity_id": "X", "is_closed": "False", "close_date": "2026-12-01", "amount": "100000",
                 "stage": "2 - Discovery", "closed_lost_reason": "", "next_step": "Call", "forecast_category": "Pipeline",
                 "economic_buyer_engaged": "True", "source": "AE", "partner": "", "originating_lead_id": ""}
    out = run_dq(leads=[], opps=[clean_opp])
    assert all(r["failed"] == 0 for r in out["results"] if r["object"] == "Opportunity")


def test_pii_guard_drops_unlisted_fields_and_redacts_text():
    clean, audit = sanitize_record({"company": "X", "email": "a@b.com", "ssn": "123-45-6789",
                                    "notes": "call 415-555-0199 or a@b.com, acct 000123456789"})
    assert "email" not in clean and "ssn" not in clean
    assert not contains_pii(clean["notes"])
    assert any("dropped field 'email'" in a for a in audit)


def test_llm_client_rejects_output_missing_contract_keys():
    with pytest.raises(OutputContractError):
        LLMClient(mode="mock").complete_json(prompt_id="t@1", system="", record={"company": "X"},
                                             required_keys=["a", "b"], mock_responder=lambda r: {"a": 1})


def test_hitl_policy_always_reviews_revenue_actions():
    p = HITLPolicy()
    assert p.decide("change_forecast_category", 0.99) == "human_review"
    assert p.decide("enroll_cadence", 0.99) == "auto_apply"
    assert p.decide("enroll_cadence", 0.99, amount=500_000) == "human_review"
    assert p.decide("enroll_cadence", 0.5) == "human_review"


def test_dedupe_matches_sql_duplicate_flag():
    leads = read_csv("leads.csv")
    con = load_warehouse()
    sql_unique = con.execute("SELECT COUNT(*) FROM v_leads WHERE is_duplicate = 0").fetchone()[0]
    assert len(dedupe_leads(leads)) == sql_unique

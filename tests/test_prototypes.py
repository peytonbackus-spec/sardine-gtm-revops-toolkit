"""Smoke tests for the unrefactored scripts in prototypes/.

These keep the prototypes honest (they import and return the documented shape) without
claiming production quality. When a prototype is promoted into a track, move its test
into that track's test file.
"""
from prototypes.churn_prediction_pipeline import AccountChurnPredictor
from prototypes.meddpicc_health_engine import MEDDPICCHealthEngine
from prototypes.revops_tech_debt_tracker import RevOpsTechDebtAuditor


def test_meddpicc_health_engine():
    opp = {"Quantified_ROI__c": True, "Economic_Buyer_Contacted__c": True, "Quantified_Pain__c": True,
           "Primary_Champion__c": "0038000000iD34AAAS", "Paper_Process_Stage__c": "Procurement Approved"}
    res = MEDDPICCHealthEngine.calculate_deal_health(opp)
    assert res["health_score"] >= 80 and res["qualified_for_stage_4"]


def test_churn_prediction_critical():
    res = AccountChurnPredictor({"account_id": "001XYZ", "wau_change_pct": -40.0,
                                 "has_active_exec_sponsor": False, "open_escalated_tickets": 2}).predict_risk()
    assert res["risk_level"] == "CRITICAL"


def test_tech_debt_auditor_flags_unused_field():
    schema = [{"api_name": "Unused_Field__c", "population_rate_pct": 0.0, "days_since_last_modified": 200}]
    res = RevOpsTechDebtAuditor(schema).run_schema_audit()
    assert len(res) == 1 and res[0]["severity"] == "HIGH"

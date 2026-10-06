"""🟦 GTM Engineer track."""
from datetime import date

from gtm_engineer.funnel_analytics.funnel_report import cohort_funnel, early_pipeline_outlook
from gtm_engineer.lead_lifecycle.lifecycle_sla import sla_report
from gtm_engineer.lead_routing.route_leads import Router
from gtm_engineer.lead_scoring.calibrate_scoring import conversion_by, is_monotonic, matured
from gtm_engineer.lead_scoring.score_leads import fit_score, grade, intent_score, score_all
from gtm_engineer.sdr_capacity.capacity_model import capacity
from shared_core.config import dedupe_leads, load_config, read_csv
from shared_core.metrics.run_sql import run_file

CFG = load_config()


def lead(**kw):
    base = {"lead_id": "L-T", "segment": "fintech_neobank", "persona": "head_of_fraud", "region": "NA",
            "employees": "4000", "product_interest": "compliance", "intent_signals": "",
            "is_existing_customer": "False", "email": "x@acme.example", "account_id": "A1", "partner": "",
            "created_date": "2026-09-01"}
    base.update(kw)
    return base


def test_icp_fintech_head_of_fraud_is_a_grade():
    assert fit_score(lead(), CFG) >= CFG["lead_scoring"]["fit_bands"]["A"]


def test_non_icp_student_is_d_grade():
    assert fit_score(lead(segment="other", persona="unknown", employees="5"), CFG) < 45


def test_intent_decays_with_half_life():
    fresh = intent_score(lead(intent_signals="demo_request@2026-09-30"), CFG, as_of=date(2026, 10, 1))
    old = intent_score(lead(intent_signals="demo_request@2026-08-01"), CFG, as_of=date(2026, 10, 1))
    assert fresh > old * 4


def test_grade_format():
    assert grade(85, 70, CFG) == "A1" and grade(10, 0, CFG) == "D4"


def test_scoring_is_monotonic_on_sample_data():
    rows = matured(score_all(read_csv("leads.csv"), CFG, point_in_time_days=7))
    assert is_monotonic(conversion_by(rows, lambda r: r["grade"][0]))


def make_router(open_opps=None, owners=None):
    return Router(CFG, open_opps or {}, owners or {})


def test_routing_rule_order():
    r = make_router(open_opps={"A1": "AE - Open Owner"}, owners={"A2": "AE - Acct Owner"})
    assert r.route(lead(segment="other"))["routing_rule"] == "R1"
    assert r.route(lead(account_id="A1"))["routed_to"] == "AE - Open Owner"
    assert r.route(lead(account_id="A2", is_existing_customer="True"))["routing_rule"] == "R3"
    assert r.route(lead(account_id="A3", partner="Helix by Q2"))["routing_rule"] == "R4"
    assert r.route(lead(account_id="A3", recommendation="Nurture"))["routing_rule"] == "R5"
    mql = r.route(lead(account_id="A3", recommendation="MQL -> route to SDR now"))
    assert mql["routing_rule"] == "R6" and mql["routed_to"].startswith("SDR")
    blank_region = r.route(lead(account_id="A3", region="", recommendation="MQL -> route to SDR now"))
    assert blank_region["routing_rule"] == "R7"


def test_round_robin_balances_load():
    r = make_router()
    owners = [r.route(lead(account_id=f"N{i}", recommendation="MQL -> route to SDR now"))["routed_to"] for i in range(10)]
    assert abs(owners.count(owners[0]) - 5) <= 1


def test_sla_report_has_owner_and_source_views():
    rep = sla_report(read_csv("leads.csv"), CFG)
    assert 0 < rep["overall_%"] < 100 and rep["by_owner"] and rep["by_source"]


def test_python_funnel_matches_sql_funnel():
    py = {c["cohort"]: c for c in cohort_funnel(dedupe_leads(read_csv("leads.csv")))}
    sql = run_file("gtm_engineer/funnel_analytics/sql/lead_funnel.sql")[0]
    for row in sql:
        assert py[row["cohort"]]["leads"] == row["leads"]
        assert py[row["cohort"]]["opp_%"] == row["opp_pct"]


def test_early_pipeline_outlook_range_brackets_point_estimate():
    leads = read_csv("leads.csv")
    out = early_pipeline_outlook(leads, {o["opportunity_id"]: o for o in read_csv("opportunities.csv")})
    lo, hi = out["range_$"]
    assert lo <= out["expected_pipeline_$"] <= hi


def test_capacity_model_scales_linearly_with_target():
    a = capacity(3_000_000, 100_000, 0.5, 0.6, 0.4, 14)
    b = capacity(6_000_000, 100_000, 0.5, 0.6, 0.4, 14)
    assert abs(b["ramped_sdrs_needed"] - 2 * a["ramped_sdrs_needed"]) < 0.2

"""🟩 GTM Strategy & Ops track."""
from gtm_strategy_ops.ai_deal_risk.deal_risk import score
from gtm_strategy_ops.forecasting.forecast_accuracy import accuracy, bias, checkpoint_table, region_summary
from gtm_strategy_ops.pipeline_analytics.pipeline_report import coverage, open_in_quarter
from gtm_strategy_ops.renewals.closed_lost_analysis import summarize
from gtm_strategy_ops.renewals.renewal_signals import health
from shared_core.config import load_config, read_csv
from shared_core.metrics.run_sql import run_file

CFG = load_config()


def opp(**kw):
    base = {"opportunity_id": "O-T", "account_name": "Test Bank", "region": "NA", "stage": "3 - Technical Validation",
            "amount": "200000", "forecast_category": "Best Case", "close_date": "2026-12-01",
            "stage_entered_date": "2026-09-25", "last_activity_date": "2026-09-30", "contacts_engaged": "4",
            "economic_buyer_engaged": "True", "poc_status": "In Progress", "security_review": "In Progress",
            "next_step": "POC readout", "is_closed": "False"}
    base.update(kw)
    return base


def test_healthy_deal_is_low_risk():
    assert score(opp(), CFG)["risk_level"] == "LOW"


def test_stalled_single_threaded_deal_is_high_risk():
    s = score(opp(stage_entered_date="2026-06-01", last_activity_date="2026-08-01", contacts_engaged="1",
                  economic_buyer_engaged="False"), CFG)
    assert s["risk_level"] == "HIGH" and "Single-threaded" in s["risk_reasons"]


def test_security_review_is_a_stage4_signal():
    s = score(opp(stage="4 - Business Case & Security Review", security_review="Not Started", poc_status="Passed"), CFG)
    assert "Security review not started" in s["risk_reasons"]


def test_forecast_accuracy_math():
    assert accuracy(90, 100) == 90.0 and accuracy(110, 100) == 90.0
    assert bias(110, 100) == 10.0 and accuracy(10, 0) is None


def test_forecast_bias_pattern_detected_by_region():
    summary = {r["region"]: r for r in region_summary(checkpoint_table(read_csv("forecast_snapshots.csv")))}
    assert summary["NA"]["avg_bias_wk8_%"] < summary["EMEA"]["avg_bias_wk8_%"]  # planted: NA sandbags vs EMEA


def test_coverage_python_matches_sql():
    py = {r["region"]: r["open_pipeline"] for r in coverage(read_csv("opportunities.csv"), CFG)}
    sql_rows = run_file("gtm_strategy_ops/pipeline_analytics/sql/pipeline_coverage.sql")[0]
    sql = {}
    for r in sql_rows:
        sql[r["region"]] = sql.get(r["region"], 0) + r["pipeline_usd"]
    for region, amount in sql.items():
        assert py[region] == amount, region
    assert py and sql  # both sides found pipeline in the current quarter


def test_open_in_quarter_excludes_omitted_and_closed():
    rows = open_in_quarter([opp(), opp(forecast_category="Omitted"), opp(is_closed="True")], CFG["current_fiscal_quarter"])
    assert len(rows) == 1


def test_renewal_health_bands_and_no_upsell_on_at_risk():
    good = health({"volume_trend_90d_pct": "10", "utilization_pct": "120", "sev1_tickets_90d": "0",
                   "exec_sponsor_active": "True", "competitor_signal": "False", "products_owned": "compliance",
                   "segment": "fintech_neobank", "arr": "100000", "renewal_date": "2026-12-01"}, CFG)
    bad = health({"volume_trend_90d_pct": "-25", "utilization_pct": "45", "sev1_tickets_90d": "2",
                  "exec_sponsor_active": "False", "competitor_signal": "True", "products_owned": "compliance",
                  "segment": "fintech_neobank", "arr": "100000", "renewal_date": "2026-12-01"}, CFG)
    assert good["band"] == "Healthy" and good["expansion_signal"].startswith("Overage")
    assert bad["band"] == "At Risk" and bad["expansion_signal"] == ""
    assert bad["expected_churn_$"] > good["expected_churn_$"]


def test_closed_lost_every_reason_has_an_owner_action():
    s = summarize(read_csv("opportunities.csv"))
    assert s["lost"] > 0 and all(r["owner_action"] for r in s["reasons"])

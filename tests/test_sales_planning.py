"""🟩 Sales planning: team/ramp, capacity, quota, territory, pipeline distribution, CRM request triage."""
from datetime import date

from gtm_strategy_ops.sales_planning import capacity_plan, quota_plan, request_triage, territory_plan
from gtm_strategy_ops.sales_planning.pipeline_distribution import distribution, gini
from gtm_strategy_ops.sales_planning.team import quarter_index, ramp_factor, rep_quotas, shift_quarter
from shared_core.config import load_config, read_csv

CFG = load_config()


def test_quarter_math_round_trips_across_years():
    assert shift_quarter("FY26-Q4", 1) == "FY27-Q1" and shift_quarter("FY27-Q1", -1) == "FY26-Q4"
    assert quarter_index("FY27-Q1") - quarter_index("FY26-Q1") == 4


def test_ramp_follows_the_vector_and_unhired_is_zero():
    vec = CFG["sales_team"]["ramp_vector"]
    start = date(2026, 7, 13)                      # FY26-Q3 start
    assert ramp_factor(start, "FY26-Q2", CFG) == 0.0
    assert ramp_factor(start, "FY26-Q3", CFG) == vec[0]
    assert ramp_factor(start, "FY26-Q4", CFG) == vec[1]
    assert ramp_factor(start, "FY28-Q1", CFG) == vec[-1]


def test_rep_quotas_are_whole_thousands():
    assert all(v % 1000 == 0 for v in rep_quotas(CFG, CFG["current_fiscal_quarter"]).values())


def test_capacity_plan_covers_every_plan_quarter_after_hiring():
    res = capacity_plan.plan(CFG)
    assert {r["quarter"] for r in res["capacity"]} == set(CFG["sales_planning"]["bookings_plan"])
    assert all(r["capacity_vs_plan_%"] >= 100 for r in res["capacity"])


def test_capacity_survival_shrinks_with_attrition():
    assert capacity_plan.survival(0, 15) == 1.0
    assert 0.95 < capacity_plan.survival(1, 15) < 1.0 and capacity_plan.survival(4, 15) < capacity_plan.survival(1, 15)


def test_quota_check_flags_a_region_with_no_ramped_rep():
    rows = {r["region"]: r for r in quota_plan.check_current(CFG)}
    assert "no fully ramped AE" in rows["MENA"]["flag"]


def test_territory_keeps_customers_with_their_owner_and_balances_within_tolerance():
    scored = territory_plan.score_accounts(read_csv("accounts.csv"), CFG)
    assigned, balance = territory_plan.assign(scored, CFG)
    owners = territory_plan.current_owners()
    customers = {a["account_id"] for a in scored if a["is_customer"] == "True"}
    region_aes = {}
    for ae, r in CFG["sales_team"]["ae_roster"].items():
        region_aes.setdefault(r["region"], set()).add(ae)
    for a in assigned:
        if a["account_id"] in customers and owners.get(a["account_id"]) in region_aes.get(a["region"], set()):
            assert a["owner"] == owners[a["account_id"]]
    tol = CFG["sales_planning"]["territory"]["balance_tolerance_pct"]
    assert all(abs(b["vs_region_mean_%"]) <= tol for b in balance)


def test_gini_bounds():
    assert gini([1, 1, 1, 1]) == 0.0
    assert gini([0, 0, 0, 10]) > 0.7


def test_distribution_routes_at_most_one_rep_per_region():
    res = distribution(CFG)
    regions = [r["region"] for r in res["routing"]]
    assert len(regions) == len(set(regions))


def test_request_priority_rules():
    base = {"revenue_impact": "Nice to have", "due_date": "", "submitted_date": "2026-09-01", "users_affected": "1",
            "category": "Report / Dashboard", "summary": "Pipeline report"}
    assert request_triage.priority({**base, "revenue_impact": "Blocks deal"}) == "P0"
    assert request_triage.priority({**base, "category": "Access / Permissions", "summary": "New AE needs access"}) == "P1"
    assert request_triage.priority({**base, "due_date": "2026-09-02"}) == "P1"
    assert request_triage.priority({**base, "revenue_impact": "Improves efficiency", "users_affected": "25"}) == "P2"
    assert request_triage.priority(base) == "P3"


def test_business_days_skip_weekends():
    assert request_triage.business_days(date(2026, 10, 2), date(2026, 10, 5)) == 1   # Fri -> Mon


def test_triage_finds_duplicates_and_classes_every_request():
    res = request_triage.triage(CFG)
    assert all(r["change_class"] in ("standard", "normal", "major") for r in res["rows"])
    assert res["insights"]["duplicates"]

"""🟦 Marketing ops: attribution, campaign and consent hygiene, demand plan."""
import re

from gtm_engineer.marketing_ops import campaign_report, demand_plan
from shared_core.config import load_config

CFG = load_config()
DATA = campaign_report.load()


def _t(mid, day):
    return {"member_id": mid, "touch_date": f"2026-05-{day:02d}"}


def test_w_shaped_credit_sums_to_one_and_weights_key_touches():
    from datetime import date
    touches = [_t("a", 1), _t("b", 5), _t("c", 10), _t("d", 15), _t("e", 20)]
    credit = campaign_report.w_shaped(touches, date(2026, 5, 10), date(2026, 5, 20))
    assert abs(sum(credit.values()) - 1) < 1e-9
    assert credit["a"] == credit["c"] == credit["e"] == 0.30
    assert abs(credit["b"] - 0.05) < 1e-9


def test_w_shaped_single_touch_gets_everything():
    from datetime import date
    credit = campaign_report.w_shaped([_t("a", 1)], date(2026, 5, 2), date(2026, 5, 3))
    assert list(credit) == ["a"] and abs(credit["a"] - 1) < 1e-9


def test_member_response_flag_matches_the_campaign_type():
    types = {c["campaign_id"]: c["type"] for c in DATA["campaigns"]}
    resp = {k: set(v["responded"]) for k, v in CFG["marketing_ops"]["campaign_types"].items()}
    for m in DATA["members"]:
        assert (m["status"] in resp[types[m["campaign_id"]]]) == (m["responded"] == "True")


def test_hygiene_catches_planted_naming_and_consent_issues():
    rules = {i["rule"][:3] for i in campaign_report.hygiene(DATA, CFG)}
    assert {"M01", "M02", "M05", "M06"} <= rules


def test_naming_pattern_accepts_the_convention():
    assert re.match(CFG["marketing_ops"]["campaign_name_pattern"], "FY26-Q3_WBN_NA_AML-Agents-Live")
    assert not re.match(CFG["marketing_ops"]["campaign_name_pattern"], "Q3 webinar AML")


def test_demand_plan_reconciles_to_the_bookings_plan():
    res = demand_plan.plan(CFG, DATA)
    r = res["rates"]
    for row in res["summary"]:
        assert abs(row["pipeline_needed_$"] * r["win_rate_$"] - row["bookings_plan_$"]) < 1
        assert row["create_in"] < row["close_quarter"] or row["create_in"][:4] < row["close_quarter"][:4]
    assert abs(sum(res["mix"].values()) - 1) < 1e-9


def test_demand_plan_gap_math():
    assert demand_plan.pct_gap(100, 60) == -40.0 and demand_plan.pct_gap(0, 5) == 0.0

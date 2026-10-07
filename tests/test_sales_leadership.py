"""🟩 Sales leadership reporting: VP brief, rep scorecard, industries, stage velocity, deal board, all-hands."""
from datetime import date, timedelta
from statistics import mean

from gtm_strategy_ops.sales_leadership import all_hands, vp_brief
from gtm_strategy_ops.sales_leadership.deal_board import build as build_board
from gtm_strategy_ops.sales_leadership.deal_board import classify
from gtm_strategy_ops.sales_leadership.history import close_pushes, load_history, stage_timelines
from gtm_strategy_ops.sales_leadership.rep_scorecard import scorecard
from gtm_strategy_ops.sales_leadership.segment_performance import verdict_for, wilson
from gtm_strategy_ops.sales_leadership.stage_velocity import analyze
from shared_core.config import AS_OF, load_config, read_csv
from shared_core.metrics.run_sql import run_file

CFG = load_config()
OPPS = read_csv("opportunities.csv")
HISTORY = load_history()


def test_every_opp_starts_in_first_stage_and_stages_never_go_backwards():
    order = [s["name"] for s in CFG["opportunity"]["stages"]]
    tl = stage_timelines(OPPS, HISTORY, CFG)
    by_opp = {}
    for t in tl:
        by_opp.setdefault(t["opportunity_id"], []).append(order.index(t["stage"]))
    assert set(by_opp) == {o["opportunity_id"] for o in OPPS}
    assert all(seq[0] == 0 and seq == sorted(seq) for seq in by_opp.values())


def test_open_deal_current_stage_matches_the_opportunity_record():
    tl = {t["opportunity_id"]: t for t in stage_timelines(OPPS, HISTORY, CFG) if t["outcome"] == "open"}
    for o in OPPS:
        if o["is_closed"] != "True":
            assert tl[o["opportunity_id"]]["stage"] == o["stage"]


def test_pushes_only_move_dates_later():
    for pushes in close_pushes(HISTORY).values():
        assert all(p["days_pushed"] > 0 for p in pushes)


def test_stage_velocity_python_matches_sql():
    py = {s["stage"]: s for s in analyze(CFG, OPPS, HISTORY)["stages"]}
    sql = {r["stage"]: r for r in run_file("gtm_strategy_ops/sales_leadership/sql/stage_velocity.sql")[0]}
    for stage, s in py.items():
        assert (s["entered"], s["advanced"], s["lost_here"], s["open_now"]) == \
               (sql[stage]["entered"], sql[stage]["advanced"], sql[stage]["lost_here"], sql[stage]["open_now"])


def test_planted_inbound_handoff_delay_is_found():
    res = analyze(CFG, OPPS, HISTORY)
    qualify = [d for d in res["drivers"] if d["dimension"] == "source" and d["value"] == "Marketing"]
    assert res["bottleneck"]["stage"].startswith("1 -") and qualify and qualify[0]["excess_days"] > 0


def test_wilson_interval_is_wide_on_small_samples():
    lo_small, hi_small = wilson(3, 7)
    lo_big, hi_big = wilson(300, 700)
    assert (hi_small - lo_small) > 3 * (hi_big - lo_big)


def test_segment_verdict_needs_sample_and_a_real_gap():
    sl = CFG["sales_leadership"]
    assert verdict_for(sl["min_sample"] - 1, 80.0, 50.0, 95.0, 27.0, sl) == "Too early"
    assert verdict_for(40, 45.0, 35.0, 55.0, 27.0, sl) == "Double down"
    assert verdict_for(40, 45.0, 20.0, 60.0, 27.0, sl) == "Watch"      # interval overlaps the company rate
    assert verdict_for(40, 10.0, 4.0, 18.0, 27.0, sl) == "Fix"


def _deal(**kw):
    base = {"close_date": (AS_OF + timedelta(days=40)).isoformat(), "last_activity_date": (AS_OF - timedelta(days=2)).isoformat(),
            "stage": "3 - Technical Validation", "stage_entered_date": (AS_OF - timedelta(days=5)).isoformat(),
            "risk_level": "LOW", "risk_reasons": "", "economic_buyer_engaged": "True", "contacts_engaged": "4"}
    base.update(kw)
    return base


def test_deal_board_rules_in_order():
    adv = AS_OF - timedelta(days=5)
    push = [{"changed_date": AS_OF - timedelta(days=3), "days_pushed": 30}]
    assert classify(_deal(close_date="2026-09-01"), CFG, [], adv)[0] == "Past due"
    assert classify(_deal(), CFG, push, adv)[0] == "Slipping"
    assert classify(_deal(risk_level="HIGH", risk_reasons="No activity in 40d"), CFG, [], adv)[0] == "At risk"
    assert classify(_deal(stage_entered_date="2026-06-01"), CFG, [], adv)[0] == "Stalled"
    assert classify(_deal(), CFG, [], adv)[0] == "Hot"
    assert classify(_deal(economic_buyer_engaged="False"), CFG, [], adv)[0] == "On track"


def test_rep_quotas_sum_to_region_quota_and_ramping_reps_carry_less():
    rows = scorecard(CFG, OPPS, build_board(CFG, OPPS, HISTORY))
    q = CFG["current_fiscal_quarter"]
    for region, quota in CFG["quota"][q].items():
        assert abs(sum(r["quota_$"] for r in rows if r["region"] == region) - quota) <= 1000 * len(rows)
    emea = {r["owner"]: r for r in rows if r["region"] == "EMEA"}
    assert emea["AE - Liam Byrne"]["quota_$"] < emea["AE - Klara Weiss"]["quota_$"]


def test_snapshot_fits_a_phone_screen_and_full_has_definitions():
    d = vp_brief.gather(CFG)
    snap, full = vp_brief.snapshot(d), vp_brief.full(d)
    assert len(snap.splitlines()) <= 25 and "Asks for you" in snap
    assert len(full) > 2 * len(snap) and "Definitions" in full


def test_all_hands_recognizes_top_and_never_ranks_the_bottom():
    d = all_hands.build("quarter", cfg=CFG)
    text = all_hands.render(d)
    coach = [r["owner"].replace("AE - ", "") for r in scorecard(CFG, OPPS) if r["status"] == "Coach"]
    recognition = text.split("## Slide 3")[1].split("## Slide 4")[0]
    top_att = recognition.split("**Quota attainment:**")[1].split("\n")[0]
    assert all(name not in top_att for name in coach)
    assert "Slide 2 · Wins" in text and "Speaker prompts" in text


def test_won_deals_spend_less_time_in_stage_than_lost_on_average():
    tl = stage_timelines(OPPS, HISTORY, CFG)
    won_ids = {o["opportunity_id"] for o in OPPS if o["is_won"] == "True"}
    lost_ids = {o["opportunity_id"] for o in OPPS if o["is_closed"] == "True" and o["is_won"] != "True"}
    first = [t for t in tl if t["stage"].startswith("1 -") and t["outcome"] != "open"]
    assert mean(t["days"] for t in first if t["opportunity_id"] in won_ids) < \
           mean(t["days"] for t in first if t["opportunity_id"] in lost_ids)


def test_as_of_is_fixed_for_reproducibility():
    assert AS_OF == date(2026, 10, 1)

"""Rep scorecard: how each AE is doing, why, and what to coach.

The VP question: "How is each rep doing?" The follow-up is always "why?", so every rep gets the
result, the drivers behind it and the one lever to work on.

Per AE:
  Result (lagging)    last quarter's bookings vs ramp-adjusted quota
  Setup (leading)     this quarter's pipeline vs quota (coverage), commit, deals needing attention
  Levers              the four sales-velocity inputs over the trailing year: pipeline created, win
                      rate, average won deal, cycle length. Each is compared with the team median of
                      ramped reps. The weakest lever is the coaching focus.
  Hygiene             share of open deals with no next step, days since last activity

Status rules (ramping reps are judged on pipeline only, not bookings):
  Ahead     coverage >= 1.25 x target and last quarter >= 100%
  On track  coverage >= target
  Watch     coverage >= 2x, or last quarter >= 70%
  Coach     everything else

This is for the VP and the rep's manager. The all-hands uses only the positive slices of it.

    python -m gtm_strategy_ops.sales_leadership.rep_scorecard
"""
from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from statistics import median

from gtm_strategy_ops.sales_leadership.deal_board import build as build_board
from gtm_strategy_ops.sales_leadership.segment_performance import closed_in_window, velocity
from gtm_strategy_ops.sales_planning.team import ramp_factor, ramp_status, rep_quotas, roster, shift_quarter
from shared_core.config import AS_OF, fiscal_quarter, load_config, parse_date, pct, read_csv, table, to_float, write_csv

LEVER_COACHING = {
    "pipeline_created": "Pipeline generation: block prospecting time, work the territory's top accounts and signal alerts.",
    "win_rate": "Win rate: deal inspection on qualification and access to power; review the last three losses together.",
    "avg_won_$": "Deal size: lead with the multi-product (fraud + compliance) case; stop discounting before value is agreed.",
    "cycle_days": "Cycle length: mutual action plans with dated steps; start security review in parallel, not after.",
}


def scorecard(cfg: dict | None = None, opps: list[dict] | None = None, board: list[dict] | None = None) -> list[dict]:
    cfg = cfg or load_config()
    opps = opps if opps is not None else read_csv("opportunities.csv")
    board = board if board is not None else build_board(cfg, opps)
    sl = cfg["sales_leadership"]
    q = cfg["current_fiscal_quarter"]
    prev_q = shift_quarter(q, -1)
    quota_now, quota_prev = rep_quotas(cfg, q), rep_quotas(cfg, prev_q)
    closed = closed_in_window(opps, sl["trailing_days"])
    created_since = AS_OF - timedelta(days=180)
    flagged = defaultdict(lambda: [0, 0])
    for r in board:
        if r["in_quarter"] and r["bucket"] in ("At risk", "Slipping", "Past due", "Stalled"):
            flagged[r["owner"]][0] += 1
            flagged[r["owner"]][1] += r["amount"]
    rows = []
    for ae, info in roster(cfg).items():
        mine = [o for o in opps if o["owner"] == ae]
        won_prev = sum(to_float(o["amount"]) for o in mine
                       if o["is_won"] == "True" and fiscal_quarter(parse_date(o["close_date"])) == prev_q)
        c = [o for o in closed if o["owner"] == ae]
        won = [o for o in c if o["is_won"] == "True"]
        rate = pct(len(won), len(c))
        avg = sum(to_float(o["amount"]) for o in won) / len(won) if won else 0.0
        cyc = median([(parse_date(o["close_date"]) - parse_date(o["created_date"])).days for o in won]) if won else 0
        created = [o for o in mine if parse_date(o["created_date"]) >= created_since]
        open_mine = [o for o in mine if o["is_closed"] != "True"]
        in_q = [o for o in open_mine if fiscal_quarter(parse_date(o["close_date"])) == q and o["forecast_category"] != "Omitted"]
        pipe_q = sum(to_float(o["amount"]) for o in in_q)
        cov = round(pipe_q / quota_now[ae], 2) if quota_now[ae] else None
        att_prev = pct(won_prev, quota_prev[ae]) if quota_prev[ae] else None
        rows.append({
            "owner": ae, "region": info["region"], "ramp": ramp_status(info["start_date"], q, cfg),
            "ramped": ramp_factor(info["start_date"], q, cfg) >= 1,
            "last_q_won_$": int(won_prev), "last_q_quota_$": quota_prev[ae],
            "last_q_attainment_%": att_prev if att_prev is not None else "n/a (ramp)",
            "quota_$": quota_now[ae], "pipeline_in_q_$": int(pipe_q), "coverage_x": cov if cov is not None else "n/a",
            "commit_$": int(sum(to_float(o["amount"]) for o in in_q if o["forecast_category"] == "Commit")),
            "needs_attention": flagged[ae][0], "needs_attention_$": flagged[ae][1],
            "closed_trailing": len(c), "win_rate_%": rate if len(c) >= sl["min_sample"] else f"{rate} (n={len(c)})",
            "win_rate_raw": rate, "avg_won_$": int(avg), "cycle_days": int(cyc) if won else "",
            "pipeline_created": len(created), "pipeline_created_$": int(sum(to_float(o["amount"]) for o in created)),
            "velocity_$_per_day": velocity(len(c), rate, avg, cyc),
            "no_next_step_%": pct(sum(1 for o in open_mine if not o["next_step"]), len(open_mine)),
            "median_days_since_activity": int(median([(AS_OF - parse_date(o["last_activity_date"])).days for o in open_mine])) if open_mine else "",
            "_n_closed": len(c),
        })
    _add_levers(rows, cfg)
    _add_status(rows, cfg)
    return sorted(rows, key=lambda r: ["Ahead", "On track", "Watch", "Coach"].index(r["status"]))


def _add_levers(rows: list[dict], cfg: dict) -> None:
    """Weakest of the four velocity levers vs the median of ramped reps with enough closed deals."""
    peers = [r for r in rows if r["ramped"] and r["_n_closed"] >= cfg["sales_leadership"]["min_sample"]] or rows
    med = {k: median([r[k] if k != "win_rate" else r["win_rate_raw"] for r in peers if r[k if k != "win_rate" else "win_rate_raw"] != ""] or [0])
           for k in ("pipeline_created", "win_rate", "avg_won_$", "cycle_days")}
    for r in rows:
        gaps = {}
        for k in ("pipeline_created", "win_rate", "avg_won_$"):
            v = r["win_rate_raw"] if k == "win_rate" else r[k]
            if med[k]:
                gaps[k] = (v - med[k]) / med[k]
        if r["cycle_days"] != "" and med["cycle_days"]:
            gaps["cycle_days"] = (med["cycle_days"] - r["cycle_days"]) / med["cycle_days"]   # longer cycle = worse
        if r["_n_closed"] < cfg["sales_leadership"]["min_sample"]:
            gaps = {k: v for k, v in gaps.items() if k == "pipeline_created"}   # too few deals to judge the rest
        weakest = min(gaps, key=gaps.get) if gaps else ""
        r["weakest_lever"] = f"{weakest} ({gaps[weakest]:+.0%} vs team)" if weakest and gaps[weakest] < -0.1 else "none below team by >10%"
        r["coaching_focus"] = LEVER_COACHING.get(weakest, "") if weakest and gaps[weakest] < -0.1 else "Keep doing what works; share it."


def _add_status(rows: list[dict], cfg: dict) -> None:
    target = cfg["opportunity"]["coverage_target"]
    for r in rows:
        _status(r, target)
        # When no trailing-year lever is weak, the problem is this quarter's setup: say so.
        if r["status"] in ("Watch", "Coach") and r["weakest_lever"].startswith("none"):
            cov = r["coverage_x"] if isinstance(r["coverage_x"], float) else 0.0
            if cov < target:
                gap = int(target * r["quota_$"] - r["pipeline_in_q_$"])
                r["coaching_focus"] = (f"Coverage, not skill: ${gap:,} short of {target}x this quarter. Build pipeline now "
                                       "and check whether real next-quarter deals can be pulled in.")
            else:
                r["coaching_focus"] = "Last quarter's miss looks like timing, not a pattern: review the deals that slipped out of it."


def _status(r: dict, target: float) -> None:
    cov = r["coverage_x"] if isinstance(r["coverage_x"], float) else 0.0
    att = r["last_q_attainment_%"] if isinstance(r["last_q_attainment_%"], float) else 0.0
    if not r["ramped"]:
        r["status"] = "On track" if cov >= target else ("Watch" if cov >= 2 else "Coach")
    elif cov >= 1.25 * target and att >= 100:
        r["status"] = "Ahead"
    elif cov >= target:
        r["status"] = "On track"
    elif cov >= 2 or att >= 70:
        r["status"] = "Watch"
    else:
        r["status"] = "Coach"


COLS = ["owner", "region", "ramp", "status", "last_q_attainment_%", "quota_$", "pipeline_in_q_$", "coverage_x", "commit_$",
        "needs_attention", "win_rate_%", "avg_won_$", "cycle_days", "pipeline_created", "weakest_lever"]


def main() -> None:
    rows = scorecard()
    cfg = load_config()
    print(f"=== Rep scorecard: {shift_quarter(cfg['current_fiscal_quarter'], -1)} result, {cfg['current_fiscal_quarter']} setup ===")
    print(table(rows, COLS))
    print("\n=== Coaching focus (for the manager's 1:1s, not for the all-hands) ===")
    for r in rows:
        if r["status"] in ("Watch", "Coach"):
            print(f"- {r['owner']} [{r['status']}]: {r['coaching_focus']}")
    write_csv("rep_scorecard.csv", rows, [c for c in rows[0] if not c.startswith("_")])


if __name__ == "__main__":
    main()

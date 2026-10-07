"""Deal board: every open deal in one of five buckets, with the reason and the next action.

The VP question: "Which deals are hot, which are at risk, and what do we do about them?"

Buckets, checked in this order (first match wins):
  Past due  close date already passed and the deal is still open. A data problem before it is a
            sales problem: fix the date or close it out before the forecast call.
  Slipping  close date pushed `slipping_deal.pushes`+ times, or pushed by
            `slipping_deal.big_push_days`+ days within the last `recent_push_days`. Research on large deal sets finds win
            rates fall as close dates are pushed further (Gong, Aviso; see the spec), so a push is a
            leading signal, not admin noise.
  At risk   HIGH on the deal-risk model (ai_deal_risk/deal_risk.py: stage age, inactivity,
            single-threading, no economic buyer, missing next step, validation/security gaps).
  Stalled   past its stage time limit, or no activity in `stalled_activity_days`.
  Hot       moved forward a stage recently, active this week, economic buyer engaged, multi-threaded,
            LOW risk and not pushed recently. These are the deals to pull resources toward.
  On track  everything else.

The risk score itself is not recomputed here: this module reuses deal_risk.score() so the forecast
call and the VP brief never disagree about a deal.

    python -m gtm_strategy_ops.sales_leadership.deal_board
"""
from __future__ import annotations

from collections import defaultdict

from gtm_strategy_ops.ai_deal_risk.deal_risk import score
from gtm_strategy_ops.sales_leadership.history import close_pushes, last_advance, load_history, stage_timelines
from shared_core.config import AS_OF, fiscal_quarter, load_config, parse_date, read_csv, table, to_float, write_csv

ORDER = ["Hot", "On track", "Stalled", "At risk", "Slipping", "Past due"]
ACTIONS = {
    "Past due": "Owner updates the close date to a buyer-confirmed one, or closes it lost, before the next forecast call.",
    "Slipping": "Re-confirm the close plan with the buyer this week; reset the date to one the buyer has agreed in writing.",
    "At risk": "Manager deal review: fix the top risk reason (exec access, second contact, dated next step) or move it out of Commit.",
    "Stalled": "Book a dated next step or close it out; a deal with no next meeting is not pipeline.",
    "Hot": "Pull in exec sponsor and SE time now; confirm paper process so nothing slows the close.",
    "On track": "Keep the plan; inspect at the normal cadence.",
}


def classify(o: dict, cfg: dict, pushes: list[dict], advanced_on, as_of=AS_OF) -> tuple[str, str]:
    sl = cfg["sales_leadership"]
    limits = {s["name"]: s["max_days"] for s in cfg["opportunity"]["stages"]}
    close = parse_date(o["close_date"])
    recent = [p for p in pushes if (as_of - p["changed_date"]).days <= sl["slipping_deal"]["recent_push_days"]]
    idle = (as_of - parse_date(o["last_activity_date"])).days
    days_in_stage = (as_of - parse_date(o["stage_entered_date"])).days
    if close < as_of:
        return "Past due", f"close date {o['close_date']} passed {(as_of - close).days}d ago"
    if len(pushes) >= sl["slipping_deal"]["pushes"]:
        return "Slipping", f"close date pushed {len(pushes)}x ({sum(p['days_pushed'] for p in pushes)}d total)"
    big = [p for p in recent if p["days_pushed"] >= sl["slipping_deal"]["big_push_days"]]
    if big:
        return "Slipping", f"close date pushed {big[-1]['days_pushed']}d in the last {sl['slipping_deal']['recent_push_days']}d"
    if o["risk_level"] == "HIGH":
        return "At risk", o["risk_reasons"].split("; ")[0]
    if (limits.get(o["stage"]) and days_in_stage > limits[o["stage"]]) or idle > sl["stalled_activity_days"]:
        why = f"{days_in_stage}d in stage (limit {limits.get(o['stage'])})" if days_in_stage > (limits.get(o["stage"]) or 10**6) \
            else f"no activity in {idle}d"
        return "Stalled", why
    hd = sl["hot_deal"]
    if (advanced_on and (as_of - advanced_on).days <= hd["advanced_within_days"] and idle <= hd["active_within_days"]
            and o.get("economic_buyer_engaged") == "True" and int(o.get("contacts_engaged") or 0) >= hd["min_contacts"]
            and o["risk_level"] == "LOW" and not recent):
        return "Hot", f"advanced {(as_of - advanced_on).days}d ago; EB engaged; {o['contacts_engaged']} contacts"
    return "On track", ""


def build(cfg: dict | None = None, opps: list[dict] | None = None, history: list[dict] | None = None) -> list[dict]:
    cfg = cfg or load_config()
    opps = opps if opps is not None else read_csv("opportunities.csv")
    history = history if history is not None else load_history()
    open_opps = [score(o, cfg) for o in opps if o["is_closed"] != "True"]
    pushes = close_pushes(history)
    advanced = last_advance(stage_timelines(opps, history, cfg))
    q = cfg["current_fiscal_quarter"]
    board = []
    for o in open_opps:
        bucket, why = classify(o, cfg, pushes.get(o["opportunity_id"], []), advanced.get(o["opportunity_id"]))
        board.append({"bucket": bucket, "opportunity_id": o["opportunity_id"], "account_name": o["account_name"],
                      "owner": o["owner"], "segment": o["segment"], "region": o["region"], "stage": o["stage"],
                      "amount": int(to_float(o["amount"])), "forecast_category": o["forecast_category"],
                      "close_date": o["close_date"], "in_quarter": fiscal_quarter(parse_date(o["close_date"])) == q,
                      "pushes": len(pushes.get(o["opportunity_id"], [])), "risk_level": o["risk_level"],
                      "why": why, "action": ACTIONS[bucket]})
    return sorted(board, key=lambda r: (-ORDER.index(r["bucket"]), -r["amount"]))


def summary(board: list[dict], in_quarter_only: bool = False) -> list[dict]:
    agg = defaultdict(lambda: [0, 0, 0])
    for r in board:
        if in_quarter_only and not r["in_quarter"]:
            continue
        a = agg[r["bucket"]]
        a[0] += 1
        a[1] += r["amount"]
        a[2] += r["amount"] if r["forecast_category"] == "Commit" else 0
    return [{"bucket": b, "deals": agg[b][0], "amount_$": agg[b][1], "of_which_commit_$": agg[b][2]} for b in ORDER[::-1] if b in agg]


def main() -> None:
    board = build()
    q = load_config()["current_fiscal_quarter"]
    print("=== Deal board: all open pipeline ===")
    print(table(summary(board)))
    print(f"\n=== Closing in {q} ===")
    print(table(summary(board, in_quarter_only=True)))
    for b in ("Past due", "Slipping", "At risk", "Hot"):
        rows = [r for r in board if r["bucket"] == b][:5]
        print(f"\n=== {b}: top {len(rows)} by amount ===")
        print(table(rows, ["opportunity_id", "account_name", "owner", "stage", "amount", "forecast_category", "close_date", "why"]))
    write_csv("deal_board.csv", board)


if __name__ == "__main__":
    main()

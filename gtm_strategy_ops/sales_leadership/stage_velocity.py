"""Stage velocity and bottlenecks: where deals slow down, and what the slow ones have in common.

The VP question: "Moving a deal from the intro call to discovery is taking forever. Why?"

Three steps, each answering a follow-up a sales leader will ask:
  1. Stage table: for every stage, how many deals entered, how many moved forward vs died there,
     median and 75th-percentile days in stage, and the gap to the stage's time limit (config).
  2. Bottleneck, two ways: where deals SLOW (the stage whose median uses the largest share of its
     time limit) and where deals DIE (the stage with the lowest forward conversion). Leaders mix
     these up; they need different fixes.
  3. Drivers: inside that stage, slice the deals by owner, source, segment, product line, deal type,
     economic-buyer access and contact count. A slice "drives" the delay when its median runs well
     over the stage median on enough deals. Each driver comes with the likely cause and the fix to
     test, so the answer to "why?" is a short list of checkable hypotheses, not a guess.

Medians, not means: one deal stuck for 200 days should not set the number for the whole team.

    python -m gtm_strategy_ops.sales_leadership.stage_velocity
"""
from __future__ import annotations

from collections import defaultdict
from statistics import median

from gtm_strategy_ops.sales_leadership.history import load_history, stage_order, stage_timelines
from shared_core.config import load_config, pct, read_csv, table, write_csv

DIMENSIONS = ["source", "owner", "segment", "product_line", "type", "eb_engaged", "contacts_band"]
# For these two, only the weak value is a cause to fix. Big buying committees (5+ contacts) being
# slower is expected, not a problem, so those slices are not reported as drivers.
ONLY_VALUES = {"eb_engaged": {"No EB"}, "contacts_band": {"1-2 contacts"}}

# What a slow slice usually means, and the first fix to test. Generic on purpose; confirm with call
# recordings and two or three rep conversations before changing process.
CAUSES = {
    "source": ("Source-specific motion: deals from this source arrive less ready, or wait on a third party (e.g. a partner's own process).",
               "Agree a joint plan with the source owner (partner manager, marketing) and track the waiting step as its own date field."),
    "owner": ("Rep execution or capacity: this AE's deals wait longer than peers' in this stage.",
              "Review three of the rep's stalled deals in 1:1; check open-opp load vs the team before assuming a skill gap."),
    "segment": ("Buyer-side process for this segment (approvals, data access, committee size).",
                "Build the segment's steps into the mutual action plan up front; start the slow step earlier in parallel."),
    "product_line": ("Product-line motion: evaluation steps differ for this line.",
                     "Give this line its own exit criteria and SE checklist for the stage."),
    "type": ("Deal-type motion: expansions and new logos move differently.",
             "Report the two types separately and set separate stage limits."),
    "eb_engaged": ("No access to power: deals without the economic buyer wait for someone who can say yes.",
                   "Make an economic-buyer meeting an exit criterion for this stage."),
    "contacts_band": ("Single-threaded: one contact means one point of delay.",
                      "Require a second persona engaged before the stage can close."),
}


# In the first stage, a slow source is almost always the hand-off itself.
FIRST_STAGE_CAUSES = {
    "source": ("Hand-off: the deal is created before a discovery meeting is held or booked.",
               "Require a booked discovery meeting (date on the opp) at conversion; SDR books onto the AE calendar during the qualifying call."),
}


def contacts_band(v) -> str:
    n = int(v or 0)
    return "1-2 contacts" if n <= 2 else "3-4 contacts" if n <= 4 else "5+ contacts"


def _p75(xs: list[int]) -> int:
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(0.75 * (len(xs) - 1))))] if xs else 0


def stage_table(timelines: list[dict], cfg: dict) -> list[dict]:
    limits = {s["name"]: s["max_days"] for s in cfg["opportunity"]["stages"]}
    rows = []
    for stage in stage_order(cfg):
        t = [r for r in timelines if r["stage"] == stage]
        adv = [r for r in t if r["outcome"] == "advanced"]
        lost = [r for r in t if r["outcome"] == "lost"]
        still = [r for r in t if r["outcome"] == "open"]
        days = [r["days"] for r in adv]
        med = int(median(days)) if days else 0
        limit = limits.get(stage) or 0
        rows.append({
            "stage": stage, "entered": len(t), "advanced": len(adv), "lost_here": len(lost), "open_now": len(still),
            "conversion_%": pct(len(adv), len(adv) + len(lost)),
            "median_days": med, "p75_days": _p75(days), "limit_days": limit,
            "over_limit_%": pct(med - limit, limit) if limit and med > limit else 0.0,
            "pressure": round(med / limit, 2) if limit else 0.0,
            "open_past_limit": sum(1 for r in still if limit and r["days"] > limit),
            "won_median_days": int(median([r["days"] for r in adv if r["is_won"] == "True"])) if any(r["is_won"] == "True" for r in adv) else "",
            "lost_deal_median_days": int(median([r["days"] for r in lost])) if lost else "",
        })
    return rows


def bottleneck(stages: list[dict], min_n: int = 8) -> dict:
    """Where deals slow: highest median/limit ratio among stages with enough deals through them."""
    eligible = [s for s in stages if s["advanced"] >= min_n and s["limit_days"]] or stages
    return max(eligible, key=lambda s: (s["pressure"], s["advanced"]))


def leak(stages: list[dict], min_n: int = 8) -> dict:
    """Where deals die: lowest forward conversion among stages with enough resolved deals."""
    eligible = [s for s in stages if s["advanced"] + s["lost_here"] >= min_n] or stages
    return min(eligible, key=lambda s: s["conversion_%"])


def drivers(timelines: list[dict], stage: str, min_n: int = 5, min_excess_days: int = 3, first_stage: bool = False) -> list[dict]:
    """Slices of deals that took materially longer than the stage median, ranked by excess deal-days."""
    done = [dict(r, eb_engaged="EB engaged" if r["economic_buyer_engaged"] == "True" else "No EB",
                 contacts_band=contacts_band(r["contacts_engaged"]))
            for r in timelines if r["stage"] == stage and r["outcome"] == "advanced"]
    if not done:
        return []
    overall = median(r["days"] for r in done)
    out = []
    for dim in DIMENSIONS:
        groups = defaultdict(list)
        for r in done:
            groups[r[dim] or "(blank)"].append(r["days"])
        for val, ds in groups.items():
            if len(ds) < min_n or (dim in ONLY_VALUES and val not in ONLY_VALUES[dim]):
                continue
            med = median(ds)
            excess = med - overall
            if excess >= min_excess_days:
                cause, fix = (FIRST_STAGE_CAUSES.get(dim) if first_stage else None) or CAUSES[dim]
                out.append({"dimension": dim, "value": val, "deals": len(ds), "median_days": int(med),
                            "stage_median": int(overall), "excess_days": int(excess),
                            "excess_deal_days": int(excess * len(ds)), "likely_cause": cause, "fix_to_test": fix})
    return sorted(out, key=lambda r: -r["excess_deal_days"])


def stuck_now(timelines: list[dict], stage: str, cfg: dict) -> list[dict]:
    limit = {s["name"]: s["max_days"] for s in cfg["opportunity"]["stages"]}.get(stage) or 0
    rows = [r for r in timelines if r["stage"] == stage and r["outcome"] == "open" and r["days"] > limit]
    return sorted(({"opportunity_id": r["opportunity_id"], "owner": r["owner"], "segment": r["segment"],
                    "source": r["source"], "amount": r["amount"], "days_in_stage": r["days"], "limit": limit} for r in rows),
                  key=lambda r: -r["days_in_stage"])


def analyze(cfg: dict | None = None, opps: list[dict] | None = None, history: list[dict] | None = None) -> dict:
    cfg = cfg or load_config()
    opps = opps if opps is not None else read_csv("opportunities.csv")
    history = history if history is not None else load_history()
    min_n = cfg.get("sales_leadership", {}).get("min_sample", 8)
    tl = stage_timelines(opps, history, cfg)
    stages = stage_table(tl, cfg)
    neck, dies = bottleneck(stages, min_n), leak(stages, min_n)
    order = stage_order(cfg)
    by_stage = {s: drivers(tl, s, first_stage=(s == order[0])) for s in order}
    zombies = [s for s in stages if s["lost_deal_median_days"] != "" and s["won_median_days"] != ""
               and s["lost_deal_median_days"] > 2 * max(1, s["won_median_days"])]
    return {"timelines": tl, "stages": stages, "bottleneck": neck, "leak": dies, "drivers": by_stage[neck["stage"]],
            "drivers_by_stage": by_stage, "first_stage": order[0], "first_hop_drivers": by_stage[order[0]],
            "stuck": stuck_now(tl, neck["stage"], cfg), "zombie_stages": zombies}


def headline(res: dict) -> str:
    b, lk = res["bottleneck"], res["leak"]
    top = res["drivers"][0] if res["drivers"] else None
    msg = (f"Deals slow most in {b['stage']}: median {b['median_days']}d against a {b['limit_days']}d limit "
           f"({int(b['pressure'] * 100)}% of the time budget), {b['open_past_limit']} open deals past the limit now.")
    if top:
        msg += (f" Main driver: {top['dimension']} = {top['value']} ({top['deals']} deals, median {top['median_days']}d, "
                f"+{top['excess_days']}d). Likely cause: {top['likely_cause']}")
    msg += f" Deals die most in {lk['stage']}: {lk['conversion_%']}% move forward."
    for z in res["zombie_stages"][:1]:
        msg += (f" Lost deals sit in {z['stage']} {z['lost_deal_median_days']}d before being closed out vs "
                f"{z['won_median_days']}d for winners: that is inflated pipeline, not slow selling.")
    return msg


def main() -> None:
    res = analyze()
    print("=== 1. Stage velocity (closed and open deals, from field history) ===")
    print(table(res["stages"], ["stage", "entered", "advanced", "lost_here", "open_now", "conversion_%", "median_days",
                                "p75_days", "limit_days", "pressure", "open_past_limit", "won_median_days", "lost_deal_median_days"]))
    print("\n=== 2. Bottleneck ===\n" + headline(res))
    hot = [st for st in res["stages"] if st["pressure"] >= 0.85 or st["stage"] in (res["bottleneck"]["stage"], res["first_stage"])]
    for st in hot:
        print(f"\n=== 3. Drivers inside {st['stage']} (pressure {st['pressure']}) ===")
        for d in res["drivers_by_stage"][st["stage"]][:4]:
            print(f"- {d['dimension']} = {d['value']}: median {d['median_days']}d vs {d['stage_median']}d ({d['deals']} deals)."
                  f"\n    Cause: {d['likely_cause']}\n    Test: {d['fix_to_test']}")
    print(f"\n=== 4. Open deals stuck in {res['bottleneck']['stage']} now: {len(res['stuck'])} ===")
    print(table(res["stuck"][:8]))
    write_csv("stage_velocity.csv", res["stages"])
    write_csv("stage_drivers.csv", [dict(d, stage=st) for st, ds in res["drivers_by_stage"].items() for d in ds])


if __name__ == "__main__":
    main()

"""Pipeline distribution: is pipeline spread across reps in a way that can hit the number?

Team totals hide the problem. A team at 3x coverage can still miss if two reps hold most of it,
one deal is half a rep's quarter, or a rep has more open deals than anyone can work.

Per AE:
  load            open opportunities vs the workable range (`pipeline_distribution.min/max_open_opps_per_ae`)
  coverage        in-quarter pipeline / rep quota (ramp-adjusted, from team.rep_quotas)
  concentration   largest deal and top-3 deals as a share of in-quarter pipeline
  stage mix       share of in-quarter $ still in stages 1-2 (needs to move fast to close this quarter)
  inflow          new opportunities in the last 90 days, vs the rep's share of quota

Team: Gini coefficient of coverage across reps (0 = even, 1 = one rep has it all) and the share
of in-quarter pipeline held by the top two reps.

Flags turn into routing actions: starved, under-covered reps get the next inbound SQLs (the routing
engine's round-robin can weight by this), overloaded reps hand early-stage deals to a peer or SDR
nurture, concentrated reps need a second-path plan for the quarter.

    python -m gtm_strategy_ops.sales_planning.pipeline_distribution
"""
from __future__ import annotations

from datetime import timedelta

from gtm_strategy_ops.sales_planning.team import rep_quotas, roster
from shared_core.config import AS_OF, fiscal_quarter, load_config, parse_date, pct, read_csv, table, to_float, write_csv


def gini(values: list[float]) -> float:
    xs = sorted(v for v in values if v >= 0)
    n, total = len(xs), sum(xs)
    if n == 0 or total == 0:
        return 0.0
    cum = sum((i + 1) * x for i, x in enumerate(xs))
    return round((2 * cum) / (n * total) - (n + 1) / n, 2)


def distribution(cfg: dict | None = None, opps: list[dict] | None = None) -> dict:
    cfg = cfg or load_config()
    opps = opps if opps is not None else read_csv("opportunities.csv")
    pd_cfg = cfg["sales_planning"]["pipeline_distribution"]
    q = cfg["current_fiscal_quarter"]
    quotas = rep_quotas(cfg, q)
    total_quota = sum(quotas.values()) or 1
    stages = [s["name"] for s in cfg["opportunity"]["stages"]]
    early = set(stages[:2])
    since = AS_OF - timedelta(days=90)
    new_total = sum(1 for o in opps if parse_date(o["created_date"]) >= since) or 1
    target = cfg["opportunity"]["coverage_target"]
    rows = []
    for ae, info in roster(cfg).items():
        mine = [o for o in opps if o["owner"] == ae and o["is_closed"] != "True"]
        in_q = sorted([to_float(o["amount"]) for o in mine if fiscal_quarter(parse_date(o["close_date"])) == q
                       and o["forecast_category"] != "Omitted"], reverse=True)
        pipe_q = sum(in_q)
        early_q = sum(to_float(o["amount"]) for o in mine if fiscal_quarter(parse_date(o["close_date"])) == q and o["stage"] in early)
        new = sum(1 for o in opps if o["owner"] == ae and parse_date(o["created_date"]) >= since)
        cov = round(pipe_q / quotas[ae], 2) if quotas[ae] else 0.0
        flags = []
        if len(mine) > pd_cfg["max_open_opps_per_ae"]:
            flags.append("Overloaded")
        if len(mine) < pd_cfg["min_open_opps_per_ae"]:
            flags.append("Starved")
        if quotas[ae] and cov < target:
            flags.append("Under-covered")
        if in_q and pct(in_q[0], pipe_q) > pd_cfg["concentration_flag_pct"]:
            flags.append("Concentrated")
        if pipe_q and pct(early_q, pipe_q) > 70:
            flags.append("Early-heavy")
        rows.append({"owner": ae, "region": info["region"], "open_opps": len(mine), "quota_$": quotas[ae],
                     "pipeline_in_q_$": int(pipe_q), "coverage_x": cov,
                     "largest_deal_%": pct(in_q[0], pipe_q) if in_q else 0.0, "top3_%": pct(sum(in_q[:3]), pipe_q) if in_q else 0.0,
                     "early_stage_%": pct(early_q, pipe_q), "new_opps_90d": new,
                     "inflow_share_%": pct(new, new_total), "quota_share_%": pct(quotas[ae], total_quota),
                     "flags": ", ".join(flags) or "OK", "action": action(flags), "_target_$": target * quotas[ae]})
    covs = [r["coverage_x"] for r in rows if r["quota_$"]]
    pipes = sorted((r["pipeline_in_q_$"] for r in rows), reverse=True)
    team = {"reps": len(rows), "coverage_gini": gini(covs), "top2_share_of_pipeline_%": pct(sum(pipes[:2]), sum(pipes)),
            "reps_under_covered": sum("Under-covered" in r["flags"] for r in rows)}
    return {"reps": rows, "team": team, "routing": routing_priority(rows)}


def action(flags: list[str]) -> str:
    """One action per flag, most urgent first. Several flags -> several actions, joined."""
    out = []
    if "Overloaded" in flags:
        out.append("Close out or re-route stale stage-1/2 deals; pause new routing until under the cap.")
    if "Starved" in flags:
        out.append("Too few deals to work: weight the next inbound SQLs here and point SDRs at this rep's T1 accounts.")
    elif "Under-covered" in flags and "Overloaded" not in flags:
        out.append("Enough deals, not enough dollars this quarter: check which next-quarter deals can honestly be pulled in, "
                   "then prospect the T1 book for size.")
    if "Concentrated" in flags:
        out.append("Second-path plan: name the deals that cover the quarter if the big one slips.")
    if "Early-heavy" in flags:
        out.append("Inspect stage 1-2 deals for a real close date this quarter; move the rest out.")
    return " ".join(out)


def routing_priority(rows: list[dict]) -> list[dict]:
    """Inbound can't be weighted to everyone, and it routes by region. Within each region, the starved or
    under-covered rep with the biggest dollar gap to target coverage gets the next inbound SQLs; the
    others work their own book first."""
    best = {}
    for r in rows:
        if ("Starved" in r["flags"] or "Under-covered" in r["flags"]) and "Overloaded" not in r["flags"]:
            gap = int(max(0, r["_target_$"] - r["pipeline_in_q_$"]))
            if gap and gap > best.get(r["region"], {}).get("gap_$", 0):
                best[r["region"]] = {"region": r["region"], "owner": r["owner"], "gap_$": gap, "flags": r["flags"]}
    return sorted(best.values(), key=lambda g: -g["gap_$"])


def main() -> None:
    res = distribution()
    print("=== Pipeline distribution by AE (current quarter) ===")
    print(table(res["reps"], ["owner", "region", "open_opps", "quota_$", "pipeline_in_q_$", "coverage_x", "largest_deal_%",
                              "top3_%", "early_stage_%", "inflow_share_%", "quota_share_%", "flags"]))
    print("\n=== Team ===")
    print(table([res["team"]]))
    print("\n=== Actions ===")
    for r in res["reps"]:
        if r["action"]:
            print(f"- {r['owner']}: {r['action']}")
    print("\n=== Next inbound SQLs, by region (weight the round-robin toward this rep) ===")
    print(table(res["routing"]))
    write_csv("pipeline_distribution.csv", res["reps"])


if __name__ == "__main__":
    main()

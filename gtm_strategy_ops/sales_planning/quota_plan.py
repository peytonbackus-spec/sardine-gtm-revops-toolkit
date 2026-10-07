"""Quota plan: check this quarter's quotas against capacity, and set next year's from the plan.

Two directions, reconciled:
  Top-down     the bookings plan Finance commits to the board (config `sales_planning.bookings_plan`)
  Bottom-up    what the team can sell: ramped rep equivalents x productivity (capacity_plan.py)

Checks on the quotas in force today (config `quota` for the current quarter):
  - Region quota vs region capacity. Implied over-assignment = quota / capacity - 1. A practitioner
    range is about 10-25%; far above that, reps miss while the company "hits plan", which is a
    culture problem as much as a math one (Kellogg, see README).
  - Quota sitting on a ramping AE, or a region with quota and no ramped AE to carry it.
  - Last quarter's attainment spread: if almost nobody hits, quotas (not people) are the problem.

Next-year proposal: for each plan quarter, total quota = plan x (1 + over-assignment), split by
region in proportion to region capacity, then by AE in proportion to ramp (team.rep_quotas logic).

    python -m gtm_strategy_ops.sales_planning.quota_plan
"""
from __future__ import annotations

from gtm_strategy_ops.sales_planning.team import ramp_factor, rep_quotas, roster, shift_quarter
from shared_core.config import fiscal_quarter, load_config, parse_date, pct, read_csv, table, to_float, write_csv


def region_capacity(cfg: dict, q: str) -> dict[str, float]:
    prod = cfg["sales_team"]["ae_quarterly_productivity"]
    out = {r: 0.0 for r in cfg["regions"]}
    for r in roster(cfg).values():
        out[r["region"]] += ramp_factor(r["start_date"], q, cfg) * prod[r["region"]]
    return out


def check_current(cfg: dict) -> list[dict]:
    q = cfg["current_fiscal_quarter"]
    cap = region_capacity(cfg, q)
    team = roster(cfg)
    lo, hi = 10, 25
    rows = []
    for region, quota in cfg["quota"][q].items():
        aes = [a for a, r in team.items() if r["region"] == region]
        ramped = [a for a in aes if ramp_factor(team[a]["start_date"], q, cfg) >= 1]
        oa = round(100 * (quota / cap[region] - 1), 1) if cap[region] else None
        if not cap[region]:
            flag = "No ramped capacity: quota cannot be carried"
        elif oa > 40:
            flag = "Quota far above capacity: expect most reps to miss"
        elif oa > hi:
            flag = "Above the usual over-assignment range"
        elif oa < 0:
            flag = "Quota below capacity: room to raise or to re-deploy"
        else:
            flag = "OK" if oa >= lo else "Thin cushion: one miss and the region misses"
        if not ramped and aes:
            flag += "; no fully ramped AE in region"
        rows.append({"region": region, "quota_$": quota, "capacity_$": int(cap[region]), "implied_over_assignment_%": oa,
                     "aes": len(aes), "ramped_aes": len(ramped), "flag": flag})
    return rows


def attainment_spread(cfg: dict, opps: list[dict]) -> dict:
    prev_q = shift_quarter(cfg["current_fiscal_quarter"], -1)
    quotas = rep_quotas(cfg, prev_q)
    team = roster(cfg)
    att = []
    for ae, qv in quotas.items():
        if qv and ramp_factor(team[ae]["start_date"], prev_q, cfg) >= 1:
            won = sum(to_float(o["amount"]) for o in opps if o["owner"] == ae and o["is_won"] == "True"
                      and fiscal_quarter(parse_date(o["close_date"])) == prev_q)
            att.append(pct(won, qv))
    n = len(att) or 1
    return {"quarter": prev_q, "ramped_reps": len(att), "at_or_above_100_%": pct(sum(a >= 100 for a in att), n),
            "70_to_99_%": pct(sum(70 <= a < 100 for a in att), n), "below_70_%": pct(sum(a < 70 for a in att), n),
            "mean_attainment_%": round(sum(att) / n, 1) if att else 0.0}


def propose(cfg: dict) -> list[dict]:
    """Next-year quota by quarter, region and AE from the bookings plan and capacity shares."""
    oa = cfg["sales_planning"]["over_assignment_pct"] / 100
    team = roster(cfg)
    rows = []
    for q, target in cfg["sales_planning"]["bookings_plan"].items():
        cap = region_capacity(cfg, q)
        total_cap = sum(cap.values()) or 1
        for ae, r in team.items():
            region_quota = target * (1 + oa) * cap[r["region"]] / total_cap
            pool = sum(ramp_factor(t["start_date"], q, cfg) for t in team.values() if t["region"] == r["region"])
            share = ramp_factor(r["start_date"], q, cfg) / pool if pool else 0
            rows.append({"quarter": q, "owner": ae, "region": r["region"], "ramp_%": int(100 * ramp_factor(r["start_date"], q, cfg)),
                         "proposed_quota_$": int(round(region_quota * share, -3))})
    return rows


def main() -> None:
    cfg = load_config()
    opps = read_csv("opportunities.csv")
    print(f"=== {cfg['current_fiscal_quarter']} quota vs capacity by region ===")
    cur = check_current(cfg)
    print(table(cur))
    print("\n=== Last quarter's attainment spread (ramped reps) ===")
    print(table([attainment_spread(cfg, opps)]))
    prop = propose(cfg)
    first_q = next(iter(cfg["sales_planning"]["bookings_plan"]))
    print(f"\n=== Proposed quota, {first_q} (plan x (1 + {cfg['sales_planning']['over_assignment_pct']}%), split by capacity, then ramp) ===")
    print(table([r for r in prop if r["quarter"] == first_q]))
    write_csv("quota_check.csv", cur)
    write_csv("quota_proposal.csv", prop)


if __name__ == "__main__":
    main()

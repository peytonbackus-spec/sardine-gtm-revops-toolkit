"""AE capacity plan: can the team we have (plus who we hire) deliver the bookings plan?

Method (a productivity-based capacity model, after Dave Kellogg's write-up; see README):
  1. Ramped rep equivalents (RREs) per quarter: each AE counts as their ramp factor for that quarter
     (config `sales_team.ramp_vector`), reduced by expected attrition.
  2. Capacity = RREs x steady-state productivity (what a ramped AE actually sells per quarter in
     that region; `ae_quarterly_productivity`). Productivity, not quota: quota is a target.
  3. Gap = bookings plan - capacity. Hires to close it are scheduled early enough to be ramped:
     a hire started in quarter s contributes ramp(q - s + 1) x productivity in quarter q.
  4. Quota capacity = capacity x (1 + over-assignment): the minimum total quota to hand out.

The output answers three questions the CRO and Finance ask every planning cycle: how much can we
sell with the team we have, how many AEs do we need and when must they start, and what is the
smallest total quota that still covers the plan.

    python -m gtm_strategy_ops.sales_planning.capacity_plan
"""
from __future__ import annotations

import math

from gtm_strategy_ops.sales_planning.team import quarter_index, ramp_factor, roster, shift_quarter
from shared_core.config import load_config, table, write_csv


def survival(quarters_ahead: int, annual_attrition_pct: float) -> float:
    """Expected share of today's reps still here after n quarters."""
    q_rate = 1 - (1 - annual_attrition_pct / 100) ** 0.25
    return (1 - q_rate) ** max(0, quarters_ahead)


def blended_productivity(cfg: dict) -> float:
    """Average ramped productivity, weighted by where today's AEs sit. Used for new hires."""
    prod = cfg["sales_team"]["ae_quarterly_productivity"]
    regions = [r["region"] for r in roster(cfg).values()]
    return sum(prod[r] for r in regions) / len(regions)


def hire_ramp(start_q: str, q: str, cfg: dict) -> float:
    t = quarter_index(q) - quarter_index(start_q) + 1
    if t < 1:
        return 0.0
    vec = cfg["sales_team"]["ramp_vector"]
    return float(vec[min(t, len(vec)) - 1])


def existing_capacity(cfg: dict, q: str) -> tuple[float, float]:
    """(RREs, $ capacity) of the current roster in quarter q, net of expected attrition."""
    team, prod = roster(cfg), cfg["sales_team"]["ae_quarterly_productivity"]
    ahead = quarter_index(q) - quarter_index(cfg["current_fiscal_quarter"])
    keep = survival(ahead, cfg["sales_team"]["annual_attrition_pct"])
    rre = sum(ramp_factor(r["start_date"], q, cfg) for r in team.values()) * keep
    cap = sum(ramp_factor(r["start_date"], q, cfg) * prod[r["region"]] for r in team.values()) * keep
    return rre, cap


def plan(cfg: dict | None = None) -> dict:
    cfg = cfg or load_config()
    sp = cfg["sales_planning"]
    quarters = list(sp["bookings_plan"])
    earliest = shift_quarter(cfg["current_fiscal_quarter"], sp["hire_lead_time_quarters"])
    full_after = len(cfg["sales_team"]["ramp_vector"]) - 1
    per_hire = blended_productivity(cfg)
    oa = sp["over_assignment_pct"] / 100
    hires: dict[str, int] = {}
    rows = []
    for q in quarters:
        rre, cap = existing_capacity(cfg, q)
        hire_cap = sum(n * hire_ramp(s, q, cfg) * per_hire for s, n in hires.items())
        gap = sp["bookings_plan"][q] - cap - hire_cap
        if gap > 0:
            # Start as early as allowed but no earlier than needed to be fully ramped by q.
            start = max(earliest, shift_quarter(q, -full_after), key=quarter_index)
            r = hire_ramp(start, q, cfg)
            if r > 0:
                n = math.ceil(gap / (r * per_hire))
                hires[start] = hires.get(start, 0) + n
                hire_cap += n * r * per_hire
        hire_rre = sum(n * hire_ramp(s, q, cfg) for s, n in hires.items())
        total = cap + hire_cap
        rows.append({"quarter": q, "plan_$": sp["bookings_plan"][q], "existing_rre": round(rre, 2),
                     "existing_capacity_$": int(cap), "new_hire_rre": round(hire_rre, 2), "new_hire_capacity_$": int(hire_cap),
                     "total_capacity_$": int(total), "capacity_vs_plan_%": round(100 * total / sp["bookings_plan"][q], 1),
                     "min_quota_to_assign_$": int(round(sp["bookings_plan"][q] * (1 + oa), -3)),
                     "status": "Covered" if total >= sp["bookings_plan"][q] * 0.995 else "Short: hires cannot ramp in time"})
    hire_rows = [{"start_quarter": s, "ae_hires": n, "open_req_by": shift_quarter(s, -sp["hire_lead_time_quarters"])}
                 for s, n in sorted(hires.items(), key=lambda x: quarter_index(x[0]))]
    return {"capacity": rows, "hires": hire_rows, "per_hire_productivity": int(per_hire), "earliest_start": earliest}


def main() -> None:
    res = plan()
    print("=== Capacity vs bookings plan (existing team net of attrition, plus planned hires) ===")
    print(table(res["capacity"]))
    print(f"\n=== Hiring plan (new AE productivity ${res['per_hire_productivity']:,}/quarter once ramped; "
          f"earliest start {res['earliest_start']}) ===")
    print(table(res["hires"]) if res["hires"] else "(no hires needed)")
    short = [r for r in res["capacity"] if r["status"] != "Covered"]
    if short:
        print("\nShort quarters can't be fixed by hiring alone: raise productivity (win rate, deal size), add "
              "partner capacity, or move the plan. " + ", ".join(r["quarter"] for r in short))
    write_csv("capacity_plan.csv", res["capacity"])
    write_csv("hiring_plan.csv", res["hires"])


if __name__ == "__main__":
    main()

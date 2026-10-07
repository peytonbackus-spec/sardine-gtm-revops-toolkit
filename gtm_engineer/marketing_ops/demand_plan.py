"""Demand plan: the reverse funnel Marketing Ops and RevOps agree on each planning cycle.

Starts from the bookings plan (config `sales_planning.bookings_plan`) and works backward with the
company's own trailing conversion rates, so Marketing's lead and MQL targets are tied to the same
number Sales is carrying:

  pipeline $ needed  = bookings plan / dollar win rate (trailing year)
  opps needed        = pipeline $ / average opportunity size
  opps by source     = opps x target source mix (config `marketing_ops.demand_plan.sourced_mix_pct`)
  lead-originated opps (Marketing, SDR, Partner) split by channel on the trailing first-touch mix
  leads needed       = channel opps / that channel's lead -> opp rate
  gap                = leads needed vs the channel's run rate over the last 90 days

Pipeline has to exist about one sales cycle before it closes, so the plan for quarter Q is a
creation target for quarter Q - `create_ahead_quarters`. That is the number to hold Marketing and
the SDR team to this quarter.

    python -m gtm_engineer.marketing_ops.demand_plan
"""
from __future__ import annotations

from collections import Counter
from datetime import timedelta

from gtm_engineer.marketing_ops.campaign_report import attribution, channel_funnel, load, touches_by_lead
from gtm_strategy_ops.sales_planning.team import shift_quarter
from shared_core.config import AS_OF, load_config, parse_date, table, to_float, write_csv

LEAD_SOURCES = ("Marketing", "SDR", "Partner")   # opportunity sources that start as a lead with campaign touches


def trailing_rates(opps: list[dict], days: int = 365) -> dict:
    since = AS_OF - timedelta(days=days)
    book = [o for o in opps if o["type"] != "Renewal"]
    closed = [o for o in book if o["is_closed"] == "True" and parse_date(o["close_date"]) >= since]
    won_amt = sum(to_float(o["amount"]) for o in closed if o["is_won"] == "True")
    all_amt = sum(to_float(o["amount"]) for o in closed)
    created = [o for o in book if parse_date(o["created_date"]) >= since]
    return {"win_rate_$": won_amt / all_amt if all_amt else 0.0,
            "avg_opp_$": sum(to_float(o["amount"]) for o in created) / len(created) if created else 0.0,
            "closed_n": len(closed), "created_n": len(created)}


def channel_mix(data: dict) -> dict[str, float]:
    """Share of converted leads by first-touch campaign type (the channels that actually make opps)."""
    camp = {c["campaign_id"]: c["type"] for c in data["campaigns"]}
    by_lead = touches_by_lead(data["members"])
    n = Counter(camp[by_lead[lead["lead_id"]][0]["campaign_id"]] for lead in data["leads"]
                if lead["opportunity_id"] and by_lead.get(lead["lead_id"]))
    total = sum(n.values())
    return {k: v / total for k, v in n.items()} if total else {}


def run_rate(data: dict, days: int = 90) -> Counter:
    """First-touch leads created per channel in the last `days` (about one quarter)."""
    camp = {c["campaign_id"]: c["type"] for c in data["campaigns"]}
    by_lead = touches_by_lead(data["members"])
    since = AS_OF - timedelta(days=days)
    return Counter(camp[by_lead[lead["lead_id"]][0]["campaign_id"]] for lead in data["leads"]
                   if by_lead.get(lead["lead_id"]) and parse_date(lead["created_date"]) >= since)


def plan(cfg: dict | None = None, data: dict | None = None) -> dict:
    cfg, data = cfg or load_config(), data or load()
    dp = cfg["marketing_ops"]["demand_plan"]
    labels = {k: v["label"] for k, v in cfg["marketing_ops"]["campaign_types"].items()}
    rates = trailing_rates(data["opps"])
    funnel = {r["channel"]: r for r in channel_funnel(data, cfg, attribution(data, cfg))}
    mix, now = channel_mix(data), run_rate(data)
    lead_share = sum(dp["sourced_mix_pct"].get(s, 0) for s in LEAD_SOURCES) / 100
    summary, detail = [], []
    for q, bookings in cfg["sales_planning"]["bookings_plan"].items():
        pipe = bookings / rates["win_rate_$"] if rates["win_rate_$"] else 0.0
        opps = pipe / rates["avg_opp_$"] if rates["avg_opp_$"] else 0.0
        create_in = shift_quarter(q, -dp["create_ahead_quarters"])
        row = {"close_quarter": q, "create_in": create_in, "bookings_plan_$": bookings, "pipeline_needed_$": int(pipe),
               "opps_needed": round(opps)}
        row.update({f"{s.lower()}_opps": round(opps * pct / 100) for s, pct in dp["sourced_mix_pct"].items()})
        summary.append(row)
        for k, share in sorted(mix.items(), key=lambda kv: -kv[1]):
            ch = labels.get(k, k)
            f = funnel.get(ch, {})
            opp_rate = (f.get("opp_%") or 0) / 100
            ch_opps = opps * lead_share * share
            leads = ch_opps / opp_rate if opp_rate else 0.0
            mqls = leads * (f.get("mql_%") or 0) / 100
            have = now.get(k, 0)
            gap = pct_gap(leads, have)
            detail.append({"create_in": create_in, "for_close_in": q, "channel": ch, "opps_needed": round(ch_opps, 1),
                           "lead_to_opp_%": f.get("opp_%", ""), "leads_needed": round(leads), "mqls_needed": round(mqls),
                           "leads_last_90d": have, "gap_%": gap,
                           "status": "On pace" if gap >= -10 else ("Behind" if gap >= -30 else "Off pace")})
    return {"rates": rates, "summary": summary, "detail": detail, "mix": mix}


def pct_gap(need: float, have: float) -> float:
    """Run rate vs need: -40 means the channel produces 40% fewer leads than the plan needs."""
    return round(100.0 * (have - need) / need, 1) if need else 0.0


def narrative(res: dict) -> str:
    first = res["summary"][0]
    now = [d for d in res["detail"] if d["create_in"] == first["create_in"]]
    off = sorted([d for d in now if d["status"] != "On pace"], key=lambda d: d["gap_%"])
    r = res["rates"]
    text = (f"To book ${first['bookings_plan_$']:,.0f} in {first['close_quarter']}, {first['create_in']} has to create "
            f"${first['pipeline_needed_$']:,.0f} of pipeline ({first['opps_needed']} opps at a {r['win_rate_$']:.0%} dollar win rate "
            f"and ${r['avg_opp_$']:,.0f} average opp). ")
    if off:
        text += "Short on: " + "; ".join(f"{d['channel']} {d['leads_last_90d']} leads vs {d['leads_needed']} needed ({d['gap_%']}%)"
                                          for d in off[:3]) + ". Fix the biggest gap first or move the target to a channel that is on pace."
    else:
        text += "Every channel is on pace at its current run rate."
    return text


def main() -> None:
    res = plan()
    r = res["rates"]
    print(f"=== Inputs (trailing year): dollar win rate {r['win_rate_$']:.1%} on {r['closed_n']} closed; "
          f"average opp ${r['avg_opp_$']:,.0f} on {r['created_n']} created ===")
    print("\n=== 1. Pipeline to create, by source (creation quarter = close quarter - 1) ===")
    print(table(res["summary"]))
    first = res["summary"][0]["create_in"]
    print(f"\n=== 2. {first}: leads needed by channel vs the last 90 days ===")
    print(table([d for d in res["detail"] if d["create_in"] == first]))
    print("\n=== 3. Narrative ===\n" + narrative(res))
    write_csv("demand_plan_summary.csv", res["summary"])
    write_csv("demand_plan_by_channel.csv", res["detail"])


if __name__ == "__main__":
    main()

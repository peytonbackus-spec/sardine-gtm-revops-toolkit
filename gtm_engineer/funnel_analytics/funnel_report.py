"""Lead-to-opportunity funnel analytics + early-pipeline outlook.

Role scope (GTM Engineer):
  foundational analytics for lead-to-opportunity conversion tracking
  dashboards covering volume, conversion velocity, pipeline value and account penetration
  early-pipeline outlooks and performance narratives

Outputs (console + outputs/*.csv, which feed the dashboard in dashboard-spec.md):
  1. Monthly cohort funnel: created -> MQL -> SAL -> SQL -> Opp
  2. Funnel by source, with median velocity (created -> SQL days)
  3. Pipeline sourced ($) by source and product line
  4. Account penetration: ICP accounts with an engaged contact
  5. Early-pipeline outlook: expected opp $ from leads in flight right now
  6. Auto-written narrative: the three sentences a leader actually reads

    python -m gtm_engineer.funnel_analytics.funnel_report
"""
from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from statistics import median

from shared_core.config import AS_OF, dedupe_leads, parse_date, pct, read_csv, table, to_float, write_csv

STAGES = ["mql_date", "sal_date", "sql_date", "converted_date"]


def cohort_funnel(leads: list[dict]) -> list[dict]:
    by_month = defaultdict(list)
    for l in leads:
        by_month[l["created_date"][:7]].append(l)
    out = []
    for month in sorted(by_month):
        rows = by_month[month]
        n = len(rows)
        counts = [sum(1 for r in rows if r.get(s)) for s in STAGES]
        out.append({"cohort": month, "leads": n, "mql_%": pct(counts[0], n), "sal_%": pct(counts[1], n),
                    "sql_%": pct(counts[2], n), "opp_%": pct(counts[3], n), "opps": counts[3]})
    return out


def by_source(leads: list[dict], opps_by_id: dict) -> list[dict]:
    groups = defaultdict(list)
    for l in leads:
        groups[l["lead_source"]].append(l)
    out = []
    for src, rows in groups.items():
        n = len(rows)
        days = [(parse_date(r["sql_date"]) - parse_date(r["created_date"])).days for r in rows if r.get("sql_date")]
        pipe = sum(to_float(opps_by_id.get(r["opportunity_id"], {}).get("amount")) for r in rows if r.get("opportunity_id"))
        out.append({"source": src, "leads": n, "mql_%": pct(sum(1 for r in rows if r["mql_date"]), n),
                    "lead_to_opp_%": pct(sum(1 for r in rows if r["converted_date"]), n),
                    "median_days_to_sql": median(days) if days else "", "pipeline_$": int(pipe),
                    "pipeline_per_lead_$": int(pipe / n) if n else 0})
    return sorted(out, key=lambda r: -r["pipeline_$"])


def account_penetration(leads: list[dict], accounts: list[dict]) -> list[dict]:
    engaged = defaultdict(set)
    for l in leads:
        if l.get("sal_date"):
            engaged[l["account_id"]].add(l["persona"])
    out = []
    for seg in sorted({a["segment"] for a in accounts} - {"other"}):
        accts = [a for a in accounts if a["segment"] == seg]
        hit = [a for a in accts if a["account_id"] in engaged]
        multi = [a for a in hit if len(engaged[a["account_id"]]) >= 2]
        out.append({"segment": seg, "accounts": len(accts), "engaged_%": pct(len(hit), len(accts)),
                    "multi_persona_%": pct(len(multi), len(accts))})
    return out


def early_pipeline_outlook(leads: list[dict], opps_by_id: dict) -> dict:
    """Expected opportunity $ over the next ~30 days from leads currently in flight.

    P(convert | current status) comes from matured history; value comes from the
    median amount of lead-sourced opps. Simple and explainable on purpose: the
    output is a range for a Monday pipeline meeting, not a forecast of record.
    """
    matured = [l for l in leads if (AS_OF - parse_date(l["created_date"])).days > 60]

    def p_from(status_field: str) -> float:
        base = [l for l in matured if l.get(status_field)]
        return sum(1 for l in base if l["converted_date"]) / len(base) if base else 0.0

    amounts = [to_float(o["amount"]) for o in opps_by_id.values() if o.get("originating_lead_id")]
    med = median(amounts) if amounts else 0
    in_flight = {"SQL": [l for l in leads if l["status"] == "SQL"],
                 "Working": [l for l in leads if l["status"] == "Working"],
                 "MQL": [l for l in leads if l["status"] == "MQL"]}
    probs = {"SQL": p_from("sql_date"), "Working": p_from("sal_date"), "MQL": p_from("mql_date")}
    expected_opps = sum(len(v) * probs[k] for k, v in in_flight.items())
    return {"in_flight": {k: len(v) for k, v in in_flight.items()}, "conv_prob": {k: round(v, 2) for k, v in probs.items()},
            "expected_opps": round(expected_opps, 1), "median_opp_$": int(med),
            "expected_pipeline_$": int(expected_opps * med),
            "range_$": (int(expected_opps * med * 0.7), int(expected_opps * med * 1.3))}


def narrative(cohorts: list[dict], sources: list[dict], outlook: dict) -> str:
    # only cohorts old enough (60+ days) to have converted; younger cohorts always look worse
    cutoff = (AS_OF - timedelta(days=60)).strftime("%Y-%m")
    recent = [c for c in cohorts if c["cohort"] < cutoff and c["leads"] >= 20][-3:] or cohorts[-3:]
    best = max(sources, key=lambda s: s["pipeline_per_lead_$"])
    worst = min((s for s in sources if s["leads"] >= 20), key=lambda s: s["pipeline_per_lead_$"])
    trend = "up" if recent[-1]["opp_%"] >= recent[0]["opp_%"] else "down"
    return (f"Lead-to-opp conversion is trending {trend} across the last three matured cohorts "
            f"({recent[0]['cohort']}: {recent[0]['opp_%']}% -> {recent[-1]['cohort']}: {recent[-1]['opp_%']}%). "
            f"{best['source']} produces the most pipeline per lead (${best['pipeline_per_lead_$']:,}); "
            f"{worst['source']} the least (${worst['pipeline_per_lead_$']:,}), so review its spend or qualification. "
            f"Leads in flight point to ~{outlook['expected_opps']} new opps worth "
            f"${outlook['range_$'][0]:,}-${outlook['range_$'][1]:,} over the next month.")


def main() -> None:
    leads = dedupe_leads(read_csv("leads.csv"))  # same population as the SQL semantic layer
    opps_by_id = {o["opportunity_id"]: o for o in read_csv("opportunities.csv")}
    cohorts, sources = cohort_funnel(leads), by_source(leads, opps_by_id)
    pen, outlook = account_penetration(leads, read_csv("accounts.csv")), early_pipeline_outlook(leads, opps_by_id)
    print("=== 1. Monthly cohort funnel ===")
    print(table(cohorts))
    print("\n=== 2-3. Funnel, velocity and pipeline by source ===")
    print(table(sources))
    print("\n=== 4. Account penetration (ICP segments) ===")
    print(table(pen))
    print("\n=== 5. Early-pipeline outlook ===")
    for k, v in outlook.items():
        print(f"  {k}: {v}")
    print("\n=== 6. Narrative ===\n" + narrative(cohorts, sources, outlook))
    for name, rows in (("funnel_cohorts.csv", cohorts), ("funnel_by_source.csv", sources), ("account_penetration.csv", pen)):
        write_csv(name, rows)


if __name__ == "__main__":
    main()

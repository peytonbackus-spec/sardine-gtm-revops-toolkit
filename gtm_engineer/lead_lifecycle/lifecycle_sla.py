"""Lead lifecycle SLA monitor.

Role scope (GTM Engineer): define qualification standards across Marketing, SDRs
and Account Executives, and drive alignment on data standards and service levels.

An SLA nobody measures doesn't hold. This reports MQL->SAL acceptance time
against the agreed SLA by SDR and by lead source, plus "stuck" leads: Working
past the SAL->SQL window, which should be converted or recycled.

    python -m gtm_engineer.lead_lifecycle.lifecycle_sla
"""
from __future__ import annotations

from collections import defaultdict

from shared_core.config import AS_OF, load_config, parse_date, pct, read_csv, table, to_float


def sla_report(leads: list[dict], cfg: dict) -> dict:
    sla = cfg["lead_lifecycle"]["sla_hours"]["mql_to_sal"]
    window = cfg["lead_lifecycle"]["sla_hours"]["sal_to_sql_days"]
    by_owner = defaultdict(lambda: [0, 0])
    by_source = defaultdict(lambda: [0, 0])
    stuck = []
    for l in leads:
        if l.get("mql_to_sal_hours"):
            met = to_float(l["mql_to_sal_hours"]) <= sla
            for bucket, key in ((by_owner, l["owner"]), (by_source, l["lead_source"])):
                bucket[key][0] += 1
                bucket[key][1] += met
        sal = parse_date(l.get("sal_date"))
        if l["status"] == "Working" and sal and (AS_OF - sal).days > window:
            stuck.append({"lead_id": l["lead_id"], "owner": l["owner"], "company": l["company"],
                          "days_since_sal": (AS_OF - sal).days})

    def rows(bucket):
        return sorted(({"key": k, "accepted": n, "within_sla": m, "sla_%": pct(m, n)} for k, (n, m) in bucket.items()),
                      key=lambda r: r["sla_%"])

    total = sum(v[0] for v in by_owner.values())
    met = sum(v[1] for v in by_owner.values())
    return {"sla_hours": sla, "overall_%": pct(met, total), "by_owner": rows(by_owner), "by_source": rows(by_source),
            "stuck": sorted(stuck, key=lambda r: -r["days_since_sal"])}


def main() -> None:
    cfg = load_config()
    rep = sla_report(read_csv("leads.csv"), cfg)
    print(f"=== MQL -> SAL SLA ({rep['sla_hours']}h): {rep['overall_%']}% met ===\n")
    print("By SDR:")
    print(table(rep["by_owner"]))
    print("\nBy lead source (high-intent sources should be fastest):")
    print(table(rep["by_source"]))
    print(f"\nStuck in Working > {cfg['lead_lifecycle']['sla_hours']['sal_to_sql_days']} days: {len(rep['stuck'])}")
    if rep["stuck"]:
        print(table(rep["stuck"][:10]))


if __name__ == "__main__":
    main()

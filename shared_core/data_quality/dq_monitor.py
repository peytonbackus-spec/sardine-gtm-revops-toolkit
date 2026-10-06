"""Data-quality monitor for Salesforce Lead and Opportunity data.

Both role tracks need it:
  GTM Engineer:        data-quality monitoring and reconciliation processes
  GTM Strategy & Ops:  data-quality monitoring across the CRM and the forecasting tool

Each rule is a small function that returns the failing records. The monitor
reports pass rate per rule, so a weekly run gives a trend line, and writes the
failures to outputs/ for the owner to fix. In production the same rules run as
a scheduled SOQL/warehouse job with a Slack digest; here they run on sample_data/.

    python -m shared_core.data_quality.dq_monitor
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Callable

from shared_core.config import AS_OF, load_config, parse_date, pct, read_csv, table, to_float, write_csv

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PERSONAL_DOMAINS = ("gmail.", "yahoo.", "hotmail.", "outlook.", "icloud.")


@dataclass
class Rule:
    rule_id: str
    obj: str            # Lead | Opportunity
    owner_role: str     # who fixes it: GTM Engineer | GTM Strategy & Ops | Shared
    severity: str       # high | medium | low
    description: str
    check: Callable[[dict], bool]   # returns True when the record FAILS


def lead_rules(cfg: dict) -> list[Rule]:
    segments = set(cfg["segments"])
    return [
        Rule("L01", "Lead", "GTM Engineer", "high", "Email missing or malformed",
             lambda r: not EMAIL_RE.match(r.get("email", ""))),
        Rule("L02", "Lead", "GTM Engineer", "medium", "Personal email domain on a B2B lead",
             lambda r: any(p in r.get("email", "") for p in PERSONAL_DOMAINS)),
        Rule("L03", "Lead", "GTM Engineer", "high", "Region blank, so routing cannot assign a pod",
             lambda r: not r.get("region")),
        Rule("L04", "Lead", "GTM Engineer", "medium", "Segment missing or not in config",
             lambda r: r.get("segment") not in segments),
        Rule("L05", "Lead", "GTM Engineer", "high", "Disqualified without a disqualify reason",
             lambda r: r.get("status") == "Disqualified" and not r.get("disqualify_reason")),
        Rule("L06", "Lead", "GTM Engineer", "high", "Converted lead not linked to an opportunity",
             lambda r: r.get("status") == "Converted" and not r.get("opportunity_id")),
        Rule("L07", "Lead", "GTM Engineer", "medium", "MQL/Working lead still sitting in Marketing Queue",
             lambda r: r.get("status") in ("MQL", "Working", "SQL") and r.get("owner") == "Marketing Queue"),
    ]


def opp_rules(cfg: dict) -> list[Rule]:
    stage_names = [s["name"] for s in cfg["opportunity"]["stages"]]
    late_stages = set(stage_names[2:5])
    return [
        Rule("O01", "Opportunity", "GTM Strategy & Ops", "high", "Open opportunity with close date in the past",
             lambda r: r["is_closed"] != "True" and (parse_date(r["close_date"]) or AS_OF) < AS_OF),
        Rule("O02", "Opportunity", "GTM Strategy & Ops", "high", "Amount is zero or blank",
             lambda r: to_float(r.get("amount")) <= 0),
        Rule("O03", "Opportunity", "GTM Strategy & Ops", "high", "Closed Lost without a closed-lost reason",
             lambda r: r["stage"] == "Closed Lost" and not r.get("closed_lost_reason")),
        Rule("O04", "Opportunity", "GTM Strategy & Ops", "medium", "Open opportunity has no next step",
             lambda r: r["is_closed"] != "True" and not r.get("next_step")),
        Rule("O05", "Opportunity", "GTM Strategy & Ops", "high", "Commit forecast category while still in stage 1-2",
             lambda r: r["forecast_category"] == "Commit" and r["stage"] in stage_names[:2]),
        Rule("O06", "Opportunity", "GTM Strategy & Ops", "medium", "Stage 3+ with no economic buyer engaged",
             lambda r: r["stage"] in late_stages and r.get("economic_buyer_engaged") != "True"),
        Rule("O07", "Opportunity", "GTM Strategy & Ops", "medium", "Partner-sourced opp with no partner named",
             lambda r: r.get("source") == "Partner" and not r.get("partner")),
        Rule("O08", "Opportunity", "Shared", "medium", "Marketing/SDR-sourced opp with no originating lead",
             lambda r: r.get("source") in ("Marketing", "SDR") and not r.get("originating_lead_id")),
    ]


def duplicate_leads(leads: list[dict]) -> list[dict]:
    """Reconciliation check: same email appearing on more than one lead."""
    counts = Counter(l["email"].lower() for l in leads if l.get("email"))
    return [l for l in leads if l.get("email") and counts[l["email"].lower()] > 1]


def run(leads: list[dict] | None = None, opps: list[dict] | None = None) -> dict:
    cfg = load_config()
    leads = leads if leads is not None else read_csv("leads.csv")
    opps = opps if opps is not None else read_csv("opportunities.csv")
    results, failures = [], []
    for rules, records, key in ((lead_rules(cfg), leads, "lead_id"), (opp_rules(cfg), opps, "opportunity_id")):
        for rule in rules:
            failed = [r for r in records if rule.check(r)]
            results.append({"rule": rule.rule_id, "object": rule.obj, "owner": rule.owner_role, "severity": rule.severity,
                            "description": rule.description, "checked": len(records), "failed": len(failed),
                            "pass_rate_%": round(100 - pct(len(failed), len(records)), 1)})
            failures += [{"rule": rule.rule_id, "record_id": r[key], "description": rule.description,
                          "owner_role": rule.owner_role} for r in failed]
    dups = duplicate_leads(leads)
    results.append({"rule": "R01", "object": "Lead", "owner": "GTM Engineer", "severity": "medium",
                    "description": "Duplicate leads (same email)", "checked": len(leads), "failed": len(dups),
                    "pass_rate_%": round(100 - pct(len(dups), len(leads)), 1)})
    failures += [{"rule": "R01", "record_id": l["lead_id"], "description": "Duplicate email", "owner_role": "GTM Engineer"} for l in dups]
    total_checks = sum(r["checked"] for r in results)
    total_fail = sum(r["failed"] for r in results)
    return {"results": results, "failures": failures, "overall_pass_rate": round(100 - pct(total_fail, total_checks), 2)}


def main() -> None:
    out = run()
    print("=== GTM Data-Quality Monitor (as of", AS_OF, ") ===\n")
    print(table(out["results"], ["rule", "object", "owner", "severity", "failed", "pass_rate_%", "description"]))
    print(f"\nOverall record-check pass rate: {out['overall_pass_rate']}%")
    path = write_csv("dq_failures.csv", out["failures"])
    print(f"Failing records for owners to fix -> {path.relative_to(path.parent.parent)}")


if __name__ == "__main__":
    main()

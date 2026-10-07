"""CRM request intake: triage, SLA tracking and backlog health for Salesforce and HubSpot requests.

Process spec: crm-request-intake.md. This module runs the rules on the request queue
(sample_data/crm_requests.csv; in production, a Salesforce case/record type or a Jira/Linear queue).

Priority (first match wins):
  P0  Blocks deal: a live deal or a rep's ability to sell is broken today
  P1  Blocks team, or due within 3 business days
  P2  Improves efficiency for 10+ users
  P3  everything else (batched into the release train)
Change class (config `sales_planning.request_intake.change_classes`) decides the path:
  standard  same-week, no release (reports, list views, access, data fixes)
  normal    built in sandbox, user-tested, shipped in the fortnightly release
  major     design review with the requesting leader first (automation, data model, routing, integrations)

SLA = first response with priority, owner and an ETA, measured in business hours.

    python -m gtm_strategy_ops.sales_planning.request_triage
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta

from shared_core.config import AS_OF, load_config, parse_date, pct, read_csv, table, write_csv

EFFORT_POINTS = {"S": 1, "M": 2, "L": 5, "XL": 8}
IMPACT_POINTS = {"Blocks deal": 10, "Blocks team": 6, "Improves efficiency": 3, "Nice to have": 1}
SELF_SERVE = {"Report / Dashboard", "List View"}


def business_days(start: date, end: date) -> int:
    """Weekdays from start to end (0 if same day)."""
    if end <= start:
        return 0
    days, d = 0, start
    while d < end:
        d += timedelta(days=1)
        if d.weekday() < 5:
            days += 1
    return days


def priority(r: dict) -> str:
    if r["revenue_impact"] == "Blocks deal":
        return "P0"
    due = parse_date(r["due_date"])
    new_hire_access = r["category"] == "Access / Permissions" and "new" in r["summary"].lower()   # a seller who can't sell
    if (r["revenue_impact"] == "Blocks team" or new_hire_access
            or (due and business_days(parse_date(r["submitted_date"]), due) <= 3)):
        return "P1"
    if r["revenue_impact"] == "Improves efficiency" and int(r["users_affected"]) >= 10:
        return "P2"
    return "P3"


def change_class(category: str, cfg: dict) -> str:
    for cls, cats in cfg["sales_planning"]["request_intake"]["change_classes"].items():
        if category in cats:
            return cls
    return "normal"


def score(r: dict) -> float:
    """Order inside a priority: impact x reach / effort (a RICE-style score without the confidence term)."""
    reach = 1 + min(int(r["users_affected"]), 40) / 10
    return round(IMPACT_POINTS[r["revenue_impact"]] * reach / EFFORT_POINTS[r["effort"]], 1)


def triage(cfg: dict | None = None, requests: list[dict] | None = None) -> dict:
    cfg = cfg or load_config()
    reqs = requests if requests is not None else read_csv("crm_requests.csv")
    sla_hours = cfg["sales_planning"]["request_intake"]["sla_hours"]
    rows = []
    for r in reqs:
        p = priority(r)
        sub = parse_date(r["submitted_date"])
        first = parse_date(r["first_response_date"])
        hours = business_days(sub, first or AS_OF) * 8
        met = (first is not None) and hours <= sla_hours[p]
        rows.append({**r, "priority": p, "change_class": change_class(r["category"], cfg), "score": score(r),
                     "response_hours": hours, "sla_hours": sla_hours[p], "sla_met": met,
                     "age_days": (AS_OF - sub).days if r["status"] in ("Backlog", "In Progress") else "",
                     "self_serve_candidate": r["category"] in SELF_SERVE})
    by_p = defaultdict(list)
    for r in rows:
        by_p[r["priority"]].append(r)
    sla = [{"priority": p, "requests": len(v), "sla_hours": sla_hours[p], "sla_met_%": pct(sum(x["sla_met"] for x in v), len(v))}
           for p, v in sorted(by_p.items())]
    open_rows = sorted([r for r in rows if r["status"] in ("Backlog", "In Progress")], key=lambda r: (r["priority"], -r["score"]))
    done = [r for r in rows if r["status"] == "Done" and r["completed_date"]]
    cycle = defaultdict(list)
    for r in done:
        cycle[r["change_class"]].append(business_days(parse_date(r["submitted_date"]), parse_date(r["completed_date"])))
    cyc = [{"change_class": k, "done": len(v), "median_business_days": sorted(v)[len(v) // 2]} for k, v in sorted(cycle.items())]
    # Same ask from the same team while an earlier one is still open: merge, don't build twice.
    seen = {}
    for r in sorted(rows, key=lambda r: (r["submitted_date"], r["request_id"])):
        key = (r["category"], r["summary"].strip().lower())
        if r["status"] in ("Backlog", "In Progress"):
            r["duplicate_of"] = seen.get(key, "")
            seen.setdefault(key, r["request_id"])
        else:
            r["duplicate_of"] = ""
    # Priority inversion: P2/P3 work in progress while a P0/P1 request sits untouched in backlog.
    urgent_waiting = any(r["status"] == "Backlog" and r["priority"] in ("P0", "P1") for r in rows)
    inversions = [r for r in rows if urgent_waiting and r["status"] == "In Progress" and r["priority"] in ("P2", "P3")]
    teams = Counter(r["requester_team"] for r in rows)
    insights = {
        "self_serve_share_%": pct(sum(r["self_serve_candidate"] for r in rows), len(rows)),
        "break_fix_share_%": pct(sum(r["category"] in ("Data Fix", "Access / Permissions") for r in rows), len(rows)),
        "top_requesting_team": teams.most_common(1)[0][0] if teams else "",
        "open_backlog": len(open_rows),
        "oldest_open_days": max((r["age_days"] for r in open_rows), default=0),
        "duplicates": [(r["request_id"], r["duplicate_of"]) for r in open_rows if r["duplicate_of"]],
        "inversions": [r["request_id"] for r in inversions],
    }
    return {"rows": rows, "sla": sla, "open": open_rows, "cycle": cyc, "insights": insights}


def main() -> None:
    res = triage()
    print("=== First-response SLA by priority ===")
    print(table(res["sla"]))
    print("\n=== Cycle time by change class (done requests) ===")
    print(table(res["cycle"]))
    print("\n=== Open queue, in work order ===")
    print(table(res["open"][:12], ["request_id", "priority", "change_class", "score", "requester_team", "category", "summary", "age_days", "status"]))
    i = res["insights"]
    print(f"\n=== Insights ===\n- {i['self_serve_share_%']}% of requests are reports or list views: "
          "a self-serve reporting session for the top requesting team removes a chunk of the queue.\n"
          f"- {i['break_fix_share_%']}% are data fixes or access: recurring ones point at a missing automation or validation rule.\n"
          f"- Top requesting team: {i['top_requesting_team']}. Open backlog: {i['open_backlog']}, oldest {i['oldest_open_days']} days.")
    if i["duplicates"]:
        print("- Duplicates to merge: " + ", ".join(f"{a} = {b}" for a, b in i["duplicates"]))
    if i["inversions"]:
        print(f"- Priority inversion: {', '.join(i['inversions'])} in progress while higher-priority requests wait in backlog. "
              "Pause or finish them, then pull from the top of the queue.")
    write_csv("crm_request_queue.csv", res["rows"])


if __name__ == "__main__":
    main()

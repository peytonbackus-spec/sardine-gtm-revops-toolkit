"""Marketing ops report: channel funnel, W-shaped attribution, channel ROI, and campaign hygiene.

Process spec: campaign-operations-spec.md. Inputs (synthetic): campaigns.csv (Salesforce Campaign),
campaign_members.csv (CampaignMember with UTMs), lead_consent.csv, leads.csv, opportunities.csv.

Four questions a marketing leader and the VP of Sales both ask:
  1. Which channels create leads that turn into pipeline?   channel funnel by first-touch campaign type
  2. Which campaigns get credit for pipeline and revenue?   W-shaped attribution (config `marketing_ops.attribution`)
  3. What does a qualified lead or an opportunity cost?     spend / outcomes, by channel
  4. Can we trust the data?                                 hygiene: naming, UTMs, statuses, list-import lag, consent

W-shaped: 30% to the first touch, 30% to the touch that made the lead an MQL (last touch on or before
the MQL date), 30% to the touch that created the opportunity (last touch on or before conversion),
10% spread across every other touch. If two of those are the same touch it gets both shares; with
no "other" touches, the 10% is shared across the key touches. Touches older than `lookback_days`
before the opportunity are ignored.

    python -m gtm_engineer.marketing_ops.campaign_report
"""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import timedelta

from shared_core.config import load_config, parse_date, pct, read_csv, table, to_bool, to_float, write_csv

CASL_IMPLIED_INQUIRY_DAYS = 183   # implied consent from an inquiry lasts six months under CASL
MARKETING_TYPES = {"WBN", "CNT", "PAID", "OUT", "EVT"}


def load() -> dict:
    return {"campaigns": read_csv("campaigns.csv"), "members": read_csv("campaign_members.csv"), "leads": read_csv("leads.csv"),
            "opps": read_csv("opportunities.csv"), "consent": read_csv("lead_consent.csv")}


def touches_by_lead(members: list[dict]) -> dict[str, list[dict]]:
    out = defaultdict(list)
    for m in members:
        out[m["lead_id"]].append(m)
    for v in out.values():
        v.sort(key=lambda m: (m["touch_date"], m["member_id"]))
    return out


def w_shaped(touches: list[dict], mql_date, opp_date) -> dict[str, float]:
    """member_id -> credit share (sums to 1)."""
    if not touches:
        return {}
    first = touches[0]["member_id"]
    def last_on_or_before(d):
        eligible = [t for t in touches if d is None or parse_date(t["touch_date"]) <= d]
        return (eligible[-1] if eligible else touches[0])["member_id"]
    keys = [first, last_on_or_before(mql_date), last_on_or_before(opp_date)]
    credit = defaultdict(float)
    for k in keys:
        credit[k] += 0.30
    others = [t["member_id"] for t in touches if t["member_id"] not in keys]
    if others:
        for o in others:
            credit[o] += 0.10 / len(others)
    else:
        for k in set(keys):
            credit[k] += 0.10 * keys.count(k) / len(keys)
    return dict(credit)


def attribution(data: dict, cfg: dict) -> list[dict]:
    lookback = cfg["marketing_ops"]["attribution"]["lookback_days"]
    camp = {c["campaign_id"]: c for c in data["campaigns"]}
    member_camp = {m["member_id"]: m["campaign_id"] for m in data["members"]}
    by_lead = touches_by_lead(data["members"])
    opp_by_id = {o["opportunity_id"]: o for o in data["opps"]}
    agg = defaultdict(lambda: {"pipeline_$": 0.0, "won_$": 0.0, "sourced_pipeline_$": 0.0, "sourced_opps": 0})
    for lead in data["leads"]:
        o = opp_by_id.get(lead["opportunity_id"])
        if not o:
            continue
        created = parse_date(o["created_date"])
        t = [x for x in by_lead.get(lead["lead_id"], [])
             if created - timedelta(days=lookback) <= parse_date(x["touch_date"]) <= created]
        if not t:
            continue
        amt = to_float(o["amount"])
        won = amt if o["is_won"] == "True" else 0.0
        for mid, share in w_shaped(t, parse_date(lead["mql_date"]), parse_date(lead["converted_date"]) or created).items():
            a = agg[member_camp[mid]]
            a["pipeline_$"] += amt * share
            a["won_$"] += won * share
        first = agg[member_camp[t[0]["member_id"]]]
        first["sourced_pipeline_$"] += amt
        first["sourced_opps"] += 1
    rows = []
    for cid, a in agg.items():
        c = camp[cid]
        rows.append({"campaign_id": cid, "campaign_name": c["campaign_name"], "type": c["type"], "spend_$": int(to_float(c["spend"])),
                     "sourced_opps": a["sourced_opps"], "sourced_pipeline_$": int(a["sourced_pipeline_$"]),
                     "attributed_pipeline_$": int(a["pipeline_$"]), "attributed_won_$": int(a["won_$"])})
    return sorted(rows, key=lambda r: -r["attributed_pipeline_$"])


def channel_funnel(data: dict, cfg: dict, attr: list[dict]) -> list[dict]:
    """By first-touch campaign type: leads, MQL/SQL/opp rates, spend, cost per MQL and per opp, pipeline per $."""
    camp = {c["campaign_id"]: c for c in data["campaigns"]}
    by_lead = touches_by_lead(data["members"])
    labels = {k: v["label"] for k, v in cfg["marketing_ops"]["campaign_types"].items()}
    f = defaultdict(lambda: {"leads": 0, "mql": 0, "sql": 0, "opps": 0})
    for lead in data["leads"]:
        t = by_lead.get(lead["lead_id"])
        if not t:
            continue
        k = camp[t[0]["campaign_id"]]["type"]
        f[k]["leads"] += 1
        f[k]["mql"] += bool(lead["mql_date"])
        f[k]["sql"] += bool(lead["sql_date"])
        f[k]["opps"] += bool(lead["opportunity_id"])
    spend = defaultdict(float)
    for c in data["campaigns"]:
        spend[c["type"]] += to_float(c["spend"])
    pipe = defaultdict(float)
    for a in attr:
        pipe[a["type"]] += a["attributed_pipeline_$"]
    rows = []
    for k, v in f.items():
        s = spend[k]
        rows.append({"channel": labels.get(k, k), "first_touch_leads": v["leads"], "mql_%": pct(v["mql"], v["leads"]),
                     "sql_%": pct(v["sql"], v["leads"]), "opp_%": pct(v["opps"], v["leads"]), "spend_$": int(s),
                     "cost_per_mql_$": int(s / v["mql"]) if v["mql"] and s else "", "cost_per_opp_$": int(s / v["opps"]) if v["opps"] and s else "",
                     "attributed_pipeline_$": int(pipe[k]), "pipeline_per_$": round(pipe[k] / s, 1) if s else "n/a (no spend)"})
    return sorted(rows, key=lambda r: -r["attributed_pipeline_$"])


def hygiene(data: dict, cfg: dict) -> list[dict]:
    mo = cfg["marketing_ops"]
    pattern = re.compile(mo["campaign_name_pattern"])
    camp = {c["campaign_id"]: c for c in data["campaigns"]}
    leads = {lead["lead_id"]: lead for lead in data["leads"]}
    issues = []

    def add(rule, record, detail):
        issues.append({"rule": rule, "record": record, "detail": detail})

    for c in data["campaigns"]:
        if not pattern.match(c["campaign_name"]):
            add("M01 Campaign name breaks convention", c["campaign_id"], c["campaign_name"])
    for m in data["members"]:
        if m["utm_source"] not in mo["utm"]["source"] or m["utm_medium"] not in mo["utm"]["medium"]:
            add("M02 UTM value outside taxonomy", m["member_id"], f"{m['utm_source']} / {m['utm_medium']}")
        if m["status"] not in mo["campaign_types"][camp[m["campaign_id"]]["type"]]["statuses"]:
            add("M03 Member status not valid for campaign type", m["member_id"], m["status"])
    first_lead = {}
    for m in data["members"]:
        first_lead.setdefault(m["campaign_id"], m["touch_date"])
        first_lead[m["campaign_id"]] = min(first_lead[m["campaign_id"]], m["touch_date"])
    sla_days = mo["list_import_sla_hours"] / 24
    for c in data["campaigns"]:
        if c["type"] in ("EVT", "WBN") and c["end_date"] and c["campaign_id"] in first_lead:
            lag = (parse_date(first_lead[c["campaign_id"]]) - parse_date(c["end_date"])).days
            if lag > sla_days:
                add("M04 List imported late", c["campaign_id"], f"{lag} days after the event (SLA {mo['list_import_sla_hours']}h)")
    touched = touches_by_lead(data["members"])
    opt_in_regions = set(mo["consent"]["regions_opt_in_required"])
    for cns in data["consent"]:
        lead = leads.get(cns["lead_id"])
        if not lead:
            continue
        mkt = [t for t in touched.get(cns["lead_id"], [])[1:] if camp[t["campaign_id"]]["type"] in MARKETING_TYPES]
        if not mkt:
            continue
        if cns["region"] in opt_in_regions and cns["consent_type"] == "none":
            add("M05 Marketed without lawful basis (GDPR)", cns["lead_id"], f"{len(mkt)} marketing touches, no consent recorded")
        if cns["country"] == "CA":
            if cns["consent_type"] == "none":
                add("M06 Marketed without CASL consent", cns["lead_id"], f"{len(mkt)} marketing touches")
            elif cns["consent_type"] == "implied_inquiry":
                expiry = parse_date(cns["consent_date"]) + timedelta(days=CASL_IMPLIED_INQUIRY_DAYS)
                late = [t for t in mkt if parse_date(t["touch_date"]) > expiry]
                if late:
                    add("M07 CASL implied consent expired", cns["lead_id"], f"{len(late)} touches after {expiry.isoformat()}")
        if to_bool(cns["email_opt_out"]) and any(camp[t["campaign_id"]]["type"] in ("OUT", "WBN", "CNT") for t in mkt):
            add("M08 Touched after opt-out (check send logs)", cns["lead_id"], "opted out; email-type campaign membership exists")
    no_campaign = [lead for lead in data["leads"] if lead["lead_id"] not in touched]
    if no_campaign:
        add("M09 Leads with no campaign attribution", f"{len(no_campaign)} leads", "lead source set but no Campaign Member")
    return issues


def run(data: dict | None = None, cfg: dict | None = None) -> dict:
    cfg, data = cfg or load_config(), data or load()
    attr = attribution(data, cfg)
    return {"attribution": attr, "funnel": channel_funnel(data, cfg, attr), "hygiene": hygiene(data, cfg)}


def main() -> None:
    res = run()
    print("=== 1. Channel funnel (first touch) and ROI ===")
    print(table(res["funnel"]))
    print("\n=== 2. Top campaigns by W-shaped attributed pipeline ===")
    print(table(res["attribution"][:10], ["campaign_name", "type", "spend_$", "sourced_opps", "sourced_pipeline_$",
                                           "attributed_pipeline_$", "attributed_won_$"]))
    counts = defaultdict(int)
    for i in res["hygiene"]:
        counts[i["rule"]] += 1
    print(f"\n=== 3. Data hygiene ({len(res['hygiene'])} issues) ===")
    print(table([{"rule": k, "issues": v} for k, v in sorted(counts.items())]))
    print("\nConsent rules (M05-M08) go to Marketing Ops and Legal the same day; naming/UTM rules (M01-M03) to the campaign owner.")
    write_csv("campaign_attribution.csv", res["attribution"])
    write_csv("channel_funnel.csv", res["funnel"])
    write_csv("marketing_hygiene.csv", res["hygiene"])


if __name__ == "__main__":
    main()

"""Deal-risk detection + AI forecast commentary.

Role scope (GTM Strategy & Ops): production AI workflows for deal-risk detection,
forecast commentary and renewal signals, integrated with the CRM and forecasting
tool, with workflow impact measured on forecast accuracy and seller capacity.

Two layers, deliberately:
  1. Deterministic risk signals (explainable, testable, no model needed). These
     decide the score. A model never decides whether a deal is at risk.
  2. AI commentary on top: turns the signals into a two-line note per deal and a
     region-level forecast summary for the forecast call. The model explains;
     the rules decide.

Long-cycle enterprise deals stall in technical validation (POC / data test) and
security review, so both are first-class signals. Adjust risk_signals() to the
stages where the company's deals actually stall.

    python -m gtm_strategy_ops.ai_deal_risk.deal_risk
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from shared_core.ai_governance.hitl import HITLPolicy, write_queue
from shared_core.ai_governance.llm_client import LLMClient, load_prompt
from shared_core.config import AS_OF, fiscal_quarter, load_config, parse_date, read_csv, table, to_float

PROMPTS = Path(__file__).parent / "prompts"
DEAL_KEYS = ["risk_summary", "recommended_action", "forecast_category_suggestion", "evidence", "confidence"]
REGION_KEYS = ["headline", "commit_assessment", "top_risks", "asks_for_leadership"]


def risk_signals(opp: dict, cfg: dict) -> list[tuple[str, int]]:
    stages = [s["name"] for s in cfg["opportunity"]["stages"]]
    limits = {s["name"]: s["max_days"] for s in cfg["opportunity"]["stages"]}
    idx = stages.index(opp["stage"]) if opp["stage"] in stages else 0
    sig = []
    days_in_stage = (AS_OF - parse_date(opp["stage_entered_date"])).days
    if limits.get(opp["stage"]) and days_in_stage > limits[opp["stage"]]:
        sig.append((f"{days_in_stage}d in stage (limit {limits[opp['stage']]})", 25))
    idle = (AS_OF - parse_date(opp["last_activity_date"])).days
    if idle > 30:
        sig.append((f"No activity in {idle}d", 30))
    elif idle > 14:
        sig.append((f"No activity in {idle}d", 20))
    if int(opp.get("contacts_engaged") or 0) < 3:
        sig.append((f"Single-threaded ({opp.get('contacts_engaged')} contacts)", 15))
    if idx >= 2 and opp.get("economic_buyer_engaged") != "True":
        sig.append(("No economic buyer engaged at stage 3+", 20))
    if parse_date(opp["close_date"]) < AS_OF:
        sig.append(("Close date in the past", 25))
    if not opp.get("next_step"):
        sig.append(("No next step", 10))
    if idx >= 3 and opp.get("poc_status") in ("Not Started", "Failed", "In Progress"):
        sig.append((f"Technical validation {opp.get('poc_status', '').lower()} at stage 4+", 15))
    if idx >= 3 and opp.get("security_review") == "Not Started":
        sig.append(("Security review not started at stage 4+", 15))
    if opp.get("forecast_category") == "Commit" and idx <= 2:
        sig.append(("Commit before business case", 10))
    return sig


def score(opp: dict, cfg: dict) -> dict:
    sig = risk_signals(opp, cfg)
    pts = min(100, sum(p for _, p in sig))
    level = "HIGH" if pts >= 50 else "MEDIUM" if pts >= 25 else "LOW"
    return {**opp, "risk_points": pts, "risk_level": level, "risk_reasons": "; ".join(s for s, _ in sig)}


def mock_deal_commentary(rec: dict) -> dict:
    reasons = [r for r in str(rec.get("notes", "")).split("; ") if r]
    top = reasons[:2] or ["No material risk signals"]
    fc = rec.get("forecast_category")
    suggestion = fc
    if fc == "Commit" and len(reasons) >= 3:
        suggestion = "Best Case"
    action = ("Book exec-sponsor call this week and set a dated next step" if any("economic buyer" in r for r in reasons)
              else "Re-confirm timeline and security-review start date" if any("Security" in r or "Close date" in r for r in reasons)
              else "Re-engage: multi-thread to a second persona" if reasons else "Keep current plan")
    return {"risk_summary": f"{rec.get('account_name')}: " + "; ".join(top) + ".",
            "recommended_action": action, "forecast_category_suggestion": suggestion,
            "evidence": [{"signal": r, "source_field": "risk_signals"} for r in reasons],
            "confidence": 0.9 if reasons else 0.95}


def mock_region_commentary(rec: dict) -> dict:
    commit, quota = to_float(rec["commit"]), to_float(rec["quota"])
    n = int(rec["high_risk_count"])
    deals = [d for d in str(rec.get("top_deals", "")).split(" | ") if d]
    if commit and to_float(rec["high_risk_commit"]) > 0.25 * commit:
        assessment = "At risk"
    elif commit < 0.7 * quota:
        assessment = "Short of quota"
    else:
        assessment = "Supportable"
    ask = ("Exec-sponsor coverage and a security-review escalation path for the deals listed" if deals
           else "No escalations this week")
    if assessment == "Short of quota":
        ask += f"; a plan to close the ${quota - commit:,.0f} gap from Best Case"
    return {"headline": f"{rec['region']} {rec['quarter']}: commit ${commit:,.0f} vs quota ${quota:,.0f}; "
                        f"{n} high-risk deal{'s' if n != 1 else ''} carrying ${to_float(rec['high_risk_amount']):,.0f}.",
            "commit_assessment": assessment, "top_risks": deals[:3], "asks_for_leadership": ask + "."}


def evaluate_deal(opp: dict, cfg: dict | None = None, client: LLMClient | None = None) -> dict:
    """Score one deal and get its commentary. Used by the eval harness and by on-demand checks."""
    cfg, client = cfg or load_config(), client or LLMClient()
    scored = score(opp, cfg)
    pid, system = load_prompt(PROMPTS / "deal_risk_commentary.md")
    rec = {k: scored.get(k) for k in ("account_name", "stage", "amount", "forecast_category", "close_date", "region")}
    rec["notes"] = scored["risk_reasons"]
    out = client.complete_json(prompt_id=pid, system=system, record=rec, required_keys=DEAL_KEYS,
                               mock_responder=mock_deal_commentary, task="Write deal-risk commentary.")
    return {"risk_level": scored["risk_level"], "risk_points": scored["risk_points"], **out}


def run(cfg: dict | None = None, client: LLMClient | None = None) -> dict:
    cfg, client = cfg or load_config(), client or LLMClient()
    q = cfg["current_fiscal_quarter"]
    opps = [score(o, cfg) for o in read_csv("opportunities.csv") if o["is_closed"] != "True"]
    deal_pid, deal_sys = load_prompt(PROMPTS / "deal_risk_commentary.md")
    reg_pid, reg_sys = load_prompt(PROMPTS / "forecast_commentary.md")
    policy, queue = HITLPolicy(), []
    for o in opps:
        if o["risk_level"] == "LOW":
            continue
        rec = {k: o[k] for k in ("account_name", "stage", "amount", "forecast_category", "close_date", "region")}
        rec["notes"] = o["risk_reasons"]
        out = client.complete_json(prompt_id=deal_pid, system=deal_sys, record=rec, required_keys=DEAL_KEYS,
                                   mock_responder=mock_deal_commentary, task="Write deal-risk commentary.")
        o.update({"ai_summary": out["risk_summary"], "ai_action": out["recommended_action"],
                  "ai_category_suggestion": out["forecast_category_suggestion"]})
        action = "change_forecast_category" if out["forecast_category_suggestion"] != o["forecast_category"] else "flag_deal_risk"
        queue.append({"opportunity_id": o["opportunity_id"], "account_name": o["account_name"], "owner": o["owner"],
                      "amount": o["amount"], "risk_level": o["risk_level"], "risk_reasons": o["risk_reasons"],
                      "ai_action": out["recommended_action"], "current_category": o["forecast_category"],
                      "suggested_category": out["forecast_category_suggestion"], "action": action,
                      "decision": policy.decide(action, out["confidence"], to_float(o["amount"]))})
    regions = []
    for region, quota in cfg["quota"][q].items():
        in_q = [o for o in opps if o["region"] == region and fiscal_quarter(parse_date(o["close_date"])) == q]
        high = sorted([o for o in in_q if o["risk_level"] == "HIGH"], key=lambda o: -to_float(o["amount"]))
        rec = {"region": region, "quarter": q, "quota": quota,
               "commit": sum(to_float(o["amount"]) for o in in_q if o["forecast_category"] == "Commit"),
               "high_risk_count": len(high), "high_risk_amount": sum(to_float(o["amount"]) for o in high),
               "high_risk_commit": sum(to_float(o["amount"]) for o in high if o["forecast_category"] == "Commit"),
               "top_deals": " | ".join(f"{o['account_name']} ${to_float(o['amount']):,.0f}: {o['risk_reasons'].split('; ')[0]}" for o in high[:3])}
        out = client.complete_json(prompt_id=reg_pid, system=reg_sys, record=rec,
                                   required_keys=REGION_KEYS, mock_responder=mock_region_commentary,
                                   task="Write the region forecast commentary.")
        regions.append({"region": region, **out})
    return {"opps": opps, "queue": queue, "regions": regions}


def main() -> None:
    res = run()
    lvl = defaultdict(lambda: [0, 0.0])
    for o in res["opps"]:
        lvl[o["risk_level"]][0] += 1
        lvl[o["risk_level"]][1] += to_float(o["amount"])
    print("=== Open pipeline by risk level ===")
    print(table([{"risk_level": k, "opps": v[0], "amount_$": int(v[1])} for k, v in sorted(lvl.items())]))
    print("\n=== Deal-risk review queue (category changes first, then by amount) ===")
    top = sorted(res["queue"], key=lambda r: (r["action"] != "change_forecast_category", -to_float(r["amount"])))[:10]
    print(table(top, ["opportunity_id", "account_name", "amount", "risk_level", "current_category", "suggested_category", "decision"]))
    print("\n=== AI forecast commentary by region ===")
    for r in res["regions"]:
        print(f"\n[{r['region']}] {r['headline']}\n  Commit: {r['commit_assessment']}\n  Risks: {r['top_risks']}\n  Ask: {r['asks_for_leadership']}")
    print(f"\nQueue -> {write_queue('deal_risk', res['queue'])}")


if __name__ == "__main__":
    main()

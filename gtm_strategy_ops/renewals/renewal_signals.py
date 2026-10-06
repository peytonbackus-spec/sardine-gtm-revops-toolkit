"""Renewal health, risk and expansion signals, plus AI renewal briefs.

Role scope (GTM Strategy & Ops): AI workflows for renewal signals, renewal
processes, closed-lost and churn insights, and retention reporting.

Why usage trend carries the highest weight in the example config: in most
subscription businesses, declining usage precedes non-renewal by a quarter or two.
Re-weight renewals.health_weights in config to match what predicts churn for the
company (calibrate on its own history).

  Health (0-100) = weighted: volume trend, utilization, support, exec sponsor, competitive
  Band           = Healthy / Watch / At Risk
  Expansion flag = utilization > 110% (overage) or single product line (cross-sell)

    python -m gtm_strategy_ops.renewals.renewal_signals
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from shared_core.ai_governance.hitl import HITLPolicy, write_queue
from shared_core.ai_governance.llm_client import LLMClient
from shared_core.config import AS_OF, load_config, parse_date, read_csv, table, to_bool, to_float

PROMPT_ID = "renewal_brief@1.0.0"
SYSTEM = (Path(__file__).parent / "renewal-process.md").read_text(encoding="utf-8")[:2000]
EXPECTED_CHURN = {"Healthy": 0.03, "Watch": 0.12, "At Risk": 0.35}  # [ASSUME] calibrate on the company's history


def components(r: dict) -> dict:
    trend = to_float(r["volume_trend_90d_pct"])
    util = to_float(r["utilization_pct"])
    return {
        "volume_trend": max(0.0, min(1.0, (trend + 30) / 60)),            # -30% -> 0, +30% -> 1
        "utilization": 1.0 if util >= 90 else max(0.0, (util - 40) / 50),  # <40% committed volume used -> 0
        "support": max(0.0, 1 - 0.35 * int(r["sev1_tickets_90d"])),
        "sponsor": 1.0 if to_bool(r["exec_sponsor_active"]) else 0.0,
        "competitive": 0.0 if to_bool(r["competitor_signal"]) else 1.0,
    }


def health(r: dict, cfg: dict) -> dict:
    w = cfg["renewals"]["health_weights"]
    c = components(r)
    score = round(100 * sum(c[k] * w[k] for k in w))
    band = "Healthy" if score >= 70 else "Watch" if score >= 50 else "At Risk"
    drivers = [k for k, v in sorted(c.items(), key=lambda kv: kv[1]) if v < 0.5][:3]
    owned = [p for p in r["products_owned"].split(";") if p]
    util = to_float(r["utilization_pct"])
    if band == "At Risk":
        expansion = ""  # save the account before selling it more
    elif util > 110:
        expansion = "Overage: committed volume exceeded"
    elif len(owned) == 1 and cfg["segments"].get(r["segment"], {}).get("core_segment"):
        other = cfg["product_lines"]["cross_sell"].get(owned[0])
        expansion = f"Cross-sell {cfg['product_lines'][other]['label']}" if other else ""
    else:
        expansion = ""
    return {**r, "health": score, "band": band, "risk_drivers": ", ".join(drivers), "expansion_signal": expansion,
            "days_to_renewal": (parse_date(r["renewal_date"]) - AS_OF).days,
            "expected_churn_$": int(to_float(r["arr"]) * EXPECTED_CHURN[band])}


def mock_brief(rec: dict) -> dict:
    drivers = rec.get("notes", "")
    plays = {"volume_trend": "Usage review: map the usage decline to its cause (seats, channel, product) before pricing talks",
             "utilization": "Right-size the commit or run an adoption plan; don't let shelfware reach procurement",
             "support": "Close Sev-1s and bring a support exec to the renewal kickoff",
             "sponsor": "Re-establish an exec sponsor: map the org, then a QBR invite from your leadership",
             "competitive": "Run a value review with quantified outcomes before a competitor bake-off starts"}
    first = drivers.split(", ")[0] if drivers else ""
    return {"situation": f"{rec.get('account_name')} renews {rec.get('product_line')} (${to_float(rec.get('arr')):,.0f} ARR) "
                         f"on {rec.get('renewal_date')}; health drivers below threshold: {drivers or 'none'}.",
            "recommended_play": plays.get(first, "Standard renewal motion"),
            "escalate": rec.get("band") == "At Risk", "confidence": 0.88}


def main() -> None:
    cfg = load_config()
    horizon = cfg["renewals"]["lookahead_days"]
    rows = [health(r, cfg) for r in read_csv("renewals.csv")]
    upcoming = sorted([r for r in rows if r["days_to_renewal"] <= horizon], key=lambda r: r["health"])
    print(f"=== Renewals in next {horizon} days: {len(upcoming)} ===\n")
    by = defaultdict(lambda: defaultdict(float))
    for r in upcoming:
        by[r["product_line"]][r["band"]] += to_float(r["arr"])
        by[r["product_line"]]["expected_churn"] += r["expected_churn_$"]
        by[r["product_line"]]["total"] += to_float(r["arr"])
    print("ARR by product line and health band:")
    print(table([{"product_line": pl, "renewing_arr": int(v["total"]), "healthy": int(v["Healthy"]), "watch": int(v["Watch"]),
                  "at_risk": int(v["At Risk"]), "expected_churn_$": int(v["expected_churn"]),
                  "forecast_GRR_%": round(100 * (1 - v["expected_churn"] / v["total"]), 1) if v["total"] else ""}
                 for pl, v in sorted(by.items())]))
    print("\nLowest-health renewals:")
    print(table(upcoming[:10], ["account_name", "product_line", "arr", "renewal_date", "days_to_renewal", "health", "band", "risk_drivers"]))
    exp = [r for r in rows if r["expansion_signal"]]
    print(f"\nExpansion signals on healthy/watch accounts: {len(exp)} (feeds the Expansion opportunity type)")
    print(table(sorted(exp, key=lambda r: -to_float(r["arr"]))[:5], ["account_name", "product_line", "arr", "band", "expansion_signal"]))
    overdue = [r for r in upcoming if r["days_to_renewal"] < 0]
    if overdue:
        print(f"\nOverdue (renewal date passed, not closed): {len(overdue)}. Data-quality and commercial issue.")

    client, policy, queue = LLMClient(), HITLPolicy(), []
    for r in [r for r in upcoming if r["band"] != "Healthy"]:
        rec = {k: r[k] for k in ("account_name", "product_line", "arr", "renewal_date")}
        rec.update({"notes": r["risk_drivers"], "band": r["band"]})
        out = client.complete_json(prompt_id=PROMPT_ID, system=SYSTEM, record=rec,
                                   required_keys=["situation", "recommended_play", "escalate", "confidence"],
                                   mock_responder=lambda _clean, rec=rec: mock_brief(rec), task="Write the renewal brief.")
        action = "escalate_renewal" if out["escalate"] else "renewal_play"
        queue.append({"account_name": r["account_name"], "product_line": r["product_line"], "arr": r["arr"], "band": r["band"],
                      "play": out["recommended_play"], "action": action,
                      "decision": policy.decide(action, out["confidence"], to_float(r["arr"]))})
    print(f"\nRenewal brief queue -> {write_queue('renewals', queue)}")


if __name__ == "__main__":
    main()

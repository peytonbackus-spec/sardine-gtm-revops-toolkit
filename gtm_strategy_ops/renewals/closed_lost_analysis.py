"""Closed-lost insight report: why we lose, to whom, and where.

Role scope (GTM Strategy & Ops): capture closed-lost and churn insights for
actionable analysis.

A loss reason picklist is only worth having if someone acts on it. This turns
loss reasons into the three cuts that go to Product, Marketing and Sales
leadership, and states the action each one implies.

    python -m gtm_strategy_ops.renewals.closed_lost_analysis
"""
from __future__ import annotations

from collections import Counter, defaultdict

from shared_core.config import pct, read_csv, table, to_float

ACTION = {  # who owns the fix for each loss reason
    "Price": "Sales leadership: discount guardrails + value-selling (quantified ROI)",
    "Lost to Competitor": "Product Marketing: battlecard refresh for the named competitor",
    "No Decision / Status Quo": "Sales: earlier economic-buyer access; quantify cost of inaction",
    "Build In-House": "Product: build-vs-buy TCO asset; data and integration advantage",
    "Security / Compliance Blocker": "Security team: pre-built security package, SOC report on request",
    "Integration Effort": "Solutions Eng: reference architectures per core provider / partner",
    "Timing / Budget": "Marketing: nurture track and recycle at budget cycle",
    "Champion Left": "Sales ops: multi-threading standard (3+ personas by stage 3)",
    "(missing)": "RevOps: data-quality fix (rule O03)",
}


def summarize(opps: list[dict]) -> dict:
    lost = [o for o in opps if o["stage"] == "Closed Lost"]
    by_reason = defaultdict(lambda: [0, 0.0])
    for o in lost:
        k = o["closed_lost_reason"] or "(missing)"
        by_reason[k][0] += 1
        by_reason[k][1] += to_float(o["amount"])
    total_amt = sum(v[1] for v in by_reason.values())
    reasons = sorted(({"reason": k, "deals": n, "lost_$": int(a), "share_$_%": pct(a, total_amt), "owner_action": ACTION.get(k, "")}
                      for k, (n, a) in by_reason.items()), key=lambda r: -r["lost_$"])
    by_prod = [{"product_line": pl, **{r: c for r, c in Counter((o["closed_lost_reason"] or "(missing)") for o in lost if o["product_line"] == pl).most_common(3)}}
               for pl in sorted({o["product_line"] for o in lost})]
    comp = Counter(o["competitor"] for o in lost if o["closed_lost_reason"] == "Lost to Competitor")
    return {"lost": len(lost), "reasons": reasons, "by_product": by_prod,
            "competitors": [{"competitor": c, "losses": n} for c, n in comp.most_common()]}


def main() -> None:
    s = summarize(read_csv("opportunities.csv"))
    print(f"=== Closed-lost analysis: {s['lost']} lost deals ===\n")
    print(table(s["reasons"]))
    print("\nTop 3 loss reasons by product line:")
    for row in s["by_product"]:
        print(f"  {row.pop('product_line')}: {row}")
    print("\nLosses to competitors:")
    print(table(s["competitors"]))


if __name__ == "__main__":
    main()

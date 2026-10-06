"""Calibrate lead scoring against conversion outcomes.

Role scope (GTM Engineer): cohort and trend analysis on lead-scoring and routing
performance, and continuous scoring improvement using conversion outcomes.

A score is only good if higher scores convert better. This script checks that on
closed-out leads (old enough to have an outcome) and reports:

  1. Conversion by grade: does A1 really beat B2 beats C3?
  2. Lift by fit component: which segments and personas over- or under-perform
     the points the config gives them? This is where weight changes come from.
  3. Monotonicity check: a pass/fail you can put in a weekly report.

    python -m gtm_engineer.lead_scoring.calibrate_scoring
"""
from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

from gtm_engineer.lead_scoring.score_leads import score_all
from shared_core.config import AS_OF, load_config, parse_date, pct, read_csv, table

MATURITY_DAYS = 45  # leads younger than this haven't had time to convert


def matured(leads: list[dict]) -> list[dict]:
    cutoff = AS_OF - timedelta(days=MATURITY_DAYS)
    return [l for l in leads if (parse_date(l["created_date"]) or AS_OF) <= cutoff]


def converted(l: dict) -> bool:
    return l["status"] == "Converted"


def conversion_by(rows: list[dict], key) -> list[dict]:
    buckets = defaultdict(lambda: [0, 0])
    for r in rows:
        k = key(r)
        buckets[k][0] += 1
        buckets[k][1] += converted(r)
    base = pct(sum(b[1] for b in buckets.values()), sum(b[0] for b in buckets.values()))
    out = []
    for k, (n, c) in sorted(buckets.items(), key=lambda kv: str(kv[0])):
        rate = pct(c, n)
        out.append({"bucket": k, "leads": n, "converted": c, "conv_%": rate, "lift": round(rate / base, 2) if base else 0})
    return out


def is_monotonic(by_letter: list[dict]) -> bool:
    rates = [r["conv_%"] for r in sorted(by_letter, key=lambda r: r["bucket"]) if r["leads"] >= 10]
    return all(a >= b for a, b in zip(rates, rates[1:]))


def weight_suggestions(by_segment: list[dict], cfg: dict) -> list[dict]:
    """Compare observed lift to configured points: flag segments the model is mis-weighting."""
    seg_cfg = cfg["segments"]
    max_pts = max(s["icp_points"] for s in seg_cfg.values()) or 1
    out = []
    for row in by_segment:
        if row["leads"] < 15 or row["bucket"] not in seg_cfg:
            continue
        configured = seg_cfg[row["bucket"]]["icp_points"]
        implied = round(min(max_pts, max_pts * row["lift"] / 1.6))  # lift ~1.6 maps to max points
        if abs(implied - configured) >= 5:
            out.append({"segment": row["bucket"], "configured_pts": configured, "observed_lift": row["lift"],
                        "suggested_pts": implied, "action": "raise" if implied > configured else "lower"})
    return out


def main() -> None:
    cfg = load_config()
    rows = matured(score_all(read_csv("leads.csv"), cfg, point_in_time_days=7))
    print(f"=== Scoring calibration on {len(rows)} matured leads (created > {MATURITY_DAYS} days ago) ===\n")
    by_letter = conversion_by(rows, lambda r: r["grade"][0])
    print("Conversion by FIT letter:")
    print(table(by_letter))
    print("\nConversion by INTENT number:")
    print(table(conversion_by(rows, lambda r: r["grade"][1])))
    print(f"\nMonotonic (A >= B >= C >= D): {'PASS' if is_monotonic(by_letter) else 'FAIL, investigate weights'}")
    by_seg = conversion_by(rows, lambda r: r["segment"])
    print("\nConversion by segment:")
    print(table(by_seg))
    sugg = weight_suggestions(by_seg, cfg)
    print("\nSuggested segment weight changes (review with Marketing + SDR leadership before applying):")
    print(table(sugg) if sugg else "  none: configured weights are consistent with observed lift")


if __name__ == "__main__":
    main()

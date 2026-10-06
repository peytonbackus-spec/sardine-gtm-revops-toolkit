"""Forecast accuracy, bias and commit-call reliability by region.

Role scope (GTM Strategy & Ops): manage forecasting cadence, categories and accuracy
measurement, and measure workflow impact on forecast accuracy.

Reads weekly forecasting-tool-style snapshots (commit / best case / pipeline per region)
and the actual closed-won for each quarter, then answers the three questions a
CRO asks about the forecast:

  1. How accurate is the commit call at week 4, 8 and 12 of the quarter?
  2. Is the error random or biased? (EMEA over-calls / NA sandbags...)
  3. What bias-correction should be applied to this quarter's calls?

    python -m gtm_strategy_ops.forecasting.forecast_accuracy
"""
from __future__ import annotations

from collections import defaultdict
from statistics import mean

from shared_core.config import read_csv, table, to_float

CHECKPOINT_WEEKS = (4, 8, 12)


def accuracy(commit: float, actual: float) -> float | None:
    if actual <= 0:
        return None
    return round(max(0.0, 1 - abs(commit - actual) / actual) * 100, 1)


def bias(commit: float, actual: float) -> float | None:
    return round((commit - actual) / actual * 100, 1) if actual > 0 else None


def checkpoint_table(snaps: list[dict]) -> list[dict]:
    rows = []
    for s in snaps:
        wk = int(s["week"])
        if wk not in CHECKPOINT_WEEKS:
            continue
        c, a = to_float(s["commit"]), to_float(s["actual_closed_won"])
        rows.append({"quarter": s["quarter"], "region": s["region"], "week": wk, "commit": int(c), "actual": int(a),
                     "accuracy_%": accuracy(c, a), "bias_%": bias(c, a)})
    return rows


def region_summary(rows: list[dict]) -> list[dict]:
    by_region = defaultdict(list)
    for r in rows:
        if r["accuracy_%"] is not None:
            by_region[r["region"]].append(r)
    out = []
    for region, rs in sorted(by_region.items()):
        wk8 = [r for r in rs if r["week"] == 8]
        avg_bias = mean(r["bias_%"] for r in wk8) if wk8 else 0
        out.append({"region": region, "quarters": len({r["quarter"] for r in rs}),
                    "acc_wk4_%": round(mean(r["accuracy_%"] for r in rs if r["week"] == 4), 1),
                    "acc_wk8_%": round(mean(r["accuracy_%"] for r in wk8), 1) if wk8 else "",
                    "acc_wk12_%": round(mean(r["accuracy_%"] for r in rs if r["week"] == 12), 1),
                    "avg_bias_wk8_%": round(avg_bias, 1),
                    "pattern": "over-calls" if avg_bias > 5 else ("sandbags" if avg_bias < -5 else "balanced"),
                    "suggested_adjustment": round(1 / (1 + avg_bias / 100), 2) if wk8 else 1.0})
    return out


def main() -> None:
    rows = checkpoint_table(read_csv("forecast_snapshots.csv"))
    print("=== Commit accuracy at week 4 / 8 / 12 (by quarter and region) ===")
    print(table(rows))
    summary = region_summary(rows)
    print("\n=== Region summary: is the error random or biased? ===")
    print(table(summary))
    print("\nHow to use: multiply a region's current-quarter commit by `suggested_adjustment` for the CRO roll-up "
          "view, and raise the bias with that region's leader. The goal is to coach it out of the call, "
          "not to adjust it forever.")


if __name__ == "__main__":
    main()

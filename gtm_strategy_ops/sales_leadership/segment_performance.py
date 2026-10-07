"""Where we win and where we don't: performance by industry segment (and any other dimension).

The VP question: "Which industries are we doing really well in, and which are we not?"

For each segment over the trailing window (config `sales_leadership.trailing_days`):
  win rate (count and $) with an 80% confidence range, average won deal, median cycle,
  sales velocity ($ per day), open pipeline, top loss reason and top competitor lost to.

Verdicts compare the segment to the company win rate, and refuse to judge small samples:
  Double down   win rate >= company + gap, and the low end of its range is above company
  Fix           win rate <= company - gap, and the high end of its range is below company
  Watch         outside the gap but the range still overlaps the company rate (could be noise)
  Hold          within the gap
  Too early     fewer than `min_sample` closed deals: do not move headcount on this yet

Why the range: with 7 closed deals, a 43% win rate is anywhere from about 20% to 68% at 80%
confidence. Leaders re-allocate territories on these numbers, so the report says how sure it is.

    python -m gtm_strategy_ops.sales_leadership.segment_performance
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict
from datetime import timedelta
from statistics import median

from shared_core.config import AS_OF, load_config, parse_date, pct, read_csv, table, to_float, write_csv

Z80 = 1.2816


def wilson(won: int, n: int, z: float = Z80) -> tuple[float, float]:
    """Wilson score interval for a win rate, in percent."""
    if n == 0:
        return 0.0, 0.0
    p = won / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return round(100 * max(0.0, centre - half), 1), round(100 * min(1.0, centre + half), 1)


def closed_in_window(opps: list[dict], days: int, as_of=AS_OF) -> list[dict]:
    start = as_of - timedelta(days=days)
    return [o for o in opps if o["is_closed"] == "True" and start <= parse_date(o["close_date"]) < as_of]


def velocity(n_opps: int, win_rate_pct: float, avg_deal: float, cycle_days: float) -> float:
    """Sales velocity: (opportunities x win rate x average deal) / cycle length, in $ per day."""
    return round(n_opps * (win_rate_pct / 100) * avg_deal / cycle_days, 0) if cycle_days else 0.0


def performance_by(opps: list[dict], dim: str, cfg: dict, label=None) -> list[dict]:
    sl = cfg["sales_leadership"]
    closed = closed_in_window(opps, sl["trailing_days"])
    co_won = sum(1 for o in closed if o["is_won"] == "True")
    co_rate = pct(co_won, len(closed))
    groups = defaultdict(list)
    for o in closed:
        groups[o[dim] or "(blank)"].append(o)
    open_pipe = defaultdict(float)
    for o in opps:
        if o["is_closed"] != "True":
            open_pipe[o[dim] or "(blank)"] += to_float(o["amount"])
    rows = []
    for key in sorted(set(groups) | set(open_pipe)):
        g = groups.get(key, [])
        won = [o for o in g if o["is_won"] == "True"]
        lost = [o for o in g if o["is_won"] != "True"]
        rate = pct(len(won), len(g))
        lo, hi = wilson(len(won), len(g))
        avg_won = sum(to_float(o["amount"]) for o in won) / len(won) if won else 0.0
        cyc = median([(parse_date(o["close_date"]) - parse_date(o["created_date"])).days for o in won]) if won else 0
        reasons = Counter(o["closed_lost_reason"] for o in lost if o["closed_lost_reason"])
        comps = Counter(o["competitor"] for o in lost if o["competitor"] not in sl["all_hands"]["competitor_none_values"])
        verdict = verdict_for(len(g), rate, lo, hi, co_rate, sl)
        rows.append({dim: label(key) if label else key, "closed": len(g), "won": len(won), "win_rate_%": rate,
                     "range_80%": f"{lo}-{hi}", "vs_company_pts": round(rate - co_rate, 1) if g else "",
                     "avg_won_$": int(avg_won), "median_cycle_days": int(cyc) if won else "",
                     "velocity_$_per_day": velocity(len(g), rate, avg_won, cyc),
                     "open_pipeline_$": int(open_pipe.get(key, 0)),
                     "top_loss_reason": reasons.most_common(1)[0][0] if reasons else "",
                     "top_competitor_lost_to": comps.most_common(1)[0][0] if comps else "", "verdict": verdict})
    order = {"Double down": 0, "Fix": 1, "Watch": 2, "Hold": 3, "Too early": 4}
    return sorted(rows, key=lambda r: (order[r["verdict"]], -r["closed"]))


def verdict_for(n: int, rate: float, lo: float, hi: float, company: float, sl: dict) -> str:
    if n < sl["min_sample"]:
        return "Too early"
    gap = sl["segment_gap_pts"]
    if rate >= company + gap:
        return "Double down" if lo > company else "Watch"
    if rate <= company - gap:
        return "Fix" if hi < company else "Watch"
    return "Hold"


def company_baseline(opps: list[dict], cfg: dict) -> dict:
    closed = closed_in_window(opps, cfg["sales_leadership"]["trailing_days"])
    won = [o for o in closed if o["is_won"] == "True"]
    avg = sum(to_float(o["amount"]) for o in won) / len(won) if won else 0.0
    cyc = median([(parse_date(o["close_date"]) - parse_date(o["created_date"])).days for o in won]) if won else 0
    rate = pct(len(won), len(closed))
    return {"closed": len(closed), "won": len(won), "win_rate_%": rate, "avg_won_$": int(avg),
            "median_cycle_days": int(cyc), "velocity_$_per_day": velocity(len(closed), rate, avg, cyc)}


def headline(rows: list[dict], dim: str, base: dict) -> str:
    strong = [r for r in rows if r["verdict"] == "Double down"]
    weak = [r for r in rows if r["verdict"] == "Fix"]
    early = [r for r in rows if r["verdict"] == "Too early"]
    parts = [f"Company win rate {base['win_rate_%']}% on {base['closed']} closed deals (trailing year)."]
    if strong:
        parts.append("Winning: " + ", ".join(f"{r[dim]} {r['win_rate_%']}% ({r['closed']} deals)" for r in strong) + ".")
    if weak:
        parts.append("Losing: " + ", ".join(f"{r[dim]} {r['win_rate_%']}% (top loss: {r['top_loss_reason'] or 'n/a'})" for r in weak) + ".")
    watch = [r for r in rows if r["verdict"] == "Watch"]
    if watch:
        parts.append("Watch (gap is real-looking but the sample could be noise): " + ", ".join(f"{r[dim]} {r['win_rate_%']}%" for r in watch) + ".")
    if early:
        parts.append(f"Too early to call: {', '.join(r[dim] for r in early)}.")
    return " ".join(parts)


def main() -> None:
    cfg = load_config()
    opps = read_csv("opportunities.csv")
    base = company_baseline(opps, cfg)
    labels = {k: v["label"] for k, v in cfg["segments"].items()}
    rows = performance_by(opps, "segment", cfg, label=lambda k: labels.get(k, k))
    print("=== Company baseline (trailing year) ===")
    print(table([base]))
    print("\n=== By industry segment ===")
    print(table(rows, ["segment", "closed", "won", "win_rate_%", "range_80%", "vs_company_pts", "avg_won_$",
                       "median_cycle_days", "velocity_$_per_day", "open_pipeline_$", "top_loss_reason", "verdict"]))
    print("\n=== By product line / region / source ===")
    for dim in ("product_line", "region", "source"):
        print(table(performance_by(opps, dim, cfg), [dim, "closed", "win_rate_%", "range_80%", "avg_won_$", "median_cycle_days", "verdict"]))
    print("\n=== Headline ===\n" + headline(rows, "segment", base))
    write_csv("segment_performance.csv", rows)


if __name__ == "__main__":
    main()

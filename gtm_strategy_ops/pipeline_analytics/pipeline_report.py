"""Pipeline analytics: coverage, segmentation, win rates, stage aging, narrative.

Role scope (GTM Strategy & Ops):
  reporting on pipeline coverage, conversion rates, forecast accuracy and retention
  analytical views segmented by region, product, source and owner
  decision-focused pipeline and forecast narratives

    python -m gtm_strategy_ops.pipeline_analytics.pipeline_report
"""
from __future__ import annotations

from collections import defaultdict
from statistics import median

from shared_core.config import AS_OF, fiscal_quarter, load_config, parse_date, pct, read_csv, table, to_float, write_csv


def stage_probability(cfg: dict) -> dict:
    return {s["name"]: s["probability"] for s in cfg["opportunity"]["stages"]}


def open_in_quarter(opps: list[dict], quarter: str) -> list[dict]:
    return [o for o in opps if o["is_closed"] != "True" and o["forecast_category"] != "Omitted"
            and fiscal_quarter(parse_date(o["close_date"])) == quarter]


def coverage(opps: list[dict], cfg: dict) -> list[dict]:
    q = cfg["current_fiscal_quarter"]
    quota = cfg["quota"][q]
    probs = stage_probability(cfg)
    won = defaultdict(float)
    for o in opps:
        if o["is_won"] == "True" and fiscal_quarter(parse_date(o["close_date"])) == q:
            won[o["region"]] += to_float(o["amount"])
    rows = []
    for region, target in quota.items():
        pipe = [o for o in open_in_quarter(opps, q) if o["region"] == region]
        total = sum(to_float(o["amount"]) for o in pipe)
        remaining = max(target - won[region], 1)
        cov = round(total / remaining, 2)
        rows.append({"quarter": q, "region": region, "quota": target, "closed_won": int(won[region]),
                     "open_pipeline": int(total), "weighted": int(sum(to_float(o["amount"]) * probs[o["stage"]] for o in pipe)),
                     "commit": int(sum(to_float(o["amount"]) for o in pipe if o["forecast_category"] == "Commit")),
                     "coverage_x": cov,
                     "status": "OK" if cov >= cfg["opportunity"]["coverage_target"] else ("WATCH" if cov >= 2 else "GAP")})
    return rows


def open_pipeline_by(opps: list[dict], dim: str) -> list[dict]:
    groups = defaultdict(list)
    for o in opps:
        if o["is_closed"] != "True":
            groups[o[dim] or "(blank)"].append(o)
    rows = []
    for k, g in groups.items():
        ages = [(AS_OF - parse_date(o["created_date"])).days for o in g]
        rows.append({dim: k, "opps": len(g), "pipeline_$": int(sum(to_float(o["amount"]) for o in g)),
                     "avg_deal_$": int(sum(to_float(o["amount"]) for o in g) / len(g)), "median_age_days": int(median(ages))})
    return sorted(rows, key=lambda r: -r["pipeline_$"])


def win_rates_by(opps: list[dict], dim: str) -> list[dict]:
    groups = defaultdict(list)
    for o in opps:
        if o["is_closed"] == "True":
            groups[o[dim] or "(blank)"].append(o)
    rows = []
    for k, g in groups.items():
        won = [o for o in g if o["is_won"] == "True"]
        won_amt, all_amt = sum(to_float(o["amount"]) for o in won), sum(to_float(o["amount"]) for o in g)
        cycles = [(parse_date(o["close_date"]) - parse_date(o["created_date"])).days for o in won]
        rows.append({dim: k, "closed": len(g), "won": len(won), "win_rate_%": pct(len(won), len(g)),
                     "win_rate_$_%": pct(won_amt, all_amt), "median_cycle_days": int(median(cycles)) if cycles else ""})
    return sorted(rows, key=lambda r: -r["closed"])


def stage_aging(opps: list[dict], cfg: dict) -> list[dict]:
    limits = {s["name"]: s["max_days"] for s in cfg["opportunity"]["stages"] if s["max_days"]}
    rows = []
    for o in opps:
        if o["is_closed"] == "True" or o["stage"] not in limits:
            continue
        days = (AS_OF - parse_date(o["stage_entered_date"])).days
        if days > limits[o["stage"]]:
            rows.append({"opportunity_id": o["opportunity_id"], "account_name": o["account_name"], "owner": o["owner"],
                         "stage": o["stage"], "days_in_stage": days, "limit": limits[o["stage"]], "amount": o["amount"]})
    return sorted(rows, key=lambda r: -(r["days_in_stage"] - r["limit"]))


def narrative(cov: list[dict], wr_product: list[dict], aging: list[dict]) -> str:
    gaps = [c for c in cov if c["status"] != "OK"]
    total_cov = round(sum(c["open_pipeline"] for c in cov) / max(1, sum(c["quota"] - c["closed_won"] for c in cov)), 2)
    best = max(wr_product, key=lambda r: r["win_rate_%"])
    parts = [f"{cov[0]['quarter']} coverage is {total_cov}x overall"]
    if gaps:
        parts.append("; " + ", ".join(f"{g['region']} {g['coverage_x']}x ({g['status']})" for g in gaps) + " need pipeline")
    parts.append(f". {best['product_line'].title()} wins {best['win_rate_%']}% of closed deals. ")
    stuck = sum(to_float(a["amount"]) for a in aging)
    parts.append(f"{len(aging)} open deals worth ${stuck:,.0f} are past their stage time limit; "
                 "inspect these first in the forecast call.")
    return "".join(parts)


def main() -> None:
    cfg = load_config()
    opps = read_csv("opportunities.csv")
    cov = coverage(opps, cfg)
    print(f"=== 1. Coverage: {cfg['current_fiscal_quarter']} (target {cfg['opportunity']['coverage_target']}x) ===")
    print(table(cov))
    for dim in ("region", "product_line", "source", "owner"):
        print(f"\n=== 2. Open pipeline by {dim} ===")
        print(table(open_pipeline_by(opps, dim)))
    wr_prod = win_rates_by(opps, "product_line")
    print("\n=== 3. Win rate + cycle by product line / source / segment ===")
    print(table(wr_prod))
    print(table(win_rates_by(opps, "source")))
    print(table(win_rates_by(opps, "segment")))
    aging = stage_aging(opps, cfg)
    print(f"\n=== 4. Deals past stage time limit: {len(aging)} ===")
    print(table(aging[:10]))
    print("\n=== 5. Narrative ===\n" + narrative(cov, wr_prod, aging))
    write_csv("pipeline_coverage.csv", cov)
    write_csv("stage_aging.csv", aging)


if __name__ == "__main__":
    main()

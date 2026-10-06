"""Consumption vs minimum commit: overage, shelfware and the revenue it implies.

Role scope (RevOps, lead-to-cash): Sardine sells on a consumption model with a minimum
monthly commit; usage draws the commit down and overages bill monthly [VERIFY]. That
makes two things RevOps has to see every month, not at renewal:

  1. Overage    usage above commit -> the customer has outgrown the contract.
                Expansion conversation now (re-commit at a better rate), not at renewal.
  2. Shelfware  trailing-90-day usage well below commit -> the customer is paying for
                volume they don't use. That shows up as a downsell or churn at renewal
                unless someone runs an adoption plan first. New logos still integrating
                (config consumption.ramp_months) are excused.

Outputs: a commit-vs-usage summary by product line and region, the overage and shelfware
action lists (each routed to the account owner), and a run-rate view of billed revenue.

    python -m gtm_strategy_ops.consumption.commit_burndown
"""
from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date

from shared_core.config import AS_OF, DATA_DIR, load_config, read_csv, table, to_float


def months_between(start: date, month: str) -> int:
    y, m = int(month[:4]), int(month[5:7])
    return (y - start.year) * 12 + m - start.month


def account_view(rows: list[dict], cfg: dict) -> list[dict]:
    """One row per account x product line with trailing-3-month utilization and flags."""
    c = cfg["consumption"]
    by_key: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        by_key[(r["account_id"], r["product_line"])].append(r)
    out = []
    for (_acct, pl), hist in by_key.items():
        hist.sort(key=lambda r: r["month"])
        last3 = hist[-3:]
        commit = sum(to_float(r["monthly_commit"]) for r in last3)
        usage = sum(to_float(r["usage_billed"]) for r in last3)
        util = round(100 * usage / commit, 1) if commit else 0.0
        latest = hist[-1]
        months_live = months_between(date.fromisoformat(latest["contract_start"]), latest["month"]) + 1
        ramping = months_live <= c["ramp_months"]
        first_util = to_float(hist[0]["usage_billed"]) / max(1.0, to_float(hist[0]["monthly_commit"]))
        trend = round(100 * (util / 100 - first_util), 1) if len(hist) >= 4 else 0.0
        if util >= c["overage_alert_pct"]:
            flag = "Overage: expansion"
        elif util < c["shelfware_alert_pct"] and not ramping:
            flag = "Shelfware: adoption plan"
        elif ramping:
            flag = "Ramping"
        else:
            flag = ""
        out.append({
            "account_name": latest["account_name"], "segment": latest["segment"], "region": latest["region"],
            "product_line": pl, "owner": latest["owner"], "monthly_commit": int(to_float(latest["monthly_commit"])),
            "util_3mo_%": util, "util_change_pts": trend, "overage_3mo_$": int(sum(to_float(r["overage"]) for r in last3)),
            "months_live": months_live, "flag": flag,
        })
    return out


def summary(rows: list[dict], key: str) -> list[dict]:
    agg: dict[str, dict] = defaultdict(lambda: {"accounts": 0, "commit_$": 0.0, "usage_$": 0.0, "overage_$": 0.0})
    latest_month = max(r["month"] for r in rows)
    for r in rows:
        if r["month"] != latest_month:
            continue
        a = agg[r[key]]
        a["accounts"] += 1
        a["commit_$"] += to_float(r["monthly_commit"])
        a["usage_$"] += to_float(r["usage_billed"])
        a["overage_$"] += to_float(r["overage"])
    return [{key: k, "accounts": v["accounts"], "commit_$": int(v["commit_$"]), "billed_usage_$": int(v["usage_$"]),
             "utilization_%": round(100 * v["usage_$"] / v["commit_$"], 1) if v["commit_$"] else 0.0,
             "overage_$": int(v["overage_$"]),
             # billed revenue = max(commit, usage) per account; approximated here as commit + overage
             "billed_revenue_$": int(v["commit_$"] + v["overage_$"])}
            for k, v in sorted(agg.items(), key=lambda kv: -kv[1]["commit_$"])]


def main() -> None:
    cfg = load_config()
    rows = read_csv("consumption.csv")
    month = max(r["month"] for r in rows)
    print(f"=== Commit vs usage, {month} (as of {AS_OF}) ===\n")
    print(table(summary(rows, "product_line")))
    print()
    print(table(summary(rows, "region")))

    view = account_view(rows, cfg)
    over = sorted([v for v in view if v["flag"].startswith("Overage")], key=lambda v: -v["overage_3mo_$"])
    shelf = sorted([v for v in view if v["flag"].startswith("Shelfware")], key=lambda v: v["util_3mo_%"])
    cols = ["account_name", "product_line", "region", "owner", "monthly_commit", "util_3mo_%", "util_change_pts", "overage_3mo_$"]
    print(f"\n=== Overage: {len(over)} account lines above commit -> re-commit conversation now ===")
    print(table([{k: v[k] for k in cols} for v in over[:10]]))
    print(f"\n=== Shelfware: {len(shelf)} account lines under {cfg['consumption']['shelfware_alert_pct']}% of commit "
          f"(excl. first {cfg['consumption']['ramp_months']} months) -> adoption plan before renewal ===")
    print(table([{k: v[k] for k in cols} for v in shelf[:10]]))

    commit_total = sum(v["monthly_commit"] for v in view)
    shelf_commit = sum(v["monthly_commit"] for v in shelf)
    over_total = sum(v["overage_3mo_$"] for v in over)
    print("\n=== Narrative ===")
    print(f"{len(over)} account lines billed ${over_total:,} of overage in the last three months: each is a re-commit "
          f"opportunity. {len(shelf)} lines carry ${shelf_commit * 12:,} of annualized commit "
          f"({round(100 * shelf_commit / max(1, commit_total))}% of total) on under-used contracts; that is the downsell "
          "exposure at renewal if no one runs an adoption plan.")
    out = DATA_DIR.parent / "outputs"
    out.mkdir(exist_ok=True)

    with open(out / "consumption_actions.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(view[0].keys()))
        w.writeheader()
        w.writerows([v for v in view if v["flag"]])
    print("\nAction list -> outputs/consumption_actions.csv")


if __name__ == "__main__":
    main()

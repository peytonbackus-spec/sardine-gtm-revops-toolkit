"""Territory plan: score every account, tier it, and carve balanced named-account books per AE.

Steps:
  1. Account potential = segment fit (config `segments.*.icp_points`) + company size (config
     `lead_scoring.size_bands`) + whitespace (+10 for a customer that owns one product line but not
     the other: the fraud <-> compliance cross-sell). Non-ICP accounts are excluded.
  2. Tier by percentile of potential: T1 (top `tier_cutoffs_pct.T1`%), T2 (up to `T2`%), the rest pooled
     for inbound and SDR coverage rather than named.
  3. Assign within each region. Live customers stay with their current owner (`keep_customer_owner`);
     then T1 and T2 accounts go, highest potential first, to the AE with the lowest potential per unit
     of capacity, within the per-AE caps. A ramping AE counts as a fraction of a seat, so new hires get
     smaller books instead of equal books they cannot work.
  4. Balance check: each AE's potential per capacity unit vs the region mean. Outside
     `balance_tolerance_pct`, the carve is not fair and quotas built on it will not be either.

This replaces "who had it last year" carving. The same potential score can weight quota by territory,
so a rep with a smaller book carries a smaller number.

    python -m gtm_strategy_ops.sales_planning.territory_plan
"""
from __future__ import annotations

from collections import defaultdict

from gtm_strategy_ops.sales_planning.team import ramp_factor, roster
from shared_core.config import load_config, pct, read_csv, table, to_bool, write_csv

WHITESPACE_POINTS = 10
MIN_SEAT = 0.33   # a ramping AE still gets a starter book


def size_points(employees: int, cfg: dict) -> int:
    for band in cfg["lead_scoring"]["size_bands"]:
        if employees >= band["min_employees"]:
            return band["points"]
    return cfg["lead_scoring"]["size_default_points"]


def score_accounts(accounts: list[dict], cfg: dict) -> list[dict]:
    product_lines = [k for k in cfg["product_lines"] if k != "cross_sell"]
    rows = []
    for a in accounts:
        if a["segment"] == "other":
            continue
        owned = [p for p in (a.get("products_owned") or "").split(";") if p]
        whitespace = to_bool(a["is_customer"]) and 0 < len(owned) < len(product_lines)
        pot = cfg["segments"][a["segment"]]["icp_points"] + size_points(int(a["employees"] or 0), cfg) + (WHITESPACE_POINTS if whitespace else 0)
        rows.append({**a, "potential": pot, "whitespace": whitespace})
    ranked = sorted(rows, key=lambda r: -r["potential"])
    cut = cfg["sales_planning"]["territory"]["tier_cutoffs_pct"]
    for i, r in enumerate(ranked):
        p = 100 * (i + 1) / len(ranked)
        r["tier"] = "T1" if p <= cut["T1"] else "T2" if p <= cut["T2"] else "Pooled"
    return ranked


def current_owners() -> dict[str, str]:
    """Owner of each live customer: the most recent renewal or opportunity owner."""
    owners = {}
    for o in sorted(read_csv("opportunities.csv"), key=lambda o: o["created_date"]):
        owners[o["account_id"]] = o["owner"]
    for r in read_csv("renewals.csv"):
        owners.setdefault(r["account_id"], r["owner"])
    return owners


def assign(scored: list[dict], cfg: dict) -> tuple[list[dict], list[dict]]:
    tp = cfg["sales_planning"]["territory"]
    q = cfg["current_fiscal_quarter"]
    team = roster(cfg)
    seat = {ae: max(MIN_SEAT, ramp_factor(r["start_date"], q, cfg)) for ae, r in team.items()}
    load = defaultdict(float)
    count = defaultdict(lambda: defaultdict(int))
    owners = current_owners() if tp["keep_customer_owner"] else {}
    out = []
    named = [a for a in scored if a["tier"] in ("T1", "T2")]
    for a in sorted(named, key=lambda a: (not to_bool(a["is_customer"]), -a["potential"])):
        region_aes = [ae for ae, r in team.items() if r["region"] == a["region"]]
        owner, reason = None, ""
        if to_bool(a["is_customer"]) and owners.get(a["account_id"]) in region_aes:
            owner, reason = owners[a["account_id"]], "customer: keep owner"
        else:
            room = [ae for ae in region_aes if count[ae][a["tier"]] < tp["max_named_accounts_per_ae"][a["tier"]] * seat[ae]]
            if room:
                owner = min(room, key=lambda ae: load[ae] / seat[ae])
                reason = "balanced"
            else:
                reason = "over capacity: pooled"
        if owner:
            load[owner] += a["potential"]
            count[owner][a["tier"]] += 1
        out.append({"account_id": a["account_id"], "account_name": a["account_name"], "segment": a["segment"], "region": a["region"],
                    "tier": a["tier"] if owner else "Pooled", "potential": a["potential"], "whitespace": a["whitespace"],
                    "owner": owner or "Pooled (SDR / inbound)", "reason": reason})
    balance = []
    for region in cfg["regions"]:
        aes = [ae for ae, r in team.items() if r["region"] == region]
        if not aes:
            continue
        per_seat = {ae: load[ae] / seat[ae] for ae in aes}
        mean = sum(per_seat.values()) / len(aes)
        for ae in aes:
            dev = pct(per_seat[ae] - mean, mean) if mean else 0.0
            ok = len(aes) == 1 or abs(dev) <= tp["balance_tolerance_pct"]
            balance.append({"owner": ae, "region": region, "seat": round(seat[ae], 2), "T1": count[ae]["T1"], "T2": count[ae]["T2"],
                            "potential": int(load[ae]), "potential_per_seat": int(per_seat[ae]), "vs_region_mean_%": dev,
                            "flag": "OK" if ok else ("Over-served" if dev > 0 else "Under-served")})
    return out, balance


def main() -> None:
    cfg = load_config()
    scored = score_accounts(read_csv("accounts.csv"), cfg)
    tiers = defaultdict(int)
    for s in scored:
        tiers[s["tier"]] += 1
    print(f"=== Account tiers ({len(scored)} ICP accounts) ===")
    print(table([{"tier": k, "accounts": v} for k, v in sorted(tiers.items())]))
    assignments, balance = assign(scored, cfg)
    print("\n=== Book balance by AE (potential per seat; ramping AEs count as a fraction of a seat) ===")
    print(table(balance))
    pooled = [a for a in assignments if a["owner"].startswith("Pooled")]
    if pooled:
        print(f"\n{len(pooled)} T1/T2 accounts exceed named-account capacity and fall to the pool: a hiring or SDR-coverage signal.")
    write_csv("territory_assignments.csv", assignments)
    write_csv("territory_balance.csv", balance)


if __name__ == "__main__":
    main()

"""🟩 Consumption vs minimum commit."""
from gtm_strategy_ops.consumption.commit_burndown import account_view, pricing_mix, summary
from shared_core.config import load_config, read_csv

CFG = load_config()


def row(month, commit, usage, start="2025-06-01", acct="A1", pl="fraud"):
    return {"account_id": acct, "account_name": "Test Pay", "segment": "fintech_neobank", "region": "NA",
            "product_line": pl, "month": month, "contract_start": start, "monthly_commit": str(commit),
            "usage_billed": str(usage), "overage": str(max(0, usage - commit)), "owner": "AE - Test"}


def months(vals, **kw):
    return [row(f"2026-{m:02d}", 10000, u, **kw) for m, u in zip(range(4, 10), vals)]


def test_overage_is_flagged_for_expansion():
    v = account_view(months([9000, 10000, 11000, 12000, 12500, 13000]), CFG)[0]
    assert v["flag"].startswith("Overage") and v["overage_3mo_$"] == 7500


def test_shelfware_flagged_after_ramp_only():
    mature = account_view(months([4000] * 6), CFG)[0]
    ramping = account_view(months([0, 0, 0, 1000, 2000, 4000], start="2026-07-01"), CFG)[0]
    assert mature["flag"].startswith("Shelfware")
    assert ramping["flag"] == "Ramping"


def test_summary_billed_revenue_is_commit_plus_overage():
    s = summary(months([10000, 10000, 10000, 10000, 10000, 15000]), "product_line")[0]
    assert s["billed_revenue_$"] == 15000 and s["overage_$"] == 5000


def test_sample_data_has_both_flags():
    flags = {v["flag"].split(":")[0] for v in account_view(read_csv("consumption.csv"), CFG)}
    assert {"Overage", "Shelfware"} <= flags


def test_flat_rate_contracts_never_raise_usage_alerts():
    rows = [{**r, "pricing_model": "flat"} for r in months([4000] * 6)]           # would be shelfware if consumption
    over = [{**r, "pricing_model": "flat"} for r in months([15000] * 6, acct="A2")]  # would be overage if consumption
    assert all(v["flag"] == "" and v["pricing_model"] == "flat" for v in account_view(rows + over, CFG))


def test_sample_data_mixes_flat_and_consumption():
    mix = {m["pricing_model"]: m for m in pricing_mix(read_csv("consumption.csv"))}
    assert set(mix) == {"flat", "consumption"}
    assert abs(sum(m["share_%"] for m in mix.values()) - 100) < 0.2


def test_roster_matches_the_sales_org_shape():
    roster = CFG["sales_team"]["ae_roster"]
    na = sum(1 for r in roster.values() if r["region"] == "NA")
    assert len(roster) == CFG["go_to_market"]["ae_count"] == 12
    assert 0.75 <= na / len(roster) <= 0.85            # ~80% US, the rest EMEA and APAC
    assert set(CFG["regions"]) == {"NA", "EMEA", "APAC"}
    assert CFG["go_to_market"]["motion"] == "sales_led"

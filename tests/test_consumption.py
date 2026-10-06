"""🟩 Consumption vs minimum commit."""
from gtm_strategy_ops.consumption.commit_burndown import account_view, summary
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

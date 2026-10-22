"""Take-home loader: synthetic fixture only. The real workbook is Sardine's data and is never used here."""
from datetime import datetime

import pytest

pd = pytest.importorskip("pandas")
openpyxl = pytest.importorskip("openpyxl")

from gtm_strategy_ops.takehome.loader import classify_pricing, load_all  # noqa: E402

MONTHS = [datetime(2024, 4, 30), datetime(2024, 5, 31), datetime(2024, 6, 30), datetime(2024, 7, 31),
          datetime(2024, 8, 31), datetime(2024, 9, 30)]

UNITS = [  # id, name, product, price, six monthly unit values
    ("C1", "Alpha", "Product A", 1000.0, [1, 1, 1, 1, 1, 1]),          # constant -> flat
    ("C1", "Alpha", "Product B", 500.0, [0, 0.5, 1, 1, 1, 1]),         # prorated first month -> flat
    ("C2", "Beta", "Product A", 800.0, [1, 1, 2, 2, 2, 2]),            # one step change -> flat
    ("C2", "Beta", "Product C", 2.0, [100, 250, 90, 400, 310, 120]),   # usage-driven -> consumption
    ("C3", "Gamma", "Product A", 0.0, [5000, 6000, 5500, 7000, 6500, 6100]),  # zero price -> flagged
    ("C4", "Delta", "Product A", 300.0, [1, 1, 1, 0, 0, 0]),           # churned, still flat
]
FIRMO = [  # id, name, region, vertical, sub, industry, segment, created, won, lost
    ("C1", "Alpha", "NAMER", "Banks", "Credit unions", "Banking", "Growth", "2023-01-05", 1, 0),
    ("C2", "Beta", "EMEA", "Payments", "Issuing", "Financial Services", "Unknown", "2023-02-05", 2, 1),
    ("C3", "Gamma", "Unknown", "Crypto", "Exchanges", "Software", "SMB", "2023-03-05", 0, 0),     # customer, no closed-won
    ("C4", "Delta", "NAMER", "Gaming", "Casinos", "Gambling", "SMB", "2023-04-05", 1, 0),
    ("X9", "Tidewell", "APAC", "Payments", "Acquiring", "Financial Services", "SMB", "2022-07-19", 0, 1),   # same ID, different company
    ("X9", "Larchmont", "NAMER", "Crypto", "Exchanges", "Software", "Unknown", "2021-11-02", 0, 2),
]


@pytest.fixture()
def workbook(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Invoiced Units"
    ws.append(["Quantities Used/Charged"])
    ws.append(["Company ID", "Company Name", "Product", "Unit price"] + MONTHS)
    for cid, name, prod, price, vals in UNITS:
        ws.append([cid, name, prod, price] + vals)
    fs = wb.create_sheet("Firmographic")
    fs.append(["Company ID", "Company name", "Region", "Vertical", "Sub-Vertical", "Industry", "Segment",
               "Customer Creation date", "Closed Won", "Closed Lost"])
    for row in FIRMO:
        fs.append(list(row))
    path = tmp_path / "takehome.xlsx"
    wb.save(path)
    return path


def test_classify_pricing_rules():
    assert classify_pricing([1, 1, 1, 1])[:2] == ("flat", "constant")
    assert classify_pricing([0.54, 1, 1, 1])[:2] == ("flat", "constant")          # prorated first month ignored
    assert classify_pricing([1, 1, 1, 0.4, 0, 0])[:2] == ("flat", "constant")     # partial last month, then churn
    assert classify_pricing([1, 1, 2, 2])[:2] == ("flat", "step")
    assert classify_pricing([100, 250, 90, 400])[0] == "consumption"
    assert classify_pricing([0, 0, 0])[0] == "inactive"
    assert classify_pricing([1, 1, 2, 2], max_flat_changes=0)[0] == "consumption"  # threshold is tunable


def test_revenue_is_units_times_price(workbook):
    t = load_all(workbook)
    m = t.monthly
    assert len(m) == len(UNITS) * len(MONTHS)
    row = m[(m.company_id == "C2") & (m["product"] == "Product C") & (m.month == "2024-05-31")].iloc[0]
    assert row.revenue == 250 * 2.0
    assert t.customers.set_index("company_id").loc["C1", "revenue_total"] == 6000 + (0.5 + 4) * 500


def test_pricing_model_per_line(workbook):
    lines = load_all(workbook).lines.set_index(["company_id", "product"])
    assert lines.loc[("C1", "Product A"), "pricing_model"] == "flat"
    assert lines.loc[("C1", "Product B"), "pricing_model"] == "flat"
    assert lines.loc[("C2", "Product C"), "pricing_model"] == "consumption"
    assert lines.loc[("C4", "Product A"), "pricing_model"] == "flat"


def test_default_is_product_based_and_both_columns_are_always_present(workbook):
    lines = load_all(workbook).lines.set_index(["company_id", "product"])
    row = lines.loc[("C3", "Product A")]                       # varying units on a flat-rate product
    assert row.pricing_model_product == "flat" and row.pricing_model_usage == "consumption"
    assert row.pricing_model == "flat"                         # default method is "product"
    usage = load_all(workbook, method="usage").lines.set_index(["company_id", "product"])
    assert usage.loc[("C3", "Product A"), "pricing_model"] == "consumption"
    assert (usage.pricing_model_product == lines.pricing_model_product).all()   # same columns either way


def test_monthly_carries_both_classifications(workbook):
    m = load_all(workbook).monthly
    assert {"pricing_model", "pricing_model_product", "pricing_model_usage"} <= set(m.columns)


def test_flat_products_are_configurable(workbook):
    lines = load_all(workbook, flat_products=("Product B",)).lines.set_index(["company_id", "product"])
    assert lines.loc[("C1", "Product A"), "pricing_model"] == "consumption"
    assert lines.loc[("C1", "Product B"), "pricing_model"] == "flat"


def test_unknown_method_is_rejected(workbook):
    with pytest.raises(ValueError, match="method"):
        load_all(workbook, method="contract")


def test_zero_price_lines_are_flagged_with_zero_revenue(workbook):
    t = load_all(workbook)
    assert t.quality["zero_price_lines"] == 1
    assert t.monthly[t.monthly.company_id == "C3"].revenue.sum() == 0


def test_colliding_company_ids_are_kept_apart_and_flagged(workbook):
    t = load_all(workbook)
    x9 = t.firmographic[t.firmographic.company_id == "X9"]
    assert len(x9) == 2 and set(x9.company_name) == {"Tidewell", "Larchmont"} and x9.id_collision.all()
    assert t.quality["id_collision_rows"] == 2 and t.quality["id_collision_ids"] == 1
    assert t.quality["collision_ids_that_are_customers"] == 0
    assert len(t.firmographic) == len(FIRMO)                          # nothing merged or dropped


def test_unknowns_and_missing_wins_are_flagged_not_dropped(workbook):
    t = load_all(workbook)
    c = t.customers.set_index("company_id")
    assert len(c) == 4
    assert bool(c.loc["C3", "region_unknown"]) and bool(c.loc["C2", "segment_unknown"])
    assert bool(c.loc["C3", "no_closed_won"]) and not bool(c.loc["C1", "no_closed_won"])
    assert t.quality["customers_without_closed_won"] == 1
    assert c.loc["C2", "win_rate"] == pytest.approx(2 / 3)


def test_customer_join_uses_id_and_name(workbook):
    c = load_all(workbook).customers.set_index("company_id")
    assert c.loc["C1", "region"] == "NAMER" and c.loc["C2", "region"] == "EMEA"
    assert c.loc["C1", "n_products"] == 2 and 0 <= c.loc["C2", "flat_revenue_share"] < 1


def test_missing_file_gives_a_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="_private/takehome/data.xlsx"):
        load_all(tmp_path / "nope.xlsx")


def test_missing_columns_fail_loudly(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Invoiced Units"
    ws.append(["title"])
    ws.append(["Company ID", "Product"] + MONTHS)
    wb.create_sheet("Firmographic")
    p = tmp_path / "bad.xlsx"
    wb.save(p)
    with pytest.raises(ValueError, match="missing expected columns"):
        load_all(p)

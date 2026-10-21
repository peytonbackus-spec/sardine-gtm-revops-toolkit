"""Workbook loader for a customer-usage and win/loss analysis.

The source workbook is private and lives in `_private/` (gitignored); it is never committed. This
module turns it into clean tables and a data-quality report, so every later number traces back to a
stated rule. Tests run on a synthetic workbook.

Rules (each is a documented assumption; change them here, not in the analysis):
  revenue        monthly revenue = units x unit price. ASSUMPTION: the price is per unit per month.
  pricing model  two classifications are always computed, and `pricing_model` is whichever one
                 `method` selects:
                   pricing_model_product  products in `flat_products` are flat-rate, all others
                                          consumption. The default ("product").
                   pricing_model_usage    inferred from usage: a line whose units never change (after
                                          ignoring a prorated first or last month) is flat, one step
                                          change is still flat, two or more changes is consumption.
                                          Tunable via `max_flat_changes` ("usage").
  zero price     lines with a unit price of 0 get revenue 0 and are flagged.
  company id     IDs that repeat across different companies are kept apart and flagged, never
                 merged; joins use ID and name.
  unknown values "Unknown" region or segment is kept and flagged, never dropped.

    python -m gtm_strategy_ops.takehome.loader            # prints the data-quality report
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PATH = REPO_ROOT / "_private" / "takehome" / "data.xlsx"
UNITS_SHEET, FIRMO_SHEET = "Invoiced Units", "Firmographic"
UNITS_COLS = ["Company ID", "Company Name", "Product", "Unit price"]
FIRMO_COLS = ["Company ID", "Company name", "Region", "Vertical", "Sub-Vertical", "Industry", "Segment",
              "Customer Creation date", "Closed Won", "Closed Lost"]
TOL = 1e-9
DEFAULT_FLAT_PRODUCTS = ("Product A", "Product B", "Product BB", "Product K", "Product S")
METHODS = ("product", "usage")


@dataclass
class Tables:
    lines: pd.DataFrame         # one row per customer x product line, wide, with pricing classification
    monthly: pd.DataFrame       # long: line x month with units and revenue
    firmographic: pd.DataFrame  # one row per Firmographic row (collisions kept apart)
    customers: pd.DataFrame     # one row per invoiced customer: firmographics + revenue + pricing mix
    quality: dict               # counts and notes about the data


def classify_pricing(units, max_flat_changes: int = 1) -> tuple[str, str, int]:
    """Return (pricing_model, pattern, n_changes) for one line's monthly units.

    Zero months are not billed months and are ignored. A first or last billed month below the
    most common value is treated as proration and ignored.
    """
    billed = [float(u) for u in units if u is not None and float(u) > TOL]
    if not billed:
        return "inactive", "none", 0
    mode = Counter(round(v, 9) for v in billed).most_common(1)[0][0]
    core = billed[:]
    if len(core) > 1 and core[0] < mode - TOL:
        core = core[1:]
    if len(core) > 1 and core[-1] < mode - TOL:
        core = core[:-1]
    changes = sum(abs(a - b) > TOL for a, b in zip(core, core[1:]))
    pattern = "constant" if changes == 0 else "step" if changes == 1 else "variable"
    return ("flat" if changes <= max_flat_changes else "consumption"), pattern, changes


def _require(df: pd.DataFrame, cols: list[str], sheet: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Sheet '{sheet}' is missing expected columns: {missing}")


def load_lines(path: Path | str = DEFAULT_PATH, max_flat_changes: int = 1, method: str = "product",
               flat_products=DEFAULT_FLAT_PRODUCTS) -> tuple[pd.DataFrame, list]:
    """Read the units sheet (a title row sits above the header). Returns (lines, month_columns).

    Both `pricing_model_product` and `pricing_model_usage` are always present; `pricing_model`
    copies the one named by `method`.
    """
    if method not in METHODS:
        raise ValueError(f"method must be one of {METHODS}, got {method!r}")
    raw = pd.read_excel(path, sheet_name=UNITS_SHEET, header=1)
    _require(raw, UNITS_COLS, UNITS_SHEET)
    months = [c for c in raw.columns if not isinstance(c, str)]
    if not months:
        raise ValueError(f"Sheet '{UNITS_SHEET}' has no month columns")
    lines = raw[UNITS_COLS + months].copy()
    lines[months] = lines[months].apply(pd.to_numeric, errors="coerce").fillna(0.0)
    lines = lines.rename(columns={"Company ID": "company_id", "Company Name": "company_name",
                                  "Product": "product", "Unit price": "unit_price"})
    cls = [classify_pricing(row, max_flat_changes) for row in lines[months].itertuples(index=False)]
    lines["pricing_model_usage"], lines["pattern"], lines["n_changes"] = zip(*cls) if cls else ([], [], [])
    flat_set = set(flat_products)
    lines["pricing_model_product"] = ["flat" if p in flat_set else "consumption" for p in lines["product"]]
    lines["pricing_model"] = lines[f"pricing_model_{method}"]
    lines["zero_price"] = lines["unit_price"].fillna(0) <= 0
    return lines, months


def to_monthly(lines: pd.DataFrame, months: list) -> pd.DataFrame:
    """Long table: one row per line per month, revenue = units x unit price."""
    keep = ["company_id", "company_name", "product", "unit_price", "pricing_model",
            "pricing_model_product", "pricing_model_usage", "zero_price"]
    long = lines.melt(id_vars=keep, value_vars=months, var_name="month", value_name="units")
    long["month"] = pd.to_datetime(long["month"])
    long["revenue"] = long["units"] * long["unit_price"].fillna(0.0)
    return long


def load_firmographic(path: Path | str = DEFAULT_PATH) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name=FIRMO_SHEET)
    _require(raw, FIRMO_COLS, FIRMO_SHEET)
    f = raw[FIRMO_COLS].rename(columns={
        "Company ID": "company_id", "Company name": "company_name", "Region": "region", "Vertical": "vertical",
        "Sub-Vertical": "sub_vertical", "Industry": "industry", "Segment": "segment",
        "Customer Creation date": "created", "Closed Won": "closed_won", "Closed Lost": "closed_lost"})
    for c in ("region", "vertical", "sub_vertical", "industry", "segment"):
        f[c] = f[c].fillna("Unknown").astype(str).str.strip().replace("", "Unknown")
    f["created"] = pd.to_datetime(f["created"], errors="coerce")
    f[["closed_won", "closed_lost"]] = f[["closed_won", "closed_lost"]].apply(pd.to_numeric, errors="coerce").fillna(0).astype(int)
    f["id_collision"] = f["company_id"].duplicated(keep=False)
    f["region_unknown"] = f["region"].eq("Unknown")
    f["segment_unknown"] = f["segment"].eq("Unknown")
    return f


def build_customers(lines: pd.DataFrame, monthly: pd.DataFrame, firmo: pd.DataFrame, months: list) -> pd.DataFrame:
    first, last = min(months), max(months)
    rev = monthly.groupby(["company_id", "company_name"]).agg(revenue_total=("revenue", "sum"), n_lines=("product", "nunique")).reset_index()
    prod = lines.groupby(["company_id", "company_name"]).agg(n_products=("product", "nunique"), zero_price_lines=("zero_price", "sum")).reset_index()
    by_m = monthly.pivot_table(index=["company_id", "company_name"], columns="month", values="revenue", aggfunc="sum", fill_value=0.0)
    mrr = pd.DataFrame({"mrr_first": by_m.get(pd.Timestamp(first), 0.0), "mrr_last": by_m.get(pd.Timestamp(last), 0.0)}).reset_index()
    flat = (monthly[monthly["pricing_model"] == "flat"].groupby(["company_id", "company_name"])["revenue"].sum()
            .rename("flat_revenue").reset_index())
    c = rev.merge(prod, on=["company_id", "company_name"]).merge(mrr, on=["company_id", "company_name"], how="left") \
           .merge(flat, on=["company_id", "company_name"], how="left")
    c["flat_revenue"] = c["flat_revenue"].fillna(0.0)
    c["flat_revenue_share"] = (c["flat_revenue"] / c["revenue_total"].where(c["revenue_total"] > 0)).fillna(0.0)
    c = c.merge(firmo, on=["company_id", "company_name"], how="left", validate="one_to_one")   # ID and name, never ID alone
    for flag in ("id_collision", "region_unknown", "segment_unknown"):
        c[flag] = c[flag].fillna(False).astype(bool)          # customers with no firmographic row
    c["no_closed_won"] = c["closed_won"].fillna(0).eq(0)
    denom = (c["closed_won"].fillna(0) + c["closed_lost"].fillna(0)).where(lambda s: s > 0)
    c["win_rate"] = c["closed_won"] / denom
    return c


def quality_report(lines, monthly, firmo, customers, months) -> dict:
    return {
        "invoiced_lines": len(lines), "invoiced_customers": int(lines["company_id"].nunique()),
        "products": int(lines["product"].nunique()), "months": [str(pd.Timestamp(m).date()) for m in (min(months), max(months))],
        "pricing_model_lines": lines["pricing_model"].value_counts().to_dict(),
        "pricing_model_product_lines": lines["pricing_model_product"].value_counts().to_dict(),
        "pricing_model_usage_lines": lines["pricing_model_usage"].value_counts().to_dict(),
        "pattern_lines": lines["pattern"].value_counts().to_dict(),
        "zero_price_lines": int(lines["zero_price"].sum()),
        "firmographic_rows": len(firmo),
        "id_collision_rows": int(firmo["id_collision"].sum()), "id_collision_ids": int(firmo.loc[firmo["id_collision"], "company_id"].nunique()),
        "collision_ids_that_are_customers": int(customers["id_collision"].sum()),
        "firmo_unknown_region_rows": int(firmo["region_unknown"].sum()), "firmo_unknown_segment_rows": int(firmo["segment_unknown"].sum()),
        "customers_unknown_region": int(customers["region_unknown"].sum()), "customers_unknown_segment": int(customers["segment_unknown"].sum()),
        "customers_missing_firmographics": int(customers["region"].isna().sum()),
        "customers_without_closed_won": int(customers["no_closed_won"].sum()),
        "notes": ["revenue = units x unit price, assuming the price is per unit per month (confirm with Sardine)",
                  "pricing model is assumed (product-based by default, usage-inferred as the alternative), not read from a contract field",
                  "Company IDs repeat for different companies in Firmographic; they are not merged"],
    }


def load_all(path: Path | str = DEFAULT_PATH, max_flat_changes: int = 1, method: str = "product",
             flat_products=DEFAULT_FLAT_PRODUCTS) -> Tables:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Copy the workbook to _private/takehome/data.xlsx (gitignored).")
    lines, months = load_lines(path, max_flat_changes, method, flat_products)
    monthly = to_monthly(lines, months)
    firmo = load_firmographic(path)
    customers = build_customers(lines, monthly, firmo, months)
    return Tables(lines, monthly, firmo, customers, quality_report(lines, monthly, firmo, customers, months))


def main() -> None:
    q = load_all().quality
    print("=== Workbook data quality ===")
    for k, v in q.items():
        if k != "notes":
            print(f"{k:34} {v}")
    print("\nNotes:")
    for n in q["notes"]:
        print(f"  - {n}")


if __name__ == "__main__":
    main()

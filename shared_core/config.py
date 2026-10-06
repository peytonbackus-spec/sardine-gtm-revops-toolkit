"""Shared config + IO helpers used by both role tracks.

Everything company-specific lives in a YAML config; this module is the only place
that knows where that file and the sample data live.

Config resolution order:
  1. $GTM_CONFIG (path to any YAML file)
  2. config/company.yaml   (created by `make new` for a real company repo)
  3. config/example.yaml   (the shipped example; used by tests and the demo)
"""
from __future__ import annotations

import csv
import os
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "sample_data"
OUTPUT_DIR = ROOT / "outputs"


def resolve_config_path() -> Path:
    env = os.environ.get("GTM_CONFIG")
    if env:
        return Path(env)
    company = ROOT / "config" / "company.yaml"
    return company if company.exists() else ROOT / "config" / "example.yaml"


CONFIG_PATH = resolve_config_path()


@lru_cache(maxsize=1)
def load_config(path: str | None = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


# Fixed "as of" date (config: fiscal.as_of_date) so every report reproduces against the synthetic data.
_fiscal = load_config().get("fiscal", {})
AS_OF: date = _fiscal.get("as_of_date") or date.today()
FY_START_MONTH: int = int(_fiscal.get("year_start_month", 1))


def read_csv(name: str) -> list[dict]:
    path = DATA_DIR / name if not Path(name).is_absolute() else Path(name)
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv(name: str, rows: Iterable[dict], fieldnames: list[str] | None = None) -> Path:
    rows = list(rows)
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / name
    if not rows:
        path.write_text("")
        return path
    fieldnames = fieldnames or list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.strptime(value[:10], "%Y-%m-%d").date()


def to_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def to_bool(value) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def pct(n: float, d: float) -> float:
    return round(100.0 * n / d, 1) if d else 0.0


def table(rows: list[dict], cols: list[str] | None = None) -> str:
    """Tiny dependency-free text table for console output."""
    if not rows:
        return "(no rows)"
    cols = cols or list(rows[0].keys())
    widths = {c: max(len(c), *(len(str(r.get(c, ""))) for r in rows)) for c in cols}
    line = "  ".join(c.ljust(widths[c]) for c in cols)
    sep = "  ".join("-" * widths[c] for c in cols)
    body = "\n".join("  ".join(str(r.get(c, "")).ljust(widths[c]) for c in cols) for r in rows)
    return f"{line}\n{sep}\n{body}"


def dedupe_leads(leads: list[dict]) -> list[dict]:
    """Drop duplicate leads (same email; keep the earliest). Mirrors v_leads.is_duplicate in the
    semantic-layer SQL so Python reports and SQL dashboards count the same leads."""
    seen, out = set(), []
    for lead in sorted(leads, key=lambda l: (l.get("created_date", ""), l.get("lead_id", ""))):
        key = (lead.get("email") or "").lower()
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        out.append(lead)
    return out


def fiscal_quarter(d: date, start_month: int | None = None) -> str:
    """Fiscal quarter label, e.g. "FY27-Q1". `start_month` is the month the fiscal year begins
    (config: fiscal.year_start_month). With start_month=10, Oct-Dec 2026 = FY27-Q1; with 1,
    the fiscal year is the calendar year. Same logic as close_fiscal_quarter in semantic_layer.sql."""
    sm = start_month or FY_START_MONTH
    fy = d.year + (1 if sm > 1 and d.month >= sm else 0)
    q = ((d.month - sm) % 12) // 3 + 1
    return f"FY{str(fy)[2:]}-Q{q}"

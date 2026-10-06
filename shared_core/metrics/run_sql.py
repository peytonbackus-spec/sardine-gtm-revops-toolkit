"""Run any SQL file in this repo against sample_data/ in an in-memory SQLite warehouse.

    python -m shared_core.metrics.run_sql gtm_engineer/funnel_analytics/sql/lead_funnel.sql
    python -m shared_core.metrics.run_sql gtm_strategy_ops/pipeline_analytics/sql/pipeline_coverage.sql

The semantic layer is always loaded first, so role-specific SQL builds on the
same typed views. That's how both roles get one definition per metric.
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

from shared_core.config import AS_OF, DATA_DIR, FY_START_MONTH, ROOT, load_config, table

SEMANTIC = ROOT / "shared_core" / "metrics" / "sql" / "semantic_layer.sql"


def render(sql: str) -> str:
    """Fill config placeholders so SQL and Python share one definition:
    {{FY_START_MONTH}}, {{CURRENT_FISCAL_QUARTER}}, {{AS_OF}}."""
    return (sql.replace("{{FY_START_MONTH}}", str(FY_START_MONTH))
               .replace("{{CURRENT_FISCAL_QUARTER}}", str(load_config()["current_fiscal_quarter"]))
               .replace("{{AS_OF}}", AS_OF.isoformat()))


def load_warehouse() -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    for csv_path in sorted(DATA_DIR.glob("*.csv")):
        with open(csv_path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        if not rows:
            continue
        cols = list(rows[0].keys())
        col_defs = ", ".join('"%s" TEXT' % c for c in cols)  # quoted: 'commit' is a reserved word
        con.execute(f"CREATE TABLE {csv_path.stem} ({col_defs})")
        con.executemany(f'INSERT INTO {csv_path.stem} VALUES ({", ".join("?" * len(cols))})',
                        [tuple(r[c] for c in cols) for r in rows])
    con.executescript(render(SEMANTIC.read_text(encoding="utf-8")))
    return con


def run_file(path: str | Path, con: sqlite3.Connection | None = None) -> list[list[dict]]:
    """Execute every statement in the file; return result sets of SELECT statements."""
    con = con or load_warehouse()
    con.row_factory = sqlite3.Row
    results = []
    sql = render(Path(path).read_text(encoding="utf-8"))
    for stmt in [s.strip() for s in sql.split(";")]:
        body = "\n".join(line for line in stmt.splitlines() if not line.strip().startswith("--")).strip()
        if not body:
            continue
        cur = con.execute(body)
        if cur.description:
            results.append([dict(r) for r in cur.fetchall()])
    return results


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else SEMANTIC
    for i, rs in enumerate(run_file(ROOT / path if not path.is_absolute() else path), 1):
        print(f"\n--- result set {i} ({len(rs)} rows) ---")
        print(table(rs[:25]))


if __name__ == "__main__":
    main()

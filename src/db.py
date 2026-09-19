"""DuckDB storage for computed curtailment."""

from __future__ import annotations

from pathlib import Path

import duckdb

DB_PATH = Path("data/curtailment.duckdb")


def connect() -> duckdb.DuckDBPyConnection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS curtailment (
            day        DATE,
            bm_unit    VARCHAR,
            lead_party VARCHAR,
            mwh        DOUBLE,
            PRIMARY KEY (day, bm_unit)
        )
        """
    )
    return con


def days_present(con) -> set[str]:
    """Days already computed, so a rerun skips them."""
    rows = con.execute("SELECT DISTINCT day FROM curtailment").fetchall()
    return {r[0].isoformat() for r in rows}


def replace_day(con, day: str, rows: list[tuple]) -> None:
    con.execute("DELETE FROM curtailment WHERE day = ?", [day])
    if rows:
        con.executemany("INSERT INTO curtailment VALUES (?, ?, ?, ?)", rows)

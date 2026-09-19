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
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS curtailment_period (
            day               DATE,
            settlement_period INTEGER,
            bm_unit           VARCHAR,
            lead_party        VARCHAR,
            mwh               DOUBLE,
            bid_gbp_per_mwh   DOUBLE,
            cost_gbp          DOUBLE,
            PRIMARY KEY (day, settlement_period, bm_unit)
        )
        """
    )
    # days with no curtailment at all, so averages aren't biased by
    # mistaking "absent" for "unknown"
    con.execute(
        "CREATE TABLE IF NOT EXISTS days_done (day DATE PRIMARY KEY)"
    )
    return con


def days_present(con) -> set[str]:
    rows = con.execute("SELECT DISTINCT day FROM curtailment").fetchall()
    return {r[0].isoformat() for r in rows}


def days_priced(con) -> set[str]:
    rows = con.execute("SELECT day FROM days_done").fetchall()
    return {r[0].isoformat() for r in rows}


def replace_day(con, day: str, rows: list[tuple]) -> None:
    con.execute("DELETE FROM curtailment WHERE day = ?", [day])
    if rows:
        con.executemany("INSERT INTO curtailment VALUES (?, ?, ?, ?)", rows)


def replace_day_priced(con, day: str, rows: list[tuple]) -> None:
    con.execute("DELETE FROM curtailment_period WHERE day = ?", [day])
    if rows:
        con.executemany(
            "INSERT INTO curtailment_period VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
    con.execute("INSERT OR REPLACE INTO days_done VALUES (?)", [day])

"""Export DuckDB tables to CSVs that live in the repo.

The daily job runs on stateless CI, so these CSVs are the persistent
record: append-only, diffable, and the dashboard's data source.
"""

from src.db import connect

con = connect()

con.execute("""
    COPY (
        SELECT day,
               round(sum(mwh), 1)      AS mwh,
               round(sum(cost_gbp), 0) AS cost_gbp,
               count(DISTINCT bm_unit) AS units
        FROM curtailment_period
        GROUP BY day ORDER BY day
    ) TO 'data/daily.csv' (HEADER, DELIMITER ',')
""")

con.execute("""
    COPY (
        SELECT day, bm_unit, lead_party,
               round(sum(mwh), 1)      AS mwh,
               round(sum(cost_gbp), 0) AS cost_gbp
        FROM curtailment_period
        GROUP BY day, bm_unit, lead_party ORDER BY day, bm_unit
    ) TO 'data/by_farm.csv' (HEADER, DELIMITER ',')
""")

for name in ("daily", "by_farm"):
    n = con.execute(f"SELECT count(*) FROM 'data/{name}.csv'").fetchone()[0]
    print(f"data/{name}.csv: {n:,} rows")

from src.db import connect
from src.elexon import fetch_boalf, wind_units

con = connect()

print(con.execute("""
    SELECT count(*) AS days,
           round(sum(daily)) AS total_mwh,
           round(avg(daily)) AS avg_daily_mwh,
           round(max(daily)) AS max_daily_mwh
    FROM (SELECT day, sum(mwh) AS daily FROM curtailment GROUP BY day)
""").fetchdf().to_string(index=False))

print("\ntop farms over the period:")
print(con.execute("""
    SELECT lead_party, round(sum(mwh)) AS mwh,
           round(100 * sum(mwh) / (SELECT sum(mwh) FROM curtailment), 1) AS pct
    FROM curtailment GROUP BY lead_party ORDER BY mwh DESC LIMIT 10
""").fetchdf().to_string(index=False))

print("\nchecking the zero days — were there really no instructions?")
units = wind_units()
for day in ["2026-08-16", "2026-08-23", "2026-09-13"]:
    records = fetch_boalf(f"{day}T00:00Z", f"{day}T23:59Z")
    wind = [r for r in records if r["bmUnit"] in units]
    print(f"  {day}: {len(records):,} acceptances total, {len(wind)} for wind")

"""Backfill curtailment over a date range into DuckDB.

Usage: python backfill.py 2026-08-01 2026-08-31

Elexon caps a physical-notification query at 7 days, so we walk the range
in weekly chunks: one plan request per unit per week, one instruction
request per day. Days already stored are skipped, so this is resumable.
"""

import sys
from collections import defaultdict
from datetime import date, timedelta

from src.curtailment import curtailment_mwh, parse_segments
from src.db import connect, days_present, replace_day
from src.elexon import fetch_boalf, fetch_pn, wind_units

CHUNK_DAYS = 7

start = date.fromisoformat(sys.argv[1])
end = date.fromisoformat(sys.argv[2])

con = connect()
done = days_present(con)
units = wind_units()
print(f"{len(units)} wind units; {len(done)} days already stored\n")

chunk_start = start
while chunk_start <= end:
    chunk_end = min(chunk_start + timedelta(days=CHUNK_DAYS - 1), end)
    days = [chunk_start + timedelta(days=i)
            for i in range((chunk_end - chunk_start).days + 1)]
    todo = [d for d in days if d.isoformat() not in done]

    if not todo:
        print(f"{chunk_start} to {chunk_end}: already stored, skipping")
        chunk_start = chunk_end + timedelta(days=1)
        continue

    # instructions, one request per day
    per_day = {}
    for day in todo:
        records = [r for r in fetch_boalf(f"{day}T00:00Z",
                                          f"{day + timedelta(days=1)}T00:00Z")
                   if r["bmUnit"] in units]
        grouped = defaultdict(list)
        for r in records:
            grouped[r["bmUnit"]].append(r)
        per_day[day] = grouped

    instructed = {u for g in per_day.values() for u in g}
    print(f"{chunk_start} to {chunk_end}: {len(instructed)} units instructed")

    # plans, one request per unit for the whole week
    plans = {}
    for i, unit in enumerate(sorted(instructed), 1):
        plans[unit] = parse_segments(
            fetch_pn(unit, f"{chunk_start}T00:00Z",
                     f"{chunk_end + timedelta(days=1)}T00:00Z"))
        print(f"\r  plans {i}/{len(instructed)}", end="", flush=True)
    print()

    for day, grouped in per_day.items():
        rows = []
        for unit, records in grouped.items():
            mwh = curtailment_mwh(plans[unit], parse_segments(records))
            if mwh > 0:
                rows.append((day.isoformat(), unit,
                             units[unit].get("leadPartyName"), mwh))
        replace_day(con, day.isoformat(), rows)
        total = sum(r[3] for r in rows)
        print(f"  {day}: {total:9,.0f} MWh across {len(rows)} units")

    chunk_start = chunk_end + timedelta(days=1)

print("\nstored:")
print(con.execute("""
    SELECT count(DISTINCT day) AS days,
           round(sum(mwh)) AS total_mwh,
           round(avg(daily), 0) AS avg_daily_mwh
    FROM curtailment,
         (SELECT sum(mwh) AS daily FROM curtailment GROUP BY day)
""").fetchdf().to_string(index=False))

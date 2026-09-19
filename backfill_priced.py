"""Backfill per-settlement-period curtailment and cost into DuckDB.

Usage: python backfill_priced.py 2025-09-19 2026-09-15

Elexon caps queries at 7 days, so we walk in weekly chunks: one plan and
one price request per unit per week, one instruction request per day.
Completed days are recorded in `days_done`, including days with nothing
curtailed, so reruns skip them and averages aren't biased by absent rows.
"""

import sys
import time
from collections import defaultdict
from datetime import date, timedelta

from src.curtailment import _parse_time, curtailment_mwh, parse_segments
from src.db import connect, days_priced, replace_day_priced
from src.elexon import fetch_boalf, fetch_bod, fetch_pn, wind_units

CHUNK_DAYS = 7

start = date.fromisoformat(sys.argv[1])
end = date.fromisoformat(sys.argv[2])

con = connect()
done = days_priced(con)
units = wind_units()
print(f"{len(units)} wind units; {len(done)} days already priced")
print(f"range: {start} to {end} ({(end - start).days + 1} days)\n")

began = time.time()
chunk_start = start

while chunk_start <= end:
    chunk_end = min(chunk_start + timedelta(days=CHUNK_DAYS - 1), end)
    days = [chunk_start + timedelta(days=i)
            for i in range((chunk_end - chunk_start).days + 1)]
    todo = [d for d in days if d.isoformat() not in done]

    if not todo:
        chunk_start = chunk_end + timedelta(days=1)
        continue

    per_day = {}
    for day in todo:
        records = [r for r in fetch_boalf(f"{day}T00:00Z",
                                          f"{day + timedelta(days=1)}T00:00Z")
                   if r["bmUnit"] in units]
        grouped = defaultdict(list)
        for r in records:
            grouped[r["bmUnit"]].append(r)
        per_day[day] = grouped

    instructed = sorted({u for g in per_day.values() for u in g})
    span_from = f"{chunk_start}T00:00Z"
    span_to = f"{chunk_end + timedelta(days=1)}T00:00Z"

    plans, prices = {}, {}
    for i, unit in enumerate(instructed, 1):
        plans[unit] = parse_segments(fetch_pn(unit, span_from, span_to))
        by_day = defaultdict(list)
        for b in fetch_bod(unit, span_from, span_to):
            if b["pairId"] == -1:
                by_day[b["settlementDate"]].append(b)
        prices[unit] = by_day
        print(f"\r  {chunk_start} to {chunk_end}: "
              f"fetching {i}/{len(instructed)}", end="", flush=True)

    for day, grouped in per_day.items():
        rows = []
        for unit, records in grouped.items():
            boal = parse_segments(records)
            for b in prices[unit].get(day.isoformat(), []):
                window = (_parse_time(b["timeFrom"]), _parse_time(b["timeTo"]))
                mwh = curtailment_mwh(plans[unit], boal, window=window)
                if mwh <= 0:
                    continue
                bid = b["bid"]
                cost = mwh * abs(bid) if bid < 0 else 0.0
                rows.append((day.isoformat(), b["settlementPeriod"], unit,
                             units[unit].get("leadPartyName"), mwh, bid, cost))
        replace_day_priced(con, day.isoformat(), rows)

    elapsed = (time.time() - began) / 60
    total = sum(r for r in [0])  # placeholder to keep line short
    print(f"\r  {chunk_start} to {chunk_end}: done "
          f"({len(instructed)} units, {elapsed:.1f} min elapsed)        ")

    chunk_start = chunk_end + timedelta(days=1)

print("\n" + con.execute("""
    SELECT count(DISTINCT day) AS days,
           round(sum(mwh)) AS total_mwh,
           round(sum(cost_gbp)) AS total_gbp,
           round(sum(cost_gbp) / sum(mwh), 2) AS gbp_per_mwh
    FROM curtailment_period
""").fetchdf().to_string(index=False))

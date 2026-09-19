"""Curtailment for every wind unit on one day.

Usage: python run_day.py 2026-09-16
"""

import sys
from collections import defaultdict
from datetime import date, timedelta

from src.curtailment import curtailment_mwh, parse_segments
from src.elexon import fetch_boalf, fetch_pn, wind_units

day = sys.argv[1] if len(sys.argv) > 1 else "2026-09-16"
start = f"{day}T00:00Z"
end = f"{date.fromisoformat(day) + timedelta(days=1)}T00:00Z"

print(f"curtailment for {day}\n")

units = wind_units()
print(f"{len(units)} wind units in the registry")

acceptances = fetch_boalf(start, end)
by_unit = defaultdict(list)
for record in acceptances:
    if record["bmUnit"] in units:
        by_unit[record["bmUnit"]].append(record)

print(f"{len(acceptances):,} acceptances, {len(by_unit)} wind units instructed")
print("fetching plans for each...\n")

results = []
for i, (unit, records) in enumerate(sorted(by_unit.items()), 1):
    pn = parse_segments(fetch_pn(unit, start, end))
    boal = parse_segments(records)
    mwh = curtailment_mwh(pn, boal)
    results.append((mwh, unit))
    print(f"  [{i}/{len(by_unit)}] {unit:<12} {mwh:8.1f} MWh", flush=True)

results.sort(reverse=True)
total = sum(mwh for mwh, _ in results)

print(f"\n{'':-<46}")
print(f"TOTAL CURTAILED: {total:,.0f} MWh\n")
print("worst offenders:")
for mwh, unit in results[:10]:
    name = units[unit].get("leadPartyName") or "?"
    print(f"  {mwh:8.1f} MWh  {unit:<12} {name}")

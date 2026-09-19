"""Are we double-counting, and how much is constraint-driven?"""

from collections import Counter, defaultdict
from datetime import date, timedelta

from src.curtailment import curtailment_mwh, parse_segments
from src.elexon import fetch_boalf, fetch_pn, wind_units

day = "2026-09-16"
start, end = f"{day}T00:00Z", f"{date.fromisoformat(day) + timedelta(days=1)}T00:00Z"

units = wind_units()
records = [r for r in fetch_boalf(start, end) if r["bmUnit"] in units]

print("amendmentFlag:", Counter(r["amendmentFlag"] for r in records).most_common())
print("soFlag:", Counter(r["soFlag"] for r in records).most_common())
print("deemedBoFlag:", Counter(r["deemedBoFlag"] for r in records).most_common())

by_unit = defaultdict(list)
for r in records:
    by_unit[r["bmUnit"]].append(r)

overlaps = 0
for unit, rs in by_unit.items():
    segs = sorted(parse_segments(rs), key=lambda s: s.start)
    for a, b in zip(segs, segs[1:]):
        if b.start < a.end:
            overlaps += 1
print(f"\noverlapping acceptance pairs: {overlaps}")

# recompute using only system-flagged instructions
so_only = defaultdict(list)
for r in records:
    if r["soFlag"]:
        so_only[r["bmUnit"]].append(r)

total = 0.0
for unit, rs in so_only.items():
    pn = parse_segments(fetch_pn(unit, start, end))
    total += curtailment_mwh(pn, parse_segments(rs))
print(f"soFlag-only total: {total:,.0f} MWh  (vs 28,795 counting everything)")

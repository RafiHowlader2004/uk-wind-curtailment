"""What did one day of curtailment cost, and at what rate?

Bid prices vary by settlement period, so volume is measured inside each
period's own time window — taken from the bid-offer records themselves,
which avoids deriving settlement periods from timestamps.
"""

import sys
from collections import defaultdict

import requests

from src.curtailment import curtailment_mwh, parse_segments, _parse_time
from src.elexon import BASE, fetch_boalf, fetch_pn, wind_units

day = sys.argv[1] if len(sys.argv) > 1 else "2026-09-04"
start, end = f"{day}T00:00Z", f"{day}T23:59Z"

units = wind_units()
records = [r for r in fetch_boalf(start, end) if r["bmUnit"] in units]
by_unit = defaultdict(list)
for r in records:
    by_unit[r["bmUnit"]].append(r)

print(f"{day}: {len(by_unit)} wind units instructed\n")

total_mwh = total_cost = 0.0
rows = []

for i, (unit, recs) in enumerate(sorted(by_unit.items()), 1):
    pn = parse_segments(fetch_pn(unit, start, end))
    boal = parse_segments(recs)

    bod = requests.get(f"{BASE}/balancing/bid-offer",
                       params={"bmUnit": unit, "from": start, "to": end},
                       timeout=60).json().get("data", [])
    bids = [b for b in bod if b["pairId"] == -1]

    unit_mwh = unit_cost = 0.0
    for b in bids:
        window = (_parse_time(b["timeFrom"]), _parse_time(b["timeTo"]))
        mwh = curtailment_mwh(pn, boal, window=window)
        if mwh <= 0:
            continue
        unit_mwh += mwh
        if b["bid"] < 0:
            unit_cost += mwh * abs(b["bid"])

    if unit_mwh > 0:
        rows.append((unit_cost, unit_mwh, unit, units[unit].get("leadPartyName")))
        total_mwh += unit_mwh
        total_cost += unit_cost
    print(f"\r  {i}/{len(by_unit)}", end="", flush=True)

rows.sort(reverse=True)
print(f"\n\n{'':-<60}")
print(f"{total_mwh:,.0f} MWh curtailed, costing £{total_cost:,.0f}")
print(f"implied average: £{total_cost / total_mwh:,.2f}/MWh\n")
print("most expensive:")
for cost, mwh, unit, party in rows[:8]:
    rate = cost / mwh if mwh else 0
    print(f"  £{cost:>10,.0f}  {mwh:>8,.0f} MWh  £{rate:>6.2f}/MWh  {unit:<12} {party}")

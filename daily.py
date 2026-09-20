"""Compute one day's curtailment and append it to the CSVs.

Runs on GitHub Actions with no database: a single day needs only that
day's instructions, plans and prices.

Defaults to two days ago. Elexon revises recent data, so yesterday can
still be incomplete when the job runs.
"""

import csv
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from src.curtailment import _parse_time, curtailment_mwh, parse_segments
from src.elexon import fetch_boalf, fetch_bod, fetch_pn, wind_units

DAILY = Path("data/daily.csv")
BY_FARM = Path("data/by_farm.csv")

day = (date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1
       else date.today() - timedelta(days=2))
key = day.isoformat()

if DAILY.exists() and key in DAILY.read_text():
    print(f"{key} already present, nothing to do")
    raise SystemExit(0)

start, end = f"{key}T00:00Z", f"{day + timedelta(days=1)}T00:00Z"
units = wind_units()

by_unit = defaultdict(list)
for r in fetch_boalf(start, end):
    if r["bmUnit"] in units:
        by_unit[r["bmUnit"]].append(r)

print(f"{key}: {len(by_unit)} wind units instructed")

farm_rows = []
for unit, records in sorted(by_unit.items()):
    pn = parse_segments(fetch_pn(unit, start, end))
    boal = parse_segments(records)
    mwh = cost = 0.0
    for b in fetch_bod(unit, start, end):
        if b["pairId"] != -1:
            continue
        window = (_parse_time(b["timeFrom"]), _parse_time(b["timeTo"]))
        period_mwh = curtailment_mwh(pn, boal, window=window)
        if period_mwh <= 0:
            continue
        mwh += period_mwh
        if b["bid"] < 0:
            cost += period_mwh * abs(b["bid"])
    if mwh > 0:
        farm_rows.append([key, unit, units[unit].get("leadPartyName"),
                          round(mwh, 1), round(cost)])

total_mwh = sum(r[3] for r in farm_rows)
total_cost = sum(r[4] for r in farm_rows)

DAILY.parent.mkdir(parents=True, exist_ok=True)
for path, header, rows in (
    (DAILY, ["day", "mwh", "cost_gbp", "units"],
     [[key, round(total_mwh, 1), round(total_cost), len(farm_rows)]]),
    (BY_FARM, ["day", "bm_unit", "lead_party", "mwh", "cost_gbp"], farm_rows),
):
    new_file = not path.exists()
    with path.open("a", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(header)
        w.writerows(rows)

print(f"{key}: {total_mwh:,.0f} MWh, £{total_cost:,.0f}")

"""What do wind bid prices actually look like?"""

import requests
from collections import Counter

B = "https://data.elexon.co.uk/bmrs/api/v1"
UNITS = ["T_MOWEO-3", "T_SGRWO-1", "T_VKNGW-2", "T_MOWWO-1"]

all_bids = []
for unit in UNITS:
    r = requests.get(f"{B}/balancing/bid-offer",
                     params={"bmUnit": unit,
                             "from": "2026-09-04T00:00Z",
                             "to": "2026-09-04T12:00Z"}, timeout=60)
    rows = r.json().get("data", [])
    print(f"\n{unit}: {len(rows)} rows")
    print("  pairIds:", Counter(x["pairId"] for x in rows).most_common())
    for x in rows[:4]:
        print(f"    SP{x['settlementPeriod']:>3} pair{x['pairId']:>3}  "
              f"level {x['levelFrom']:>6} -> {x['levelTo']:>6}   "
              f"bid {x['bid']:>8}   offer {x['offer']:>8}")
    all_bids += [(x["pairId"], x["bid"]) for x in rows]

print("\nbid prices by pairId:")
by_pair = {}
for pair, bid in all_bids:
    by_pair.setdefault(pair, []).append(bid)
for pair in sorted(by_pair):
    vals = by_pair[pair]
    print(f"  pair {pair:>3}: n={len(vals):>3}  "
          f"min {min(vals):>8.2f}  max {max(vals):>8.2f}  "
          f"negative: {sum(1 for v in vals if v < 0)}")

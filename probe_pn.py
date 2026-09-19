import requests, json

BASE = "https://data.elexon.co.uk/bmrs/api/v1"
unit = "T_VKNGW-2"

r = requests.get(f"{BASE}/balancing/physical",
                 params={"bmUnit": unit, "dataset": "PN",
                         "from": "2026-09-16T00:00Z", "to": "2026-09-16T06:00Z"},
                 timeout=60)
print("status:", r.status_code)
d = r.json()
rows = d.get("data", d) if isinstance(d, dict) else d
print("rows:", len(rows))
if rows:
    print(json.dumps(rows[0], indent=2))
    print("\nnext few:")
    for x in rows[1:6]:
        print(f"  {x.get('timeFrom')} -> {x.get('timeTo')}  "
              f"{x.get('levelFrom')} -> {x.get('levelTo')} MW")

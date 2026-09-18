import json, collections, requests

def load(path):
    d = json.load(open(path))
    return d["data"] if isinstance(d, dict) and "data" in d else d

units = load("bmunits.json")
by_id = {u["elexonBmUnit"]: u for u in units if u.get("elexonBmUnit")}

boalf = load("boalf.json")
ids = {r["bmUnit"] for r in boalf}
matched = ids & set(by_id)
print(f"units instructed in that hour: {len(ids)}, found in registry: {len(matched)}")
print("their fuel types:", collections.Counter(
    by_id[i].get("fuelType") for i in matched).most_common())
print("not in registry:", sorted(ids - matched)[:8])

print("\nfetching a full day...")
r = requests.get("https://data.elexon.co.uk/bmrs/api/v1/datasets/BOALF",
                 params={"from": "2026-09-16T00:00Z", "to": "2026-09-17T00:00Z",
                         "format": "json"}, timeout=120)
day = r.json()["data"]
wind_day = [x for x in day if by_id.get(x["bmUnit"], {}).get("fuelType") == "WIND"]
print(f"acceptances that day: {len(day):,}, wind: {len(wind_day):,}")
print("most-instructed wind units:")
for u, n in collections.Counter(x["bmUnit"] for x in wind_day).most_common(5):
    print(f"  {n:>4}  {u}  ({by_id[u].get('leadPartyName')})")

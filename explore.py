import json, collections

def load(path):
    d = json.load(open(path))
    return d["data"] if isinstance(d, dict) and "data" in d else d

def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0

units = load("bmunits.json")
wind_units = [u for u in units if u.get("fuelType") == "WIND"]
wind = {u["elexonBmUnit"] for u in wind_units}
cap = sum(num(u.get("generationCapacity")) for u in wind_units)
print(f"wind units: {len(wind)}, total capacity: {cap:,.0f} MW")

boalf = load("boalf.json")
wind_acc = [r for r in boalf if r["bmUnit"] in wind]
print(f"acceptances this hour: {len(boalf)}, wind: {len(wind_acc)}")

for r in wind_acc[:5]:
    print(f"  {r['bmUnit']:<12} {r['timeFrom'][11:16]}-{r['timeTo'][11:16]}  "
          f"{r['levelFrom']:>6} -> {r['levelTo']:>6} MW   soFlag={r['soFlag']}")

owners = collections.Counter(u["leadPartyName"] for u in wind_units)
print("\ntop wind operators:")
for name, n in owners.most_common(6):
    print(f"  {n:>3}  {name}")

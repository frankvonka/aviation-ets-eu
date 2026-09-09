"""Understand 2013+ divergence between '1. Total allocated' and '1.1 Freely allocated'."""
import csv
from collections import defaultdict

rows = list(csv.DictReader(open("/root/aviation-emissions/data/_eea_ets_aviation_raw.csv")))
# find (year, country) where total_alloc != free, show raw labels
piv = defaultdict(dict)
for r in rows:
    try:
        v = float(r["value"])
    except (TypeError, ValueError):
        continue
    piv[(r["year"], r["country_code"])][r["citl_information"]] = piv[(r["year"], r["country_code"])].get(r["citl_information"], 0) + v

for (y, cc), d in sorted(piv.items()):
    if y in ("2013", "2014", "2016", "2021") and "1. Total allocated allowances (EUA or EUAA)" in d:
        t = d["1. Total allocated allowances (EUA or EUAA)"]
        f = d.get("1.1 Freely allocated allowances", 0.0)
        if abs(t - f) > 1:
            print(y, cc, f"total={t:,.0f} free={f:,.0f} diff={t-f:,.0f}")
            for k in sorted(d):
                if k.startswith("1."):
                    print(f"    {k!r} = {d[k]:,.0f}")

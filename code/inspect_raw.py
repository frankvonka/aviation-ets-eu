"""Inspect the raw EEA EU ETS aviation extract: column structure and DE 2012 rows."""
import csv

rows = list(csv.DictReader(open("/root/aviation-emissions/data/_eea_ets_aviation_raw.csv")))
print("rows:", len(rows))
print("columns:", list(rows[0].keys()))
# distinct labels
from collections import Counter
labels = Counter(r["citl_information"] for r in rows)
print("\nlabels:")
for k, v in labels.most_common():
    print(f"  {v:>5}  {k!r}")
# DE 2012 rows
print("\nDE 2012 rows:")
for r in rows:
    if r.get("country_code") == "DE" and r.get("year") == "2012":
        print("  ", r)
# countries & years
cys = sorted({(r["year"], r["country_code"]) for r in rows})
print("\nyear x country combos:", len(cys))
print("years:", sorted({c[0] for c in cys}))
print("countries:", sorted({c[1] for c in cys}))

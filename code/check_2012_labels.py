"""Check 2012 aviation free-allocation anomaly: likely both 2012 and period totals mixed,
or 'free' includes Art.10a rows. Inspect a single country's raw 2012 labels."""
import csv
from collections import defaultdict

rows = list(csv.DictReader(open("/root/aviation-emissions/data/_eea_ets_aviation_raw.csv")))
agg = defaultdict(list)
for r in rows:
    if r["country_code"] == "DE" and r["year"] == "2012":
        agg[r["citl_information"]].append(r["value"])
    if r["country_code"] == "DE" and r["year"] == "2013":
        agg["2013_" + r["citl_information"]].append(r["value"])
for k, v in sorted(agg.items()):
    print(f"{k!r}: {v}")

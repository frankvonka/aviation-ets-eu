"""List all distinct labels in 2019/2020/2021 aviation rows to find extra correction rows."""
import csv
from collections import defaultdict

rows = list(csv.DictReader(open("/root/aviation-emissions/data/_eea_ets_aviation_raw.csv")))
seen = defaultdict(set)
for r in rows:
    seen[r["year"]].add(r["citl_information"])
for y in ("2019", "2020", "2021", "2017"):
    print(y)
    for lab in sorted(seen[y]):
        print("   ", lab)

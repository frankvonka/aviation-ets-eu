"""Final identity check: free = Total - auctioned must equal
   (1.1 - 1.1.4 Swiss + 1.2 corrections)  [2012-2019, Swiss CHU n/a]
or (1.1 + 1.2 corrections)               [2020-2021, Swiss CHU included in 1.1]
"""
import csv
from collections import defaultdict, Counter

rows = list(csv.DictReader(open("/root/aviation-emissions/data/_eea_ets_aviation_raw.csv")))
pivot = defaultdict(dict)
for r in rows:
    cc = r["country_code"]
    if len(cc) != 2:
        continue
    try:
        v = float(r["value"])
    except (TypeError, ValueError):
        continue
    pivot[(r["year"], cc)][r["citl_information"]] = pivot[(r["year"], cc)].get(r["citl_information"], 0.0) + v

L_TOT = "1. Total allocated allowances (EUA or EUAA)"
L_AUC = "1.3 Allowances auctioned or sold (EUAs and EUAAs)"
L_11 = "1.1 Freely allocated allowances"
L_12 = "1.2 Correction to freely allocated allowances (not reflected in EUTL)"
L_114 = "1.1.4 Swiss Free Allocated allowances for aircraft operators"

ok, bad = Counter(), []
for (y, cc), d in sorted(pivot.items()):
    if L_TOT not in d or L_11 not in d:
        continue
    free = d[L_TOT] - d.get(L_AUC, 0.0)
    base = d[L_11] + d.get(L_12, 0.0)
    if abs(free - base) <= 1.0:
        ok["free=1.1+1.2"] += 1
    elif abs(free - (base - d.get(L_114, 0.0))) <= 1.0:
        ok["free=1.1-1.1.4+1.2"] += 1
    else:
        bad.append((y, cc, free, base, base - d.get(L_114, 0.0)))

print(ok, "| violations:", len(bad))
for v in bad:
    print("   ", v)

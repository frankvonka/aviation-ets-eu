"""Rebuild eutl_aviation.csv with corrected identities:
- verified_tco2 = 2. Verified emissions (EUTL total; equals 2.1 + 2.2 in 2020-21)
- free_allocation_tco2 = Total allocated - auctioned (Swiss CHU-covered free allocation excluded;
   free = 1.1 - 1.1.4 Swiss + 1.2 corrections; identity verified)
"""
import csv
from collections import defaultdict

RAW = "/root/aviation-emissions/data/_eea_ets_aviation_raw.csv"
OUT = "/root/aviation-emissions/data/eutl_aviation.csv"

rows = list(csv.DictReader(open(RAW)))
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

YEARS = [str(y) for y in range(2012, 2022)]
L_TOT = "1. Total allocated allowances (EUA or EUAA)"
L_AUC = "1.3 Allowances auctioned or sold (EUAs and EUAAs)"
L_VER2 = "2. Verified emissions"
L_11 = "1.1 Freely allocated allowances"
L_12 = "1.2 Correction to freely allocated allowances (not reflected in EUTL)"
L_114 = "1.1.4 Swiss Free Allocated allowances for aircraft operators"

out_rows, bad = [], []
for (y, cc), d in sorted(pivot.items()):
    if y not in YEARS or L_TOT not in d:
        continue
    free = d[L_TOT] - d.get(L_AUC, 0.0)
    ver = d.get(L_VER2)
    if ver is None:
        print(f"WARNING no verified emissions: {y} {cc}")
        continue
    if L_11 in d:
        expect = d[L_11] - d.get(L_114, 0.0) + d.get(L_12, 0.0)
        if abs(expect - free) > 1.0:
            bad.append((y, cc, free, expect))
    out_rows.append({
        "year": int(y),
        "member_state": cc,
        "verified_tco2": round(ver, 3),
        "free_allocation_tco2": round(free, 3),
        "source": "EEA EU ETS database v02 (Union Registry/EUTL extract), main_activity=10-aviation",
    })

print("rows:", len(out_rows), "| identity violations:", len(bad))
for v in bad[:10]:
    print("   ", v)

with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["year", "member_state", "verified_tco2", "free_allocation_tco2", "source"])
    w.writeheader()
    w.writerows(out_rows)
print("wrote", OUT, "| countries:", sorted({r['member_state'] for r in out_rows}))

by_year = defaultdict(lambda: [0.0, 0.0])
for r in out_rows:
    by_year[r["year"]][0] += r["verified_tco2"]
    by_year[r["year"]][1] += r["free_allocation_tco2"]
print(f"\n{'year':<6}{'EU verified tCO2':>18}{'EU free alloc tCO2':>20}")
for y in sorted(by_year):
    v, f_ = by_year[y]
    print(f"{y:<6}{v:>18,.0f}{f_:>20,.0f}")

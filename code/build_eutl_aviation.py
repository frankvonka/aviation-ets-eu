"""Build eutl_aviation.csv: per member state x year 2012-2021 aviation verified emissions
and free allocation from the EEA EU ETS database (Union Registry extract).

verified_tco2        <- '2.1 EU-ETS Verified Emission' (tCO2e)
free_allocation_tco2 <- '1. Total allocated allowances (EUA or EUAA)'
                        minus '1.3 Allowances auctioned or sold'
   (equals 1.1 freely allocated + 1.2 corrections + 1.1.2 NER + 1.1.4 Swiss free allocation;
    verified by identity check on every (year, country) pair)
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
LABEL_TOTAL = "1. Total allocated allowances (EUA or EUAA)"
LABEL_AUCT = "1.3 Allowances auctioned or sold (EUAs and EUAAs)"
LABEL_VER = "2.1 EU-ETS Verified Emission"

out_rows = []
id_violations = []
for (y, cc), d in sorted(pivot.items()):
    if y not in YEARS:
        continue
    total = d.get(LABEL_TOTAL)
    auct = d.get(LABEL_AUCT, 0.0)
    ver = d.get(LABEL_VER)
    if total is None or ver is None:
        print(f"WARNING missing primary metric: {y} {cc}: {sorted(d)}")
        continue
    free = total - auct
    # verify free == sum of free components where all present
    comps = d.get("1.1 Freely allocated allowances", None)
    if comps is not None:
        expect = comps + d.get("1.2 Correction to freely allocated allowances (not reflected in EUTL)", 0.0) \
                 + d.get("1.1.2 Free allocation from the new entrants reserve (Art. 10a(7))", 0.0) \
                 + d.get("1.1.4 Swiss Free Allocated allowances for aircraft operators", 0.0)
        if abs(expect - free) > 1.0:
            id_violations.append((y, cc, free, expect))
    out_rows.append({
        "year": int(y),
        "member_state": cc,
        "verified_tco2": round(ver, 3),
        "free_allocation_tco2": round(free, 3),
        "source": "EEA EU ETS database (Union Registry/EUTL extract), v81, main_activity=10-aviation",
    })

print("rows:", len(out_rows), "| free-allocation identity violations:", len(id_violations))
for v in id_violations[:10]:
    print("   ", v)

with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["year", "member_state", "verified_tco2", "free_allocation_tco2", "source"])
    w.writeheader()
    w.writerows(out_rows)
print("wrote", OUT)

# sanity totals
by_year = defaultdict(lambda: [0.0, 0.0])
for r in out_rows:
    by_year[r["year"]][0] += r["verified_tco2"]
    by_year[r["year"]][1] += r["free_allocation_tco2"]
print(f"\n{'year':<6}{'EU verified tCO2':>18}{'EU free alloc tCO2':>20}")
for y in sorted(by_year):
    v, f_ = by_year[y]
    print(f"{y:<6}{v:>18,.0f}{f_:>20,.0f}")

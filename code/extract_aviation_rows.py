"""Extract aviation (main_activity_code=10) rows for 2012-2021 from the EEA ETS database."""
import openpyxl, csv
from collections import Counter

wb = openpyxl.load_workbook("/root/aviation-emissions/data/ETS_Database_July_2026.xlsx", read_only=True)
ws = wb["Sheet1"]

HEADER = None
rows_out = []
info_counter = Counter()
av_years = Counter()
n = 0
for row in ws.iter_rows(min_row=2, values_only=True):
    n += 1
    version, cc, act, active, info, year, size, value, unit = row
    info_counter[str(info)] += 1
    if str(act) == "10":  # aviation
        av_years[str(year)] += 1
        if isinstance(year, (int, float)) and 2012 <= int(year) <= 2021:
            rows_out.append([int(year), cc, str(info).strip(), value, unit, version])

print("total data rows:", n)
print("\nall citl_information labels:")
for k, v in info_counter.most_common():
    print(f"  {v:>7}  {k!r}")
print("\naviation (act=10) year coverage:")
for k, v in sorted(av_years.items()):
    print(f"  {k}: {v}")
print("\naviation rows 2012-2021:", len(rows_out))
print("sample:", rows_out[:8])

with open("/root/aviation-emissions/data/_eea_ets_aviation_raw.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["year", "country_code", "citl_information", "value", "unit", "version"])
    w.writerows(rows_out)
wb.close()

"""Show full 2020 AT raw rows (every value) to reconcile the 84,847 gap."""
import csv

rows = list(csv.DictReader(open("/root/aviation-emissions/data/_eea_ets_aviation_raw.csv")))
for r in rows:
    if r["year"] == "2020" and r["country_code"] == "AT":
        print(f"{r['citl_information'][:75]:<77} {float(r['value']):>15,.3f}  [{r['unit']}]")

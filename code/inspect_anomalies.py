"""Inspect EE/IS 2017 raw rows, GB 2021, EE/SI/SK 2020; extract background-note PDF text on aviation."""
import csv
from collections import defaultdict

rows = list(csv.DictReader(open("/root/aviation-emissions/data/_eea_ets_aviation_raw.csv")))
def show(pred, title):
    print(f"--- {title}")
    for r in rows:
        if pred(r):
            print(f"   {r['citl_information'][:70]:<72} {float(r['value']):>15,.1f}  [{r['unit'][:18]}]")

show(lambda r: r["year"]=="2017" and r["country_code"]=="EE", "EE 2017")
show(lambda r: r["year"]=="2017" and r["country_code"]=="IS", "IS 2017")
show(lambda r: r["year"]=="2020" and r["country_code"]=="EE", "EE 2020")
show(lambda r: r["year"]=="2021" and r["country_code"]=="GB", "GB 2021")
show(lambda r: r["year"]=="2012" and r["country_code"]=="AT", "AT 2012")
show(lambda r: r["year"]=="2013" and r["country_code"]=="AT", "AT 2013")

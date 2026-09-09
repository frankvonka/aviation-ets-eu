#!/usr/bin/env python3
"""(a) verify partial CSV subset of parquet-derived CSV; (b) hunt the state-xlsx."""
import json, subprocess, time, os

UA = "Mozilla/5.0 (compatible; aviation-data-research/1.0)"
D = "/root/aviation-emissions/data"

def curl(url, timeout=90):
    p = subprocess.run(["curl", "-sL", "--max-time", str(timeout), "-A", UA,
                        "-w", "\n__HTTP__:%{http_code}", url], capture_output=True, text=True)
    if "__HTTP__:" in p.stdout:
        body, code = p.stdout.rsplit("\n__HTTP__:", 1)
        return code.strip(), body
    return "ERR", p.stderr[:200]

# ---------- (a) subset verification via pyarrow ----------
code = f'''
import csv, pyarrow.parquet as pq
new = open("{D}/g2g_emissions.csv").read()
old = open("{D}/g2g_emissions_recovered.csv").read().splitlines()
miss = [l for l in old if l not in new and not l.startswith("LEVEL")]
print("old lines:", len(old), "| missing from new CSV:", len(miss))
print(miss[:3])
'''
r = subprocess.run(["/root/aviation-emissions/.venv/bin/python", "-c", code],
                   capture_output=True, text=True)
print("=== subset check ===\n", r.stdout, r.stderr[-300:] if r.returncode else "")

# ---------- (b) CDX hunts ----------
def cdx(q, name):
    for attempt in (1, 2, 3):
        c, b = curl(f"http://web.archive.org/cdx/search/cdx?{q}&output=json")
        if c == "200" and b.strip().startswith("["):
            try:
                rows = json.loads(b)[1:]
                print(f"=== {name}: {len(rows)} ===")
                for x in rows[:80]:
                    print("  ", x)
                return rows
            except json.JSONDecodeError:
                pass
        print(f"--- {name} try{attempt} http={c} len={len(b)}")
        time.sleep(20)
    return []

h = {}
h["latest_month_all"] = cdx(
    "url=eurocontrol.int/datasets/our-data-emissions-latest-month.csv&fl=timestamp,statuscode,mimetype,length", "latest_month_all")
h["our_data_all"] = cdx(
    "url=eurocontrol.int/datasets/our-data-emissions.csv&fl=timestamp,statuscode,mimetype,length", "our_data_all")
h["state_xlsx"] = cdx(
    "url=eurocontrol.int&matchType=domain&filter=original:.*(emissions_by_state|small.?emitter).*&filter=statuscode:200&fl=timestamp,original,mimetype,length&limit=50", "state_xlsx")
h["datasets_prefix"] = cdx(
    "url=eurocontrol.int/datasets/&matchType=prefix&filter=statuscode:200&collapse=urlkey&fl=timestamp,original,mimetype&limit=200", "datasets_prefix")

json.dump(h, open(f"{D}/.cdx_hunt2.json", "w"), indent=2)

# ---------- (c) Memento timetravel for the xlsx ----------
c, b = curl("http://timetravel.mementoweb.org/api/json/2024/https://www.eurocontrol.int/performance/data/download/xls/CO2_emissions_by_state.xlsx", 60)
print("\n=== timetravel http=", c, " len=", len(b))
print(b[:1500])

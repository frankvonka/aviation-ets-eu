#!/usr/bin/env python3
"""Search the archived EUROCONTROL download tree for CO2/emissions/state files."""
import json, subprocess, time, sys, urllib.parse

UA = "Mozilla/5.0 (compatible; aviation-data-research/1.0)"
OUT = "/root/aviation-emissions/data/.cdx_hits"

def curl(url, timeout=90):
    p = subprocess.run(["curl", "-sL", "--max-time", str(timeout), "-A", UA,
                        "-w", "\n__HTTP__:%{http_code}", url],
                       capture_output=True, text=True)
    if "__HTTP__:" in p.stdout:
        body, code = p.stdout.rsplit("\n__HTTP__:", 1)
        return code.strip(), body
    return "ERR", p.stderr[:200]

SEARCHES = [
    ("csv_tree_all", "url=eurocontrol.int/performance/data/download/csv/&matchType=prefix&filter=statuscode:200&fl=timestamp,original,mimetype,length&limit=500"),
    ("xls_tree_all", "url=eurocontrol.int/performance/data/download/xls/&matchType=prefix&filter=statuscode:200&fl=timestamp,original,mimetype,length&limit=200"),
    ("co2_regex",    "url=eurocontrol.int&matchType=domain&filter=original:.*(co2|emission).*&filter=statuscode:200&collapse=urlkey&fl=timestamp,original,mimetype,length&limit=100"),
    ("state_regex",  "url=eurocontrol.int&matchType=domain&filter=original:.*state.*xlsx.*&filter=statuscode:200&fl=timestamp,original,mimetype,length&limit=50"),
]

hits = {}
for name, q in SEARCHES:
    url = f"http://web.archive.org/cdx/search/cdx?{q}&output=json"
    for attempt in (1, 2, 3):
        code, body = curl(url)
        print(f"--- {name} try{attempt} http={code} len={len(body)}", flush=True)
        if code == "200" and body.strip().startswith("["):
            try:
                rows = json.loads(body)
                hits[name] = rows[1:]
                print(f"    {len(rows)-1} rows")
                break
            except json.JSONDecodeError as e:
                print("    json err:", e, body[:200])
        time.sleep(20)
    time.sleep(5)

with open(OUT + ".json", "w") as f:
    json.dump(hits, f, indent=2)

for name, rows in hits.items():
    print(f"\n===== {name} ({len(rows)}) =====")
    for r in rows:
        print(" ", r)

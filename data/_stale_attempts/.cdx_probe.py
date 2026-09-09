#!/usr/bin/env python3
"""Probe Wayback CDX for URL variants / prefix matches of the targets."""
import json, subprocess, time

UA = "Mozilla/5.0 (compatible; aviation-data-research/1.0)"
QUERIES = [
    # prefix sweep over the whole download tree
    "eurocontrol.int/performance/data/download/&matchType=prefix&filter=statuscode:200&collapse=urlkey&fl=timestamp,original,statuscode,mimetype,length&limit=200",
    # www variant
    "www.eurocontrol.int/performance/data/download/csv/g2g_emissions.csv&fl=timestamp,statuscode,mimetype,length",
    # older performance site layout (sai / prudev paths seen on old EUROCONTROL)
    "eurocontrol.int/performance&matchType=prefix&filter=statuscode:200&collapse=urlkey&fl=timestamp,original,mimetype&limit=100",
]

def curl(url, timeout=60):
    p = subprocess.run(["curl", "-sL", "--max-time", str(timeout), "-A", UA,
                        "-w", "\n__HTTP__:%{http_code}", url],
                       capture_output=True, text=True)
    if "__HTTP__:" in p.stdout:
        body, code = p.stdout.rsplit("\n__HTTP__:", 1)
        return code.strip(), body
    return "ERR", p.stderr[:200]

for i, q in enumerate(QUERIES):
    url = f"http://web.archive.org/cdx/search/cdx?url={q}&output=json"
    for attempt in (1, 2, 3):
        code, body = curl(url)
        print(f"--- Q{i} try{attempt} http={code} len={len(body)}", flush=True)
        if code == "200" and body.strip().startswith("["):
            try:
                rows = json.loads(body)
                print(f"    {max(0, len(rows)-1)} captures")
                for r in rows[1:60]:
                    print("   ", r)
                break
            except json.JSONDecodeError as e:
                print("    json err", e)
        if code == "ERR":
            print("   ", body)
        time.sleep(15)
    time.sleep(3)

#!/usr/bin/env python3
"""Step 1: discover Wayback snapshots for the two EUROCONTROL targets."""
import json, subprocess, time, sys

UA = "Mozilla/5.0 (compatible; aviation-data-research/1.0; contact: researcher)"
TARGETS = {
    "g2g": "eurocontrol.int/performance/data/download/csv/g2g_emissions.csv",
    "state": "eurocontrol.int/performance/data/download/xls/CO2_emissions_by_state.xlsx",
}

def curl(url, timeout=45):
    cmd = ["curl", "-sL", "--max-time", str(timeout), "-A", UA,
           "-w", "\n__HTTP__:%{http_code}", url]
    p = subprocess.run(cmd, capture_output=True, text=True)
    out = p.stdout
    if "__HTTP__:" in out:
        body, code = out.rsplit("\n__HTTP__:", 1)
        return code.strip(), body
    return "ERR", p.stderr.strip()[:300]

results = {}
for key, url in TARGETS.items():
    # --- available API, up to 4 tries spaced 30s ---
    avail = None
    for attempt in range(1, 5):
        code, body = curl(f"http://archive.org/wayback/available?url={url}")
        print(f"[avail] {key} try{attempt} http={code} len={len(body)}", flush=True)
        if code == "200" and body.strip().startswith("{"):
            try:
                j = json.loads(body)
                snap = j.get("archived_snapshots", {}).get("closest")
                if snap:
                    avail = snap
                    break
                print(f"[avail] {key}: 200 but no snapshot", flush=True)
                break
            except json.JSONDecodeError:
                pass
        time.sleep(30)

    # --- CDX API, up to 3 tries ---
    cdx = None
    for attempt in range(1, 4):
        code, body = curl(
            f"http://web.archive.org/cdx/search/cdx?url={url}&output=json"
            f"&fl=timestamp,statuscode,mimetype,length&limit=-15")
        print(f"[cdx] {key} try{attempt} http={code} len={len(body)}", flush=True)
        if code == "200" and body.strip().startswith("["):
            try:
                rows = json.loads(body)
                if len(rows) > 1:
                    cdx = rows[1:]
                    break
                print(f"[cdx] {key}: empty index", flush=True)
                break
            except json.JSONDecodeError:
                pass
        time.sleep(20)

    results[key] = {"available": avail, "cdx": cdx}
    print(f"== {key}: avail={avail} cdx_rows={len(cdx) if cdx else 0}", flush=True)

with open("/root/aviation-emissions/data/.wayback_discovery.json", "w") as f:
    json.dump(results, f, indent=2)
print(json.dumps(results, indent=2))

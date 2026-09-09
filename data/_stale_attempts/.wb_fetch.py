#!/usr/bin/env python3
"""Download archived EUROCONTROL emissions files (id_ raw form) and validate."""
import json, subprocess, time, os

UA = "Mozilla/5.0 (compatible; aviation-data-research/1.0)"
D = "/root/aviation-emissions/data"
os.chdir(D)

FETCH = [
    # (out, web.archive.org URL)
    ("g2g_emissions.parquet",
     "https://web.archive.org/web/20250814084639id_/https://www.eurocontrol.int/performance/data/download/parquet/g2g_emissions.parquet"),
    ("mom_co2.csv",
     "https://web.archive.org/web/20260209140521id_/https://www.eurocontrol.int/performance/data/download/csv/mom_co2.csv"),
    ("our-data-emissions-latest-month.csv",
     "https://web.archive.org/web/20250819194609id_/https://www.eurocontrol.int/datasets/our-data-emissions-latest-month.csv"),
    ("our-data-emissions.csv",
     "https://web.archive.org/web/20230504124650id_/https://www.eurocontrol.int/datasets/our-data-emissions.csv"),
]

for out, url in FETCH:
    ok = False
    for attempt in (1, 2, 3):
        p = subprocess.run(["curl", "-sL", "--max-time", "240", "-A", UA,
                            "-o", out, "-w", "%{http_code} %{size_download}", url],
                           capture_output=True, text=True)
        print(f"{out} try{attempt}: http/size={p.stdout}", flush=True)
        sz = os.path.getsize(out) if os.path.exists(out) else 0
        if p.stdout.startswith("200") and sz > 500:
            ok = True
            break
        time.sleep(25)
    print(f"  -> {out}: {os.path.getsize(out) if os.path.exists(out) else 0} bytes, ok={ok}", flush=True)
    time.sleep(5)

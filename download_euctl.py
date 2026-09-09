"""Download EUROCONTROL emissions files bypassing Cloudflare via cloudscraper."""
import cloudscraper, sys
from pathlib import Path

DATA = Path("/root/aviation-emissions/data")
FILES = {
    "g2g_emissions.csv": "https://www.eurocontrol.int/performance/data/download/csv/g2g_emissions.csv",
    "CO2_emissions_by_state.xlsx": "https://www.eurocontrol.int/performance/data/download/xls/CO2_emissions_by_state.xlsx",
    "g2g_emissions.parquet": "https://www.eurocontrol.int/performance/data/download/parquet/g2g_emissions.parquet",
}

s = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "mobile": False},
    delay=10
)

for name, url in FILES.items():
    try:
        r = s.get(url, timeout=120)
        ok = not r.content[:50].lower().startswith(b"<!doctype html") and b"Cloudflare" not in r.content[:2000]
        print(f"{name}: HTTP {r.status_code}, {len(r.content):,} bytes, valid={'YES' if ok else 'NO'}", flush=True)
        if ok and r.status_code == 200 and len(r.content) > 10000:
            (DATA / name).write_bytes(r.content)
            print(f"  saved -> {name}", flush=True)
    except Exception as e:
        print(f"{name}: ERROR {str(e)[:200]}", flush=True)

"""Probe EEA datahub API + discomap endpoints for EU ETS dataset structure."""
import requests, json, sys

s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64) research-script"
TIMEOUT = 30

urls = [
    # EEA datahub API variants
    ("datahub-api", "https://www.eea.europa.eu/api/datahub/datahubitem-view/98f04097-26de-4fca-86c4-63834818c0c0"),
    ("datahub-api2", "https://sdi.eea.europa.eu/catalogue/srv/api/records/98f04097-26de-4fca-86c4-63834818c0c0"),
    # discomap datamart known patterns
    ("discomap-root", "https://discomap.eea.europa.eu/App/AirQualityStatistics/index.html"),
    ("eea-sdi", "https://sdi.eea.europa.eu/catalogue/search?queryText=EU%20ETS"),
]

for name, url in urls:
    try:
        r = s.get(url, timeout=TIMEOUT, allow_redirects=True)
        ct = r.headers.get("content-type", "")
        print(f"== {name}: HTTP {r.status_code} ct={ct[:60]} len={len(r.content)} final={r.url[:120]}")
        if r.status_code == 200 and ("json" in ct or "text" in ct):
            txt = r.text[:1500]
            print(txt)
        print()
    except Exception as e:
        print(f"== {name}: ERROR {type(e).__name__}: {str(e)[:200]}\n")
        sys.stdout.flush()

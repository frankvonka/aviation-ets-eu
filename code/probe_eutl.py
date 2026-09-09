"""Probe EUTL public web interface + fetch euets-scraper source to find EEA datahub API."""
import requests

s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
s.headers["Accept-Language"] = "en"

# 1) EUTL main page
try:
    r = s.get("https://ec.europa.eu/clima/ets/", timeout=40)
    print("EUTL root:", r.status_code, len(r.content), r.url)
    txt = r.text
    import re
    links = sorted(set(re.findall(r'href="([^"]+\.do[^"]*)"', txt)))
    print(" .do links:", links[:20])
    frames = re.findall(r'src="([^"]+)"', txt)
    print(" frames/srcs:", frames[:20])
except Exception as e:
    print("EUTL root ERR:", type(e).__name__, str(e)[:200])

# 2) euets-scraper source: find datahub API endpoint
for path in ["main/README.md", "master/README.md"]:
    try:
        r = s.get(f"https://raw.githubusercontent.com/vegardege/euets-scraper/{path}", timeout=30)
        if r.status_code == 200:
            print(f"\n=== euets-scraper {path}: {len(r.content)} bytes")
            print(r.text[:2500])
            break
    except Exception as e:
        print("readme ERR", str(e)[:100])

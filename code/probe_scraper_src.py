"""Read scraper.py + archive.py from euets-scraper to learn the EEA datahub API."""
import requests

s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0"
for p in ["src/euets_scraper/scraper.py", "src/euets_scraper/archive.py"]:
    r = s.get(f"https://raw.githubusercontent.com/vegardege/euets-scraper/main/{p}", timeout=30)
    print(f"===== {p} ({len(r.content)} bytes) =====")
    print(r.text[:6000])
    print("...")

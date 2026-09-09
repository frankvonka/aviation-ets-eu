"""Read the remaining part of scraper.py (parsing + fetch_datasets)."""
import requests

s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0"
r = s.get("https://raw.githubusercontent.com/vegardege/euets-scraper/main/src/euets_scraper/scraper.py", timeout=30)
t = r.text
print(t[6000:12100])

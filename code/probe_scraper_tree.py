"""Read euets-scraper source to find the EEA datahub API endpoint + zip file naming."""
import requests, re

s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0"

# list repo tree via GitHub API
r = s.get("https://api.github.com/repos/vegardege/euets-scraper/git/trees/main?recursive=1", timeout=30)
print("tree:", r.status_code)
paths = [t["path"] for t in r.json().get("tree", []) if t["path"].endswith(".py")]
print(paths)

"""Fetch EEA datahub EU ETS page HTML and extract dataset accordions + Direct download links."""
import requests, re
from html.parser import HTMLParser

s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
URL = "https://www.eea.europa.eu/en/datahub/datahubitem-view/98f04097-26de-4fca-86c4-63834818c0c0"
r = s.get(URL, timeout=60)
print("page:", r.status_code, len(r.content))
html = r.text

# All links with their label text
link_re = re.compile(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', re.S)
seen = {}
for href, label in link_re.findall(html):
    label = re.sub(r"<[^>]+>", " ", label)
    label = re.sub(r"\s+", " ", label).strip()
    if href not in seen and ("download" in label.lower() or "download" in href.lower()):
        seen[href] = label
for href, label in list(seen.items())[:40]:
    print(f"  [{label[:60]}] {href[:160]}")

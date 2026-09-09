"""Download the 7.5 MB EEA EU ETS dataset zip and list its contents."""
import requests, io, zipfile
from pathlib import Path

OUT = Path("/root/aviation-emissions/data/_eea_ets.zip")
s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0 Chrome/126.0"
url = "https://sdi.eea.europa.eu/datashare/s/BrZkLYoYCGAy73H/download"
r = s.get(url, timeout=180, allow_redirects=True)
print("status", r.status_code, "ct", r.headers.get("content-type"), "len", len(r.content))
if r.status_code != 200 or len(r.content) > 200_000_000:
    raise SystemExit("abort: unexpected response")
OUT.write_bytes(r.content)
print("saved", OUT, OUT.stat().st_size)
with zipfile.ZipFile(OUT) as z:
    for i in z.infolist():
        print(f"  {i.file_size:>12,}  {i.filename}")

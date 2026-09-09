"""Resolve 'Direct download' page -> zip URL, and inspect page structure for per-file links."""
import requests, re

s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0 Chrome/126.0"

for dd in ["https://sdi.eea.europa.eu/data/a94a5d68-9973-4e2c-9a7a-fd7690ec3473",
           "https://sdi.eea.europa.eu/data/24567358-d375-4dff-87d7-d9943c68f5e0"]:
    try:
        r = s.get(dd, timeout=60, allow_redirects=True)
        print("==", dd)
        print("   status", r.status_code, "ct", r.headers.get("content-type"), "len", len(r.content), "final", r.url[:150])
        ct = r.headers.get("content-type", "")
        if "zip" in ct or "octet" in ct:
            print("   IT IS A ZIP directly")
            continue
        html = r.text
        # find 'Download all files' and other file links
        for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.S):
            href, label = m.group(1), re.sub(r"<[^>]+>", " ", m.group(2))
            label = re.sub(r"\s+", " ", label).strip()
            if any(k in label.lower() for k in ("download", "csv", "sql", "txt", "zip")) or any(
                k in href.lower() for k in ("download", "csv", "sql", "zip")):
                print(f"   [{label[:70]}] {href[:180]}")
        # table rows listing files?
        rows = re.findall(r"<td[^>]*>([^<]{3,80})</td>", html)
        print("   td sample:", rows[:25])
    except Exception as e:
        print("==", dd, "ERR", type(e).__name__, str(e)[:200])

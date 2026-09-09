"""Fetch the EEA datahub JSON API for the EU ETS dataset (main record + linked datasets).
The datahub uses a different API path than the SDI catalogue."""
import requests, json

s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0 research-script"
RID = "98f04097-26de-4fca-86c4-63834818c0c0"

candidates = [
    f"https://sdi.eea.europa.eu/portal/api/records/{RID}",
    f"https://www.eea.europa.eu/api/datahub/items/{RID}",
    f"https://www.eea.europa.eu/api/datahub/datasets/{RID}",
    "https://www.eea.europa.eu/api/datahub/search?query=EU%20ETS&limit=5",
    f"https://disc-cover.eea.europa.eu/api/records/{RID}",
    f"https://sdi.eea.europa.eu/catalogue/srv/eng/q?_content_type=json&any=EU ETS&from=1&to=10",
]
for u in candidates:
    try:
        r = s.get(u, timeout=30, allow_redirects=True)
        ct = r.headers.get("content-type", "")
        print("==", r.status_code, ct[:50], len(r.content), u[:110])
        if r.status_code == 200 and ("json" in ct or "javascript" in ct):
            try:
                print(json.dumps(r.json(), indent=1)[:2500])
            except Exception:
                print(r.text[:800])
    except Exception as e:
        print("== ERR", u[:110], type(e).__name__, str(e)[:150])

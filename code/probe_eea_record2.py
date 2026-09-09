"""Try Geonetwork JSON API variants + discomap table publisher endpoints."""
import requests, json

s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0 research-script"
RID = "98f04097-26de-4fca-86c4-63834818c0c0"

urls = [
    f"https://sdi.eea.europa.eu/catalogue/srv/api/records/{RID}?language=eng&format=json",
    f"https://sdi.eea.europa.eu/catalogue/srv/eng/api/records/{RID}",
    f"https://sdi.eea.europa.eu/catalogue/srv/api/records/{RID}/formatters/xml",
    # geonetwork classic
    f"https://sdi.eea.europa.eu/catalogue/srv/api/records/{RID}/attachments",
]
for u in urls:
    try:
        r = s.get(u, timeout=30)
        ct = r.headers.get("content-type", "")
        print("==", r.status_code, ct[:50], len(r.content), u[:110])
        if r.status_code == 200 and "json" in ct:
            print(json.dumps(r.json(), indent=1)[:4000])
    except Exception as e:
        print("== ERR", u[:110], type(e).__name__, str(e)[:150])

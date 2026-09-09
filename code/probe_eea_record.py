"""Get the real JSON record for EEA EU ETS dataset from SDI catalogue."""
import requests, json

s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0 research-script"

r = s.get("https://sdi.eea.europa.eu/catalogue/datahub/api/records/98f04097-26de-4fca-86c4-63834818c0c0?language=eng", timeout=30)
print("record:", r.status_code, r.headers.get("content-type"), len(r.content))
d = r.json()
# print links/distributions
def walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            walk(v, f"{path}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, f"{path}[{i}]")
    else:
        sval = str(o)
        if sval.startswith("http") and any(x in sval.lower() for x in ("discomap", "download", ".csv", ".zip", ".sql", ".txt", "dataset")):
            print(f"{path} = {sval[:200]}")

walk(d)
print("\n--- keys:", list(d.keys())[:40])

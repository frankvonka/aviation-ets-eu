"""Parse the ISO 19139 XML record: extract download links for EU ETS dataset."""
import requests, re

s = requests.Session()
s.headers["User-Agent"] = "Mozilla/5.0 research-script"
RID = "98f04097-26de-4fca-86c4-63834818c0c0"
r = s.get(f"https://sdi.eea.europa.eu/catalogue/srv/api/records/{RID}/formatters/xml", timeout=30)
xml = r.text
# all URLs in the record
urls = sorted(set(re.findall(r'https?://[^<"\s]+', xml)))
for u in urls:
    if any(k in u.lower() for k in ("discomap", "download", "csv", "zip", "sql", "txt", "sdi.eea")):
        print(u)
print("---- titles containing 'dataset'")
for m in re.finditer(r'<gco:CharacterString>([^<]*[Dd]ataset[^<]*)</gco:CharacterString>', xml):
    print(m.group(1))

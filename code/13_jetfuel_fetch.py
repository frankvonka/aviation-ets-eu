"""13_jetfuel_fetch.py — Complete the Eurostat INTAVI jet-fuel pull for ALL EU27+UK+IS/NO/CH.
The interrupted agent saved raw JSON for AT only; the API URL pattern is recoverable
from the raw file. Fetches the full INTAVI x O4669XR5230B (kerosene) matrix and
saves jetfuel_consumption.csv for all countries 2010-2024. Official Eurostat only.
"""
import json, urllib.request, time
import pandas as pd
from pathlib import Path

DATA = Path("/root/aviation-emissions/data")
OUT = DATA / "jetfuel_consumption.csv"
LOG = []
def log(s=""):
    print(s, flush=True); LOG.append(str(s))

# Inspect existing raw json to recover exact API parameters
raw = json.load(open(DATA/"jetfuel_intavi_raw.json"))
# Eurostat JSON-stat 2.0: {"version":..,"class":"dataset","value":{...},"dimension":{...}}
if isinstance(raw, dict):
    dims = raw.get("dimension", {})
    ids = list(dims.keys())
    log(f"JSON-stat dims: {ids}")
    geo_ids = dims.get("geo", {}).get("category", {}).get("index", {})
    log(f"geo codes in AT-file: {list(geo_ids)[:5]}...")
else:
    log("raw is a list?"); raw = None

URL = ("https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nrg_bal_c"
       "?format=JSON&lang=EN&freq=A&nrg_bal=INTAVI&siec=O4669XR5230B&unit=KTOE&time=2010&time=2011"
       "&time=2012&time=2013&time=2014&time=2015&time=2016&time=2017&time=2018&time=2019"
       "&time=2020&time=2021&time=2022&time=2023&time=2024")
log("fetching full INTAVI matrix...")
for attempt in range(3):
    try:
        with urllib.request.urlopen(URL, timeout=180) as r:
            data = json.load(r)
        break
    except Exception as e:
        log(f"  attempt {attempt+1} failed: {str(e)[:120]}")
        time.sleep(5)
else:
    raise SystemExit("Eurostat fetch failed")

dims = data["dimension"]["geo"]["category"]["index"]
time_ids = data["dimension"]["time"]["category"]["index"]
vals = data["value"]
Tn = len(time_ids)
rows = []
for gcode, gidx in dims.items():          # gcode = e.g. 'AT', gidx = integer position
    for tcode, tidx in time_ids.items():
        v = vals.get(str(gidx * Tn + tidx))
        if v is not None:
            rows.append(dict(country=gcode, year=int(tcode), ktoe=v,
                source="Eurostat nrg_bal_c, nrg_bal=INTAVI, siec=O4669XR5230B (kerosene-type jet fuel), unit=KTOE"))
df = pd.DataFrame(rows).sort_values(["country","year"])
df.to_csv(OUT, index=False)
log(f"saved {df.shape}, countries={df.country.nunique()}, years {df.year.min()}-{df.year.max()}")
(DATA/"jetfuel_fetch_log.txt").write_text("\n".join(LOG))

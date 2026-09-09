"""13b_jetfuel_fetch_v2.py — Robust Eurostat INTAVI fetch (JSON-stat 2.0, correct
value indexing: row-major over all dimensions in `id` order, not just geo x time).
Fetches kerosene-type jet fuel (O4669XR5230B), INTAVI balance, KTOE, 2010-2024,
all countries. Official Eurostat only.
"""
import json, urllib.request, time
import pandas as pd
from pathlib import Path

DATA = Path("/root/aviation-emissions/data")
OUT = DATA / "jetfuel_consumption.csv"
LOG = []
def log(s=""):
    print(s, flush=True); LOG.append(str(s))

URL = ("https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nrg_bal_c"
       "?format=JSON&lang=EN&freq=A&nrg_bal=INTAVI&siec=O4661XR5230B&unit=KTOE"
       + "".join(f"&time={y}" for y in range(2010, 2025)))
log("fetching INTAVI x kerosene matrix...")
data = None
for attempt in range(3):
    try:
        with urllib.request.urlopen(URL, timeout=240) as r:
            data = json.load(r)
        break
    except Exception as e:
        log(f"  attempt {attempt+1}: {str(e)[:150]}")
        time.sleep(8)
if data is None or not isinstance(data, dict):
    raise SystemExit("Eurostat fetch failed after retries")

ids   = data["id"]                      # dimension order, e.g. ['freq','nrg_bal','siec','unit','geo','time']
sizes = data["size"]                    # lengths per dimension
dims  = data["dimension"]
vals  = data["value"]
log(f"ids={ids}, sizes={sizes}")

# positions of geo and time within the dimension order
i_geo  = ids.index("geo")
i_time = ids.index("time")
geo_map  = dims["geo"]["category"]["index"]     # code -> position within geo dim
time_map = dims["time"]["category"]["index"]

# stride for each dimension (row-major)
strides = [int(np := 1)]
strides = []
acc = 1
for s in reversed(sizes):
    strides.append(acc); acc *= s
strides = list(reversed(strides))

rows = []
for gcode, gpos in geo_map.items():
    for tcode, tpos in time_map.items():
        flat = gpos*strides[i_geo] + tpos*strides[i_time]
        v = vals.get(str(flat))
        if v is not None:
            rows.append(dict(country=gcode, year=int(tcode), ktoe=v,
                source="Eurostat nrg_bal_c, nrg_bal=INTAVI, siec=O4661XR5230B (kerosene-type jet fuel, excl. biofuel), unit=KTOE"))

df = pd.DataFrame(rows).sort_values(["country","year"])
df.to_csv(OUT, index=False)
log(f"saved {df.shape}, countries={df.country.nunique()}, years {df.year.min()}-{df.year.max()}")
(DATA/"jetfuel_fetch_log.txt").write_text("\n".join(LOG))
log("DONE")

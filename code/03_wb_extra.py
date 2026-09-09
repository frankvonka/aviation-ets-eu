"""03_wb_extra.py — Fetch WB controls for the 11 non-EU control states (official WDI API).
Adds: AL AM BA GE MC MD ME MK RS TR XK (+ fix LI).
Then REBUILD G2G state-month-segment WITHOUT double counting:
  exact duplicate row pairs = the STATE block is printed twice in the raw file.
  Deduplicate on all 12 columns with keep='first' (documented), then aggregate.
"""
import pandas as pd, numpy as np, json, urllib.request, time
from pathlib import Path

BASE = Path("/root/aviation-emissions"); DATA = BASE / "data"
LOG = []
def log(s=""):
    print(s, flush=True); LOG.append(str(s))

# ── 1. WB indicators for control states ──────────────────────────────────
IND = {"NY.GDP.PCAP.CD": "gdp_pc", "IS.AIR.PSGR": "air_psgr",
       "IS.AIR.GOOD.MT.K1": "air_freight", "ST.INT.ARVL": "tourism"}
CTRY = "AL;AM;BA;GE;MC;MD;ME;MK;RS;TR;XK;LI"
rows = []
for code, col in IND.items():
    url = (f"https://api.worldbank.org/v2/country/{CTRY}/indicator/{code}"
           f"?date=2010:2024&format=json&per_page=1000")
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            data = json.load(r)
        for rec in data[1] or []:
            if rec["value"] is not None:
                rows.append(dict(country=rec["countryiso3code"], year=int(rec["date"]),
                                 indicator=col, value=rec["value"]))
        log(f"{col}: fetched {sum(1 for x in rows if x['indicator']==col)} non-null obs")
    except Exception as e:
        log(f"{col}: ERROR {str(e)[:150]}")
    time.sleep(1)
wide = (pd.DataFrame(rows).pivot_table(index=["country", "year"], columns="indicator",
                                       values="value").reset_index())
wide.columns.name = None
# merge with existing wb_controls (keep both; combined file below)
wb_old = pd.read_csv(DATA / "wb_controls.csv")
wb_all = (pd.concat([wb_old, wide], ignore_index=True)
          .drop_duplicates(subset=["country", "year"], keep="last")
          .sort_values(["country", "year"]))
wb_all.to_csv(DATA / "wb_controls_all.csv", index=False)
log(f"wb_controls_all: {wb_all.shape}, countries: {wb_all.country.nunique()}")

# ── 2. G2G dedup + rebuild ───────────────────────────────────────────────
g2g = pd.read_csv(DATA / "g2g_emissions.csv")
n0 = len(g2g)
g2g_dd = g2g.drop_duplicates(keep="first")
log(f"G2G dedup on all 12 cols: {n0} -> {len(g2g_dd)} (removed {n0-len(g2g_dd)})")
# sanity: after dedup, (AREA,YEAR,MONTH,SEGMENT,FTYPE,PHASE) should be unique for STATE rows
sd = g2g_dd[g2g_dd.LEVEL == "STATE"]
key_dups = sd.duplicated(subset=["AREA","YEAR","MONTH","MARKET_SEGMENT","FLIGHT_TYPE","FLIGHT_PHASE"]).sum()
log(f"remaining key duplicates after dedup: {key_dups}")
g2g_s = (sd.groupby(["AREA", "YEAR", "MONTH", "MARKET_SEGMENT"], as_index=False)
         .agg(nb_flights=("NB_FLIGHTS", "sum"), co2_t=("CO2_TONS", "sum")))
g2g_s.columns = ["iso", "YEAR", "MONTH", "segment", "nb_flights", "co2_t"]
g2g_s["co2_per_flight"] = g2g_s.co2_t / g2g_s.nb_flights.replace(0, np.nan)
# cross-check vs previous (double-counted) version: totals should halve approx
g2g_s.to_csv(DATA / "g2g_state_month.csv", index=False)
tot = g2g_s.groupby("YEAR").co2_t.sum()
log(f"G2G dedup state totals by year (Mt CO2):\n{(tot/1e6).round(1).to_string()}")

# ── 3. Segment shares 2019 (recomputed on deduped data) ──────────────────
seg19 = (g2g_s[g2g_s.YEAR == 2019].groupby(["iso", "segment"]).co2_t.sum().unstack(fill_value=np.nan))
seg19_share = seg19.div(seg19.sum(axis=1), axis=0)
seg19_share.to_csv(DATA / "segment_shares_2019.csv")
log(f"segment shares 2019: {seg19_share.shape}")

# ── 4. Rebuild annual/monthly panel with full WB controls ────────────────
raw = pd.read_excel(DATA / "CO2_emissions_by_state.xlsx", sheet_name="DATA")
raw.columns = [c.strip() for c in raw.columns]
name_map = json.load(open(DATA / "state_map.json")) if (DATA / "state_map.json").exists() else None
if name_map is None:
    name_map = {
        "AUSTRIA":"AT","BELGIUM":"BE","BULGARIA":"BG","CROATIA":"HR","CYPRUS":"CY",
        "CZECHIA":"CZ","DENMARK":"DK","DENMARK*":"DK","ESTONIA":"EE","FINLAND":"FI",
        "FRANCE":"FR","GERMANY":"DE","GREECE":"EL","HUNGARY":"HU","IRELAND":"IE",
        "ITALY":"IT","LATVIA":"LV","LITHUANIA":"LT","LUXEMBOURG":"LU","MALTA":"MT",
        "NETHERLANDS":"NL","POLAND":"PL","PORTUGAL":"PT","PORTUGAL*":"PT",
        "ROMANIA":"RO","SLOVAKIA":"SK","SLOVENIA":"SI","SPAIN":"ES",
        "CANARY ISLANDS":"ES","SWEDEN":"SE","UNITED KINGDOM":"GB","UNITED KINGDOM*":"GB",
        "ICELAND":"IS","NORWAY":"NO","NORWAY*":"NO","SWITZERLAND":"CH",
        "TÃœRKIYE":"TR","TÜRKIYE":"TR","TURKIYE":"TR",
        "ALBANIA":"AL","ARMENIA":"AM","BOSNIA AND HERZEGOVINA":"BA","GEORGIA":"GE",
        "KOSOVO":"XK","LIECHTENSTEIN":"LI","MOLDOVA, REPUBLIC OF":"MD","MONACO":"MC",
        "MONTENEGRO":"ME","NORTH MACEDONIA":"MK","SERBIA":"RS"}
    json.dump(name_map, open(DATA / "state_map.json", "w"), indent=1)
raw["iso"] = raw["STATE_NAME"].map(name_map)
panel_m = (raw.groupby(["iso","YEAR","MONTH"], as_index=False)
           .agg(CO2_t=("CO2_QTY_TONNES","sum"), flights=("TF","sum"),
                n_source=("STATE_NAME","nunique")))
EU27 = ["AT","BE","BG","HR","CY","CZ","DK","EE","FI","FR","DE","EL","HU","IE",
        "IT","LV","LT","LU","MT","NL","PL","PT","RO","SK","SI","ES","SE"]
TREATED = set(EU27 + ["IS","NO","LI","CH","GB"])
panel_m["ets_covered"] = panel_m.iso.isin(TREATED).astype(int)
panel_m["co2_per_flight"] = panel_m.CO2_t / panel_m.flights.replace(0, np.nan)
panel_m["ln_co2"] = np.log(panel_m.CO2_t); panel_m["ln_flights"] = np.log(panel_m.flights)
panel_m["ln_intensity"] = np.log(panel_m.co2_per_flight)
panel_m["post2012"] = (panel_m.YEAR >= 2012).astype(int)
panel_m["did"] = panel_m.post2012 * panel_m.ets_covered

panel_a = (panel_m[panel_m.YEAR <= 2025].groupby(["iso","YEAR"], as_index=False)
           .agg(CO2_t=("CO2_t","sum"), flights=("flights","sum"), months_obs=("MONTH","nunique"),
                ets_covered=("ets_covered","max")))
panel_a["co2_per_flight"] = panel_a.CO2_t / panel_a.flights
panel_a["ln_co2"] = np.log(panel_a.CO2_t); panel_a["ln_flights"] = np.log(panel_a.flights)
panel_a["ln_intensity"] = np.log(panel_a.co2_per_flight)
panel_a["post2012"] = (panel_a.YEAR >= 2012).astype(int)
panel_a["did"] = panel_a.post2012 * panel_a.ets_covered

panel_a = panel_a.merge(wb_all, left_on=["iso","YEAR"], right_on=["country","year"], how="left")
panel_a = panel_a.merge(pd.read_csv(DATA/"prices.csv")[["year","ets_eur"]],
                        left_on="YEAR", right_on="year", how="left")
panel_a.drop(columns=[c for c in ["country","year_y","year"] if c in panel_a.columns],
             inplace=True, errors="ignore")
log(f"panel_a rebuilt: {panel_a.shape}; gdp_pc missing={panel_a.gdp_pc.isna().sum()} "
    f"({100*panel_a.gdp_pc.isna().mean():.0f}%)")
panel_a.to_csv(DATA / "panel_state_year.csv", index=False)
panel_m.to_csv(DATA / "panel_state_month.csv", index=False)
(BASE / "results" / "cleaning_log_part2.txt").write_text("\n".join(LOG))
log("REBUILD COMPLETE")

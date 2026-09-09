"""02_clean_build.py — Clean SET panel, harmonize states, build analysis datasets.
Every operation documented. Saves:
  data/panel_state_year.csv   — annual state panel 2010-2025 (analysis main)
  data/panel_state_month.csv  — monthly state panel 2010-2026-06
  data/g2g_state_month.csv    — G2G aggregated state-month by segment (2019-2024)
  results/cleaning_log.txt
"""
import pandas as pd, numpy as np
from pathlib import Path

BASE = Path("/root/aviation-emissions")
DATA = BASE / "data"
LOG = []
def log(s=""):
    print(s, flush=True); LOG.append(str(s))

# ── 1. Load SET raw ──────────────────────────────────────────────────────
raw = pd.read_excel(DATA / "CO2_emissions_by_state.xlsx", sheet_name="DATA")
raw.columns = [c.strip() for c in raw.columns]
log(f"raw: {raw.shape}")

# ── 2. State harmonization (documented mapping) ──────────────────────────
# Artifacts found in audit: trailing '*' variants (2026 rows re-named),
# UTF-8 mojibake 'TÃœRKIYE' vs 'TÜRKIYE', CANARY ISLANDS (region of ES).
name_map = {
    "AUSTRIA":"AT","BELGIUM":"BE","BULGARIA":"BG","CROATIA":"HR","CYPRUS":"CY",
    "CZECHIA":"CZ","DENMARK":"DK","DENMARK*":"DK","ESTONIA":"EE","FINLAND":"FI",
    "FRANCE":"FR","GERMANY":"DE","GREECE":"EL","HUNGARY":"HU","IRELAND":"IE",
    "ITALY":"IT","LATVIA":"LV","LITHUANIA":"LT","LUXEMBOURG":"LU","MALTA":"MT",
    "NETHERLANDS":"NL","POLAND":"PL","PORTUGAL":"PT","PORTUGAL*":"PT",
    "ROMANIA":"RO","SLOVAKIA":"SK","SLOVENIA":"SI","SPAIN":"ES",
    "CANARY ISLANDS":"ES",  # EUROCONTROL reports Canary ISRs separately; folded into ES (documented)
    "SWEDEN":"SE","UNITED KINGDOM":"GB","UNITED KINGDOM*":"GB",
    "ICELAND":"IS","NORWAY":"NO","NORWAY*":"NO","SWITZERLAND":"CH",
    "TÃœRKIYE":"TR","TÜRKIYE":"TR","TURKIYE":"TR",
    "ALBANIA":"AL","ARMENIA":"AM","BOSNIA AND HERZEGOVINA":"BA","GEORGIA":"GE",
    "KOSOVO":"XK","LIECHTENSTEIN":"LI","MOLDOVA, REPUBLIC OF":"MD","MONACO":"MC",
    "MONTENEGRO":"ME","NORTH MACEDONIA":"MK","SERBIA":"RS",
}
raw["iso"] = raw["STATE_NAME"].map(name_map)
unmapped = raw.loc[raw.iso.isna(), "STATE_NAME"].unique()
log(f"unmapped states: {unmapped}")
assert raw.iso.notna().all(), "Unmapped states found — fix mapping"

# Fold duplicates (DK*, PT*, GB*, NO*, TR, Canary->ES) by summing within iso-year-month
n_before = len(raw)
panel_m = (raw.groupby(["iso", "YEAR", "MONTH"], as_index=False)
              .agg(CO2_t=("CO2_QTY_TONNES", "sum"), flights=("TF", "sum"),
                   n_source_states=("STATE_NAME", "nunique")))
log(f"after folding name variants + Canary->ES: {n_before} -> {len(panel_m)} rows, "
    f"{panel_m.iso.nunique()} iso units")
log(f"rows that were folded (n_source_states>1): {(panel_m.n_source_states>1).sum()}")

# ── 3. Treatment groups (EU ETS aviation scope, per ICAP/EU law) ─────────
# TREATED: EU27 + IS,NO,LI (EEA) + CH (linked) + GB (EU ETS 2012-2020; UK ETS after —
#          still carbon-priced; robustness excludes GB)
EU27 = ["AT","BE","BG","HR","CY","CZ","DK","EE","FI","FR","DE","EL","HU","IE",
        "IT","LV","LT","LU","MT","NL","PL","PT","RO","SK","SI","ES","SE"]
TREATED = set(EU27 + ["IS","NO","LI","CH","GB"])
panel_m["ets_covered"] = panel_m.iso.isin(TREATED).astype(int)
log(f"treated units: {panel_m[panel_m.ets_covered==1].iso.nunique()}, "
    f"control units: {panel_m[panel_m.ets_covered==0].iso.nunique()}")
log(f"control states: {sorted(panel_m[panel_m.ets_covered==0].iso.unique())}")

# ── 4. Exclude partial year 2026 from ANNUAL panel (Jan-Jun only) ────────
panel_a = (panel_m[panel_m.YEAR <= 2025]
           .groupby(["iso", "YEAR"], as_index=False)
           .agg(CO2_t=("CO2_t", "sum"), flights=("flights", "sum"),
                months_obs=("MONTH", "nunique"), ets_covered=("ets_covered", "max")))
full = panel_a.groupby("YEAR")["months_obs"].max()
panel_a["complete_year"] = panel_a.months_obs == panel_a.iso.map(
    panel_a.groupby("iso").months_obs.max())  # informational
log(f"annual panel: {panel_a.shape}, years {panel_a.YEAR.min()}-{panel_a.YEAR.max()}")
# states with coverage gaps in annual data
gaps = panel_a.groupby("iso").YEAR.agg(["min","max","count"])
gaps["expected"] = gaps["max"] - gaps["min"] + 1
log(f"units with missing years in span:\n{gaps[gaps['count'] < gaps['expected']].to_string()}")

# ── 5. Variables ─────────────────────────────────────────────────────────
for p, tag in [(panel_a, "a"), (panel_m, "m")]:
    p["co2_per_flight"] = p.CO2_t / p.flights.replace(0, np.nan)  # tonnes/flight (intensity)
    p["ln_co2"] = np.log(p.CO2_t)
    p["ln_flights"] = np.log(p.flights)
    p["ln_intensity"] = np.log(p.co2_per_flight)
# ETS post-2012 dummy + interaction
for p in [panel_a, panel_m]:
    p["post2012"] = (p.YEAR >= 2012).astype(int)
    p["did"] = p.post2012 * p.ets_covered

# ── 6. Merge WB controls + ETS price (annual) ────────────────────────────
wb = pd.read_csv(DATA / "wb_controls.csv")
pr = pd.read_csv(DATA / "prices.csv")[["year", "ets_eur"]]
panel_a = panel_a.merge(wb, left_on=["iso", "YEAR"], right_on=["country", "year"], how="left")
panel_a = panel_a.merge(pr, left_on="YEAR", right_on="year", how="left", suffixes=("", "_pr"))
panel_a.drop(columns=[c for c in ["country", "year_pr"] if c in panel_a.columns], inplace=True)
log(f"after WB+ETS merge: {panel_a.shape}; missing gdp_pc={panel_a.gdp_pc.isna().sum()}, "
    f"air_psgr={panel_a.air_psgr.isna().sum()}, ets={panel_a.ets_eur.isna().sum()}")
log(f"WB countries matched: {panel_a.loc[panel_a.gdp_pc.notna(),'iso'].nunique()} of {panel_a.iso.nunique()} "
    f"(controls exist only for EU28 list — non-ECAC control states have no WB row is FALSE: WB covers all)")

# ── 7. G2G aggregate: state-month-segment (2019-2024) ────────────────────
g2g = pd.read_csv(DATA / "g2g_emissions.csv")
dup_full = g2g.duplicated().sum()
log(f"G2G exact duplicate rows: {dup_full} — inspecting cause")
dupes = g2g[g2g.duplicated(keep=False)].sort_values(g2g.columns.tolist())
log(f"example duplicate block:\n{dupes.head(4).to_string()}")
# sum flight types + phases within state-month-segment (each phase is additive by construction)
g2g_s = (g2g[g2g.LEVEL == "STATE"]
         .groupby(["AREA", "YEAR", "MONTH", "MARKET_SEGMENT"], as_index=False)
         .agg(nb_flights=("NB_FLIGHTS", "sum"), co2_t=("CO2_TONS", "sum")))
g2g_s.columns = ["iso", "YEAR", "MONTH", "segment", "nb_flights", "co2_t"]
g2g_s["co2_per_flight"] = g2g_s.co2_t / g2g_s.nb_flights.replace(0, np.nan)
log(f"G2G state-month-segment panel: {g2g_s.shape}, states={g2g_s.iso.nunique()}")
# segment shares (pre-COVID 2019) for exposure heterogeneity
seg19 = (g2g_s[g2g_s.YEAR == 2019].groupby(["iso", "segment"]).co2_t.sum()
         .unstack(fill_value=np.nan))
seg19_share = seg19.div(seg19.sum(axis=1), axis=0)
seg19_share.to_csv(DATA / "segment_shares_2019.csv")

# ── 8. Save analysis datasets ────────────────────────────────────────────
panel_a.to_csv(DATA / "panel_state_year.csv", index=False)
panel_m.to_csv(DATA / "panel_state_month.csv", index=False)
g2g_s.to_csv(DATA / "g2g_state_month.csv", index=False)
(BASE / "results" / "cleaning_log.txt").write_text("\n".join(LOG))
log("SAVED: panel_state_year.csv, panel_state_month.csv, g2g_state_month.csv, segment_shares_2019.csv")

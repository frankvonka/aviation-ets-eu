"""01_explore.py — Data audit for EU aviation emissions project.
Datasets:
  A. CO2_emissions_by_state.xlsx (EUROCONTROL Small Emitters Tool, monthly 2010-2026)
  B. g2g_emissions.csv (EUROCONTROL Gate-to-Gate, monthly 2019-2024, segments+phases)
  C. wb_controls.csv (World Bank WDI: gdp_pc, air_psgr, air_freight, tourism)
  D. prices.csv (EEX EUA ETS price annual)
Audit per empirical-research-agent spec: N, units, coverage, balance, duplicates,
missingness, types, impossible values, constants, coverage changes, gaps, breaks.
"""
import pandas as pd, numpy as np, json
from pathlib import Path

BASE = Path("/root/aviation-emissions")
DATA = BASE / "data"
AUD = BASE / "results" / "data_audit"
AUD.mkdir(parents=True, exist_ok=True)
OUT_lines = []

def log(s=""):
    print(s, flush=True)
    OUT_lines.append(str(s))

# ── A: SET country-month panel ────────────────────────────────────────────
log("=" * 70)
log("A. CO2_emissions_by_state.xlsx — DATA sheet")
raw = pd.read_excel(DATA / "CO2_emissions_by_state.xlsx", sheet_name="DATA")
raw.columns = [c.strip() for c in raw.columns]
log(f"raw shape: {raw.shape}")
log(f"columns: {list(raw.columns)}")
log(f"dtypes:\n{raw.dtypes.to_string()}")
log(f"years: {raw.YEAR.min()}-{raw.YEAR.max()}")
log(f"months: {sorted(raw.MONTH.unique())[:3]}...{sorted(raw.MONTH.unique())[-3:]}")
log(f"n states: {raw.STATE_NAME.nunique()}")
log(f"states: {sorted(raw.STATE_NAME.unique())}")
# duplicates
dup = raw.duplicated(subset=["YEAR", "MONTH", "STATE_NAME"]).sum()
log(f"duplicate (year,month,state) rows: {dup}")
# missingness
miss = raw.isna().sum()
log(f"missing per column:\n{miss.to_string()}")
# impossible values
log(f"CO2_QTY_TONNES: min={raw.CO2_QTY_TONNES.min():.1f}, max={raw.CO2_QTY_TONNES.max():.1f}, "
    f"negatives={(raw.CO2_QTY_TONNES < 0).sum()}, zeros={(raw.CO2_QTY_TONNES == 0).sum()}")
log(f"TF: min={raw.TF.min()}, max={raw.TF.max()}, negatives={(raw.TF < 0).sum()}, zeros={(raw.TF == 0).sum()}")
# near-zero / suspicious small values
small = raw[(raw.CO2_QTY_TONNES < 100) & raw.CO2_QTY_TONNES.notna()]
log(f"rows with CO2 < 100t: {len(small)} (states: {small.STATE_NAME.unique()[:10]})")
# balance
obs_per_state = raw.groupby("STATE_NAME")["YEAR"].agg(["min", "max", "count"])
log(f"obs per state: min={obs_per_state['count'].min()}, max={obs_per_state['count'].max()}")
incomplete = obs_per_state[obs_per_state["count"] < obs_per_state["count"].max()]
log(f"states with fewer obs than max: {len(incomplete)}")
log(incomplete.to_string())
# CO2 intensity distribution (outliers)
raw["co2_per_flight"] = raw.CO2_QTY_TONNES / raw.TF.replace(0, np.nan)
log(f"CO2/flight: describe\n{raw.co2_per_flight.describe().to_string()}")
log(f"CO2/flight > 10t (suspicious): {(raw.co2_per_flight > 10).sum()}")
log(f"CO2/flight < 0.1t (suspicious): {(raw.co2_per_flight < 0.1).sum()}")
# structural break check: 2020 COVID
yr = raw.groupby("YEAR")[["TF", "CO2_QTY_TONNES"]].sum()
log(f"yearly totals (all states):\n{yr.to_string()}")

# ── B: G2G segment data ───────────────────────────────────────────────────
log("=" * 70)
log("B. g2g_emissions.csv")
g2g = pd.read_csv(DATA / "g2g_emissions.csv")
log(f"shape: {g2g.shape}")
log(f"years: {g2g.YEAR.min()}-{g2g.YEAR.max()}")
log(f"levels: {g2g.LEVEL.unique()}")
state_rows = g2g[g2g.LEVEL == "STATE"]
log(f"STATE-level rows: {len(state_rows)}; unique areas: {state_rows.AREA.nunique()}")
log(f"STATE areas sample: {sorted(state_rows.AREA.unique())[:15]}")
net_rows = g2g[g2g.LEVEL == "NETWORK"]
log(f"NETWORK-level rows: {len(net_rows)}; areas: {net_rows.AREA.unique()}")
log(f"segments: {g2g.MARKET_SEGMENT.unique()}")
log(f"flight types: {g2g.FLIGHT_TYPE.unique()} | phases: {g2g.FLIGHT_PHASE.unique()}")
dupB = g2g.duplicated().sum()
log(f"full duplicates: {dupB}")
log(f"missing per column:\n{g2g.isna().sum().to_string()}")
log(f"CO2_TONS: min={g2g.CO2_TONS.min():.2f}, max={g2g.CO2_TONS.max():.1f}, neg={(g2g.CO2_TONS < 0).sum()}")
# monthly totals for break detection
gm = net_rows.groupby(["YEAR", "MONTH"])[["NB_FLIGHTS", "CO2_TONS"]].sum().reset_index()
gm["ym"] = gm.YEAR * 100 + gm.MONTH
log(f"network monthly flights: 2019-01={gm[gm.ym==201901].NB_FLIGHTS.iloc[0]:,.0f}, "
    f"2020-04={gm[gm.ym==202004].NB_FLIGHTS.iloc[0]:,.0f} (COVID trough), "
    f"2024-12={gm[gm.ym==202412].NB_FLIGHTS.iloc[0]:,.0f}")

# ── C: WB controls ────────────────────────────────────────────────────────
log("=" * 70)
log("C. wb_controls.csv")
wb = pd.read_csv(DATA / "wb_controls.csv")
log(f"shape: {wb.shape}, countries: {wb.country.nunique()}, years: {wb.year.min()}-{wb.year.max()}")
log(f"missingness: {wb.isna().sum().to_dict()}")

# ── D: ETS prices ─────────────────────────────────────────────────────────
log("=" * 70)
log("D. prices.csv")
pr = pd.read_csv(DATA / "prices.csv")
log(f"shape: {pr.shape}, years: {pr.year.min()}-{pr.year.max()}")
log(pr.to_string(index=False))

# ── Save audit outputs ────────────────────────────────────────────────────
raw.to_csv(AUD / "set_raw_dump.csv", index=False)
summary = dict(
    set_rows=len(raw), set_states=int(raw.STATE_NAME.nunique()),
    set_years=f"{raw.YEAR.min()}-{raw.YEAR.max()}",
    set_duplicates=int(dup),
    g2g_rows=len(g2g), g2g_years=f"{g2g.YEAR.min()}-{g2g.YEAR.max()}",
    wb_rows=len(wb), ets_years=f"{pr.year.min()}-{pr.year.max()}",
)
(AUD / "audit_summary.json").write_text(json.dumps(summary, indent=2))
(BASE / "results" / "data_audit.txt").write_text("\n".join(OUT_lines))
log("=" * 70)
log("AUDIT COMPLETE")

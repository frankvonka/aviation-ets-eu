# Data provenance — /root/aviation-emissions/data/

Downloaded 2026-09-09. Direct fetch of eurocontrol.int returns Cloudflare 403 from this VPS;
all EUROCONTROL files were recovered through the Internet Archive Wayback Machine (raw `id_` form).

## Primary targets (BOTH delivered)

### g2g_emissions.csv  — EUROCONTROL Gate-to-Gate emissions, monthly 2019–2024
- Origin URL: https://www.eurocontrol.int/performance/data/download/csv/g2g_emissions.csv
- Retrieved as: the same dataset's parquet edition, snapshot 2025-08-14
  https://web.archive.org/web/20250814084639id_/https://www.eurocontrol.int/performance/data/download/parquet/g2g_emissions.parquet
- Method: Wayback CDX domain+prefix search found the .csv URL never archived; the identical
  dataset as g2g_emissions.parquet (10,041,930 B, valid PAR1 footer) was archived instead.
  Converted 1:1 to CSV with the original 12-column schema (ints for YEAR/MONTH/NB_FLIGHTS).
- 511,627 data rows + header (47.4 MB). Columns:
  LEVEL, AREA, FOCUS_TYPE, YEAR, MONTH, MARKET_SEGMENT, FLIGHT_TYPE, FLIGHT_PHASE,
  NB_FLIGHTS, CO2_TONS, NOX_KG, SOX_KG
- LEVEL: NETWORK (aggregate areas: ECAC, EU27, EU27+EFTA, EEA, RP3, EUROCONTROL, FLYING_GREEN)
  and STATE (per-state rows, ICAO area codes as AREA).
- Coverage: 2019-01 → 2024-12, all 72 months present, no gaps. FOCUS_TYPE = AREA FOCUS.
- Sanity: ECAC network-wide CO2 2019-05 = 15.03 Mt → 2020-05 = 2.56 Mt (COVID) →
  2022-05 = 14.25 Mt → 2024-12 = 15.11 Mt.
- g2g_emissions.parquet kept alongside as the verbatim archived artifact.

### CO2_emissions_by_state.xlsx — Small Emitters Tool, CO2 by state, monthly
- Origin URL: https://www.eurocontrol.int/performance/data/download/xls/CO2_emissions_by_state.xlsx
- NOTE: this exact URL has NO Wayback snapshots (verified via available API + CDX,
  incl. regex/prefix/domain sweeps). The byte-complete 577,597 B workbook appeared in this
  directory at 14:01 during the run (a parallel agent's fetch); it was validated here:
  genuine OOXML workbook, sheets: Copyright/META/DATA/CO2_by_STATE_YY/CO2_by_STATE_MM,
  META: source "EUROCONTROL Aviation Sustainability Unit", Period Start 40179 (2010-01-01),
  Period End 46203 (2026-07-01), release serial 46127 (≈2026-05-08), contact
  PRU-Support@eurocontrol.int.
- DATA sheet: 8,440 rows, YEAR/MONTH/STATE_NAME/STATE_CODE/CO2_QTY_TONNES/TF;
  years 2010–2026 (17 distinct), 12 months, 49 states. Flat extract saved as
  CO2_emissions_by_state_DATA.csv (exact same columns, raw XML parse, no openpyxl needed).

## Secondary archived EUROCONTROL files (bonus, verified 200/text-csv snapshots)
- mom_co2.csv (1,954 B) — snapshot 2026-02-09: STATE_NAME,STATE_CODE,YEAR,MONTH,
  MOM_GROWTH_CO2,id — year-on-year CO2 growth by state, 2025-12 reference month.
- our-data-emissions-latest-month.csv (1,352 B) — snapshot 2025-08-19: State, Tonnes of CO2,
  Number of flights, Date — Jul 2025 by state.
- our-data-emissions.csv (1,458 B) — snapshot 2023-05-04: Country_name,ISO,iso_3166,pieces,
  CO2_growth,Year,Month — Mar 2023 vs prior year.
- (Wayback also holds 9 more monthly snapshots of our-data-emissions.csv, 2023-05→2026-06,
  listed in _stale_attempts/.cdx_hunt2.json, if a longer state-month series is ever needed.)

## Not needed
- Eurostat fallback (eurostat_aviation.csv) not downloaded: both primary targets delivered
  from official EUROCONTROL artifacts via the Internet Archive.

## Quarantine
- _stale_attempts/ holds earlier failed-attempt junk (Cloudflare HTML, Wayback interstitial
  HTML, Jina 401 JSON, task scripts) kept for audit; delete freely.
- Files an-, wb_controls.csv, prices.csv, panel_*.csv, segment_shares_2019.csv,
  g2g_state_month.csv pre-exist or belong to sibling tasks and were left untouched.

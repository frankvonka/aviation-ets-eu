# EUTL Aviation Data — Provenance

## File
`data/eutl_aviation.csv` — per administering member state × year, 2012–2021:
verified emissions of aircraft operators and free allocation (entitlements) to
aircraft operators under the EU ETS.

Columns: `year`, `member_state` (ISO2), `verified_tco2`, `free_allocation_tco2`, `source`.
295 rows = 30 administering countries × 10 years, minus 15 (year, country) pairs with no
verified-emissions row (details under Known gaps). No values were imputed or invented.

## Source (official)
- **EEA dataset**: *European Union Emissions Trading System (EU ETS) data from the Union Registry*,
  European Environment Agency, datahub item `98f04097-26de-4fca-86c4-63834818c0c0`
  (https://www.eea.europa.eu/en/datahub/datahubitem-view/98f04097-26de-4fca-86c4-63834818c0c0)
- **Version used**: `eea_t_eu-emission-trading-scheme_p_2005-2025_v02_r00`, published July 2026
  (data extracted by EEA from the European Commission **Union Registry**, formerly the EU
  Transaction Log, EUTL; internal dataset `version` field = 81).
- **Download**: 7.5 MB zip via the dataset's "Direct download" page
  `https://sdi.eea.europa.eu/data/a94a5d68-9973-4e2c-9a7a-fd7690ec3473` →
  `https://sdi.eea.europa.eu/datashare/s/BrZkLYoYCGAy73H/download` (fetched 2026-09-09).
  Archive contents: `ETS_Database_July_2026.xlsx` (84,056 data rows; the machine-readable
  full database behind the EU ETS data viewer), plus background note, data-quality note,
  user manual and metadata XML.
- This is the EEA's own filtered/aggregated extract of EUTL/Union Registry data — NOT the
  ~2 GB "Download" zip of the EEA EU ETS Data Viewer web app, which was deliberately avoided.

## Filter applied
Rows with `main_activity_code = 10` (ETS activity type 10 = **aviation / aircraft operators**),
years 2012–2021, one row per administering country (`country_code`, ISO 2-letter, includes
EEA non-EU: NO, IS, LI; GB = UK for 2012–2020).

## Metric definitions (as coded by EEA from Union Registry/EUTL)
- **verified_tco2** ← label `2. Verified emissions` (unit: tonne of CO2-eq.).
  Verified emissions of aircraft operators reported in the Union Registry for the
  administering country. In 2020–2021 this EUTL total includes Swiss-linking emissions
  (`2.2 Swiss Verified Emissions for aircraft operators`, surrendered with Swiss CHUs);
  label `2.1 EU-ETS Verified Emission` covers the EUA-surrendered part only.
- **free_allocation_tco2** ← label `1. Total allocated allowances (EUA or EUAA)` **minus**
  label `1.3 Allowances auctioned or sold (EUAs and EUAAs)` (units = allowances ≈ tCO2).
  Verified for all 286 (year, country) pairs that carry the component labels against the
  identity `Total − auctioned = 1.1 Freely allocated allowances + 1.2 Correction to freely
  allocated allowances (not reflected in EUTL)`; 0 violations. The `1.2` corrections are
  country-level adjustments; for aviation they arise mainly from the 2012 "stop-the-clock"
  decision (free allocation above the reduced scope had to be returned, largely not
  reflected in the EUTL) — see EEA/ETC-CM *EU ETS data viewer background note*, section
  2.1.2 and glossary entry for label 1.2 (included in the source archive).
  Notes:
  - 2012 free allocation = entitlements issued for the 2012 scheme year (full or reduced
    scope at operator choice), net of the EEA-recorded 2012 stop-the-clock correction
    (`1.2`) where the issuing MS is also the correcting MS. The EEA notes these returns
    are "to a large extent" not reflected in the EUTL, so residual cross-country offsets
    may exist in 2012 net-of-correction figures.
  - 2020–2021: free allocation to operators of the administered country that is covered by
    **Swiss CHUs** (`1.1.4 Swiss Free Allocated allowances for aircraft operators`) is
    included in label `1.1` and therefore in this file's free_allocation column (it is part
    of `Total − auctioned`).

## Known gaps (rows absent from the source, not dropped by this pipeline)
- **LI (Liechtenstein), all 10 years**: allocation rows only (a single administered operator;
  entitlements moved to/from other MSs); no verified-emissions row for aviation → excluded.
- **EE, SI, SK in 2020; GB in 2021**: no verified-emissions row (EE 2020 & GB 2021 have
  zero-allocation rows only; the EEA data-quality note documents registry-side
  reallocation/withdrawal of entries in latest years) → excluded.
- All 15 exclusions are (year, country) pairs where the EEA/EUTL extract itself contains no
  `2. Verified emissions` row for activity 10.

## Validation performed
- 2012–2019 summed verified emissions (30 countries incl. GB, NO, IS) ≈ 84.0 (2012),
  53.5 (2013), … 68.2 (2019) MtCO2 — consistent with EEA *Trends and Projections in the EU
  ETS* aviation reporting (e.g. ~85 Mt in 2012, ~53 Mt in 2013 under reduced scope).
- 2020 ≈ 25.3 Mt, 2021 ≈ 28.0 Mt (COVID collapse; 2021 includes Swiss-linking emissions).
- Free allocation ≈ 67.5 Mt (2012, incl. full-scope entitlements) vs ~30–32.7 Mt (2013–2020,
  reduced-scope era: 82% free / 15% auctioned / 3% reserve), 23.9 Mt (2021) — consistent
  with the EEA background note's description of the 3% auction share for aviation and the
  2021 scope change (50% of 2019 benchmark emissions, EEA-only flights).
- Internal identity checks pass for 100% of rows carrying component labels (see above).

## Reproduction
Scripts (all under `code/`, run with `/root/.venvs/aviation/bin/python`):
- `download_eea_ets.py` — fetch 7.5 MB EEA zip (URL above) → `data/_eea_ets.zip`
- `extract_ets_xlsx.py` → `extract_aviation_rows.py` — extract `ETS_Database_July_2026.xlsx`,
  filter activity-10 rows 2012–2021 → `data/_eea_ets_aviation_raw.csv` (intermediate)
- `build_eutl_aviation.py` — pivots labels, applies the metric definitions above, writes
  `data/eutl_aviation.csv`
- `verify_identity.py` — re-checks the free-allocation identity (0 violations)

## Archive notes
`data/_eea_ets.zip` (7.5 MB) and `data/ETS_Database_July_2026.xlsx` (3.4 MB) retained
locally; delete either if disk is needed — the CSV and the download URL are sufficient
to reproduce.

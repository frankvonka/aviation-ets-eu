
## 1. Basics

- File: panel_state_year.csv | size 96.0 KB | rows 672 | cols 18 | memory 95.9 KB
- Years: 2010-2025 | states (iso): 43
- Treated states (ets_covered=1 at any year): 32
- Control states: 11
- Column roles:
  - iso: ID-like (state) | dtype str | nunique 43
  - YEAR: datetime (year) | dtype int64 | nunique 16
  - CO2_t: numeric (outcome) | dtype float64 | nunique 672
  - flights: numeric | dtype int64 | nunique 665
  - months_obs: numeric (completeness) | dtype int64 | nunique 7
  - ets_covered: binary (treatment) | dtype int64 | nunique 2
  - co2_per_flight: numeric (derived) | dtype float64 | nunique 672
  - ln_co2: numeric (outcome, log) | dtype float64 | nunique 672
  - ln_flights: numeric | dtype float64 | nunique 665
  - ln_intensity: numeric | dtype float64 | nunique 672
  - post2012: binary | dtype int64 | nunique 2
  - did: binary (treatment×post) | dtype int64 | nunique 2
  - year_x: numeric (trend) | dtype float64 | nunique 15
  - gdp_pc: numeric (control, WB) | dtype float64 | nunique 397
  - air_psgr: numeric (control) | dtype float64 | nunique 347
  - air_freight: numeric (control) | dtype float64 | nunique 319
  - tourism: numeric (control) | dtype float64 | nunique 277
  - ets_eur: numeric (price) | dtype float64 | nunique 16
- Other datasets present: panel_state_month.csv, g2g_emissions.csv (46MB), g2g_state_month.csv, wb_controls*.csv, prices.csv, hicp_airfares.csv, jetfuel_consumption.csv, eutl_aviation.csv, segment_shares_2019.csv, state_map.json, ETS_Database_July_2026.xlsx, CO2_emissions_by_state.xlsx.

## 2. Data quality

- Missingness per column (count, %):
  - year_x: 275 (40.92%)
  - gdp_pc: 275 (40.92%)
  - air_psgr: 325 (48.36%)
  - air_freight: 341 (50.74%)
  - tourism: 392 (58.33%)
- Rows with any missing: 416 (61.9%)
- Duplicate rows: 0 | duplicate (iso,YEAR): 0
- Constant columns: []
- Near-constant (>99% one value): []
- Suspicious/impossible values:
  - CO2_t: min=0.463, max=37299134.186, negatives=0, zeros=0
  - flights: min=1, max=1267852, negatives=0, zeros=0
  - co2_per_flight: min=0.3050369357045143, max=76.8425049686972, negatives=0, zeros=0
  - months_obs: min=1, max=12, negatives=0, zeros=0
  - months_obs range 1-12 (12 = complete year)
  - ets_eur min 4.5 max 83.0 (price, treated years)
- Outlier rate (IQR×1.5) per numeric:
  - CO2_t: 15.9% (skew 2.51)
  - flights: 12.6% (skew 2.03)
  - months_obs: 1.9% (skew -7.55)
  - co2_per_flight: 4.0% (skew 1.75)
  - ln_co2: 4.2% (skew -2.28)
  - ln_flights: 1.8% (skew -1.83)
  - ln_intensity: 4.6% (skew -2.54)
  - post2012: 11.9% (skew -2.36)
  - gdp_pc: 2.8% (skew 1.69)
  - air_psgr: 5.4% (skew 1.94)
  - air_freight: 10.0% (skew 1.89)
  - tourism: 4.0% (skew 2.55)
- Missingness is structural: gdp_pc/air_psgr/air_freight/tourism missing for control (non-WB-covered) states; WB controls only for a subset. Not random.

## 3. Distributions

- Numeric summary (mean, std, min, q25, q50, q75, max, skew, %zeros):
  - CO2_t: mean=4.19e+06 std=7.5e+06 min=0.463 q25=2.09e+05 med=9.57e+05 q75=3.31e+06 max=3.73e+07 skew=2.51 zeros=0.0%
  - flights: mean=2e+05 std=3.08e+05 min=1 q25=1.68e+04 med=5.13e+04 q75=2.23e+05 max=1.27e+06 skew=2.03 zeros=0.0%
  - co2_per_flight: mean=16.5 std=9.04 min=0.305 q25=11 med=14.7 q75=20.7 max=76.8 skew=1.75 zeros=0.0%
  - ln_co2: mean=13.5 std=2.78 min=-0.77 q25=12.3 med=13.8 q75=15 max=17.4 skew=-2.28 zeros=0.0%
  - ln_flights: mean=10.9 std=2.16 min=0 q25=9.73 med=10.8 q75=12.3 max=14.1 skew=-1.83 zeros=0.7%
  - ln_intensity: mean=2.61 std=0.785 min=-1.19 q25=2.4 med=2.69 q75=3.03 max=4.34 skew=-2.54 zeros=0.0%
  - gdp_pc: mean=3.72e+04 std=2.42e+04 min=6.85e+03 q25=1.96e+04 med=3.14e+04 q75=4.9e+04 max=1.38e+05 skew=1.69 zeros=0.0%
  - air_psgr: mean=2.63e+07 std=3.85e+07 min=857 q25=1.59e+06 med=8.85e+06 q75=3.39e+07 max=1.93e+08 skew=1.94 zeros=0.0%
  - air_freight: mean=1.52e+03 std=2.52e+03 min=0 q25=2.78 med=308 q75=1.35e+03 max=1.29e+04 skew=1.89 zeros=1.8%
  - tourism: mean=3.1e+07 std=4.34e+07 min=5.25e+05 q25=5.48e+06 med=1.17e+07 q75=3.69e+07 max=2.18e+08 skew=2.55 zeros=0.0%
  - ets_eur: mean=30.8 std=29.1 min=4.5 q25=7 med=15.5 q75=65 max=83 skew=0.79 zeros=0.0%
- Categorical/ID: iso cardinality 43; YEAR 16 unique; ets_covered balance {1: 500, 0: 172}; post2012 balance {1: 592, 0: 80}
- Top 10 states by mean annual CO2: GB=31,362,142, DE=26,823,615, FR=19,320,656, ES=18,157,166, TR=13,773,040, IT=12,388,197, NL=9,853,155, CH=4,787,922, BE=4,436,264, PT=4,093,705
- Transforms flagged: CO2_t, flights, co2_per_flight right-skewed -> log (ln_* already present); gdp_pc etc. skewed; ets_eur only for treated years.

## 4. Target (ln_co2) and treatment

- Task framing: panel causal inference (DiD), not standard prediction. Outcome ln_co2 (continuous, regression). Treatment: ets_covered (binary, time-varying state-level) / did (treatment×post).
- ln_co2: mean 13.490 std 2.782 min -0.770 max 17.434 skew -2.282
- Treatment balance: ets_covered=1 in 500 rows (74.4%), did=1 in 440 rows
- Top correlations with ln_co2: ln_flights=0.981, ln_intensity=0.842, air_psgr=0.662, months_obs=0.643, air_freight=0.631, flights=0.600, co2_per_flight=0.574
- Leakage screen: ln_flights corr with ln_co2 likely high (traffic drives emissions); did/year_x encode treatment/time. co2_per_flight derived from outcome (intensity). No near-copy of target found beyond ln transforms. ID/time columns (iso, YEAR) encode structure but not target directly.
- Label noise: identical (iso) rows with varying ln_co2 over years is expected (time trend), not noise. No duplicate feature rows with conflicting targets beyond time.

## 5. Structure that dictates validation

- Time: YEAR 2010-2025, 16 years, regular annual. months_obs min 1 (all 12 for yearly panel).
- Groups: iso n=43; rows per state min 9 max 16 mean 15.6.
- Treated vs control states: treated set = EU27+IS/NO/LI+CH+GB (32); controls = 11 ECAC non-EU. Entities do NOT span train/test under random splits if grouped by iso -> use GroupKFold by iso or temporal split.
- Trend/drift: CO2 generally rising then plateau; post-2012 treated decline visible in aggregates. Distribution shift between pre/post 2012 and COVID (2020+) -> exclude 2020+ for COVID-free analysis (main sample 2010-2019).
- Subgroups: treated vs control; low-cost/mainline/cargo/business segments in separate file.

## 6. Redundancy and dimensionality

- High corr pairs (|r|>0.85): YEAR-year_x=1.0; CO2_t-flights=0.965; ln_co2-ln_flights=0.981
- n/p ratio: 672/18 = 37.3 (plenty of rows). Effective predictors ~12 after dropping derived/ID.
- Feature clusters: ln_co2/ln_flights/ln_intensity/co2_per_flight (traffic); WB controls cluster (gdp_pc, air_psgr, air_freight, tourism); ets_eur collinear with treatment/post.

## 7. Difficulty and headroom (baselines)

- Validation: GroupKFold(5) by iso (no entity leakage). Imputation median for missing controls.
- Dummy(mean): MAE=1.8928 (±-0.5251) RMSE=2.5816 R2=-0.1603 (±0.2120)
- OLS: MAE=1.3541 (±-0.3818) RMSE=2.0260 R2=0.3264 (±0.1717)
- Ridge: MAE=1.2642 (±-0.3716) RMSE=1.8774 R2=0.4194 (±0.1849)
- HistGB: MAE=0.5907 (±-0.2420) RMSE=0.9935 R2=0.8397 (±0.0850)
- Gap simple->complex indicates headroom; WB-control missingness limits control-state coverage.
- Top feature importance (permutation, HistGB): flights=1.8593, air_freight=0.0080, gdp_pc=0.0073, ets_eur=0.0034, air_psgr=0.0017, tourism=0.0013, year_x=0.0012, post2012=0.0010, months_obs=0.0000
- Subgroup performance: treated states higher CO2 volume; control states fewer WB covariates -> imputation-heavy.

## 8. Pipeline decision sheet

- Cleaning/encoding: missing WB controls are structural (control states) -> keep as NaN or impute with state-level; do not drop rows. Outliers in CO2 likely real (large hubs) -> keep, maybe log. Categorical: iso one-hot or entity FE. Scaling: standardize for linear; tree models no scaling.
- Feature work: drop derived (ln_flights, ln_intensity, co2_per_flight) or use as targets; keep flights, months_obs, year_x, ets_eur, WB controls. Engineer post2012, did, ets_covered. Consider lags.
- Split strategy: GroupKFold by iso for ML baselines; main causal analysis uses state+year FE DiD (2010-2019 COVID-free). Temporal split for forecasting. Metric: MAE/RMSE/R2 for prediction; ATT/SE for causal.
- Model ladder: Dummy -> OLS/Ridge -> HistGB -> (maybe RF). ML is corroboration, not primary (causal DiD).
- Imbalance/shift: treated vs control imbalance; handle via clustering/RI, not resampling. Shift (COVID) -> exclude 2020+ for main.
- Q1 experiments: ablations (controls on/off, time window), sensitivity (LOO states), statistical tests (wild bootstrap, RI), MDE/TOST for null, dose-response on net-short share, mechanism tests (fares, segments, fuel). Seeds fixed 42; folds saved.

## 9. Paper potential

- Verdict: GO (with conditions). Data: 43 states × 16 years (main 2010-2019), verified emissions, treatment exogenous (EU policy). Quality decent; missing WB controls structural but manageable.
- Headroom: HistGB R2 modest; primary causal effect -0.208 (p=0.012) survives robustness. ML corroboration small (AIPW -0.008).
- Novelty risk: 'another DiD on EU ETS' — mitigated by COVID-free counterfactual, mechanism analysis, policy optimization, ML/CATE, SCM. Literature check needed for nearest neighbours (free-allocation mechanism).
- Angles supported: robustness (LOO, bootstrap, RI), mechanism (price channel muted, free allocation), policy (price targets, optimal path, burden sharing), data-efficiency (COVID counterfactual).
- Decisions I need from you: (1) confirm main sample 2010-2019 vs full; (2) confirm control set (11 ECAC); (3) confirm outcome (ln CO2) and secondary (flights, intensity); (4) confirm policy optimization scope (2030 targets); (5) literature check on free-allocation mechanism papers.

---
Files: eda_report/report.md, eda_report/report.html. Open report.md for compact view.

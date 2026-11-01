# Inventory: aviation-fresh

Code files: 27 | Result files: 53 | Data files: 24
README: True | Env file: True | Tests: True | Git: True

## Code files (every one must be audited)

| # | Path | Lines | Roles (guess) | Seed? | Read? |
|---|---|---|---|---|---|
| 1 | `code/02_clean_build.py` | 185 | data, ablation | NO | [ ] |
| 2 | `code/05_models_fixed.py` | 141 | data, ml, stats, timeseries_panel | NO | [ ] |
| 3 | `code/05_reconcile.py` | 67 | data, ml, stats | NO | [ ] |
| 4 | `code/06_ml_suite.py` | 171 | data, ml | yes | [ ] |
| 5 | `code/07_scm_suite.py` | 154 | data, optimization | yes | [ ] |
| 6 | `code/08_simulation_suite.py` | 191 | data, ml, simulation, ablation, stats | yes | [ ] |
| 7 | `code/09_optimization_suite.py` | 312 | data, optimization | yes | [ ] |
| 8 | `code/10_tables_figures.py` | 184 | data, simulation, ablation, timeseries_panel, plotting | NO | [ ] |
| 9 | `code/11_null_precision.py` | 156 | data, ml, simulation, ablation, stats | yes | [ ] |
| 10 | `code/12_mechanism_pass_through.py` | 92 | data, ml, stats | NO | [ ] |
| 11 | `code/14_fuel_crosscheck.py` | 48 | data, stats | NO | [ ] |
| 12 | `code/15_dose_response.py` | 59 | data, stats | NO | [ ] |
| 13 | `code/build_manuscript.py` | 569 | data, simulation, ablation, stats | yes | [ ] |
| 14 | `run_all.py` | 89 | utility | NO | [ ] |
| 15 | `scripts/capture_environment.py` | 44 | utility | NO | [ ] |
| 16 | `scripts/freeze_manifest.py` | 89 | utility | NO | [ ] |
| 17 | `scripts/postprocess_results.py` | 43 | simulation | NO | [ ] |
| 18 | `scripts/reproduce_and_verify.sh` | 16 | utility | NO | [ ] |
| 19 | `scripts/run_each_script.sh` | 30 | utility | NO | [ ] |
| 20 | `scripts/save_model_artifacts.py` | 33 | data, ml | yes | [ ] |
| 21 | `scripts/seeded_selection.py` | 49 | utility | yes | [ ] |
| 22 | `scripts/verify_determinism.py` | 45 | utility | NO | [ ] |
| 23 | `src/__init__.py` | 0 | utility | NO | [ ] |
| 24 | `src/config_loader.py` | 58 | data, simulation, ablation | yes | [ ] |
| 25 | `src/preprocessing.py` | 53 | data | NO | [ ] |
| 26 | `src/split_manager.py` | 47 | utility | yes | [ ] |
| 27 | `tests/test_smoke.py` | 149 | data, ablation | yes | [ ] |

## Results (every one must be audited)

| # | Path | Size (KB) | Audited? |
|---|---|---|---|
| 1 | `artifacts/logs/environment.json` | 0 | [ ] |
| 2 | `artifacts/logs/stamp_log.json` | 1 | [ ] |
| 3 | `eda_report/report.html` | 10 | [ ] |
| 4 | `figures/F10_allocation.png` | 70 | [ ] |
| 5 | `figures/F1_ets_vs_co2.png` | 110 | [ ] |
| 6 | `figures/F2_heatmap.png` | 122 | [ ] |
| 7 | `figures/F3_event_study.png` | 47 | [ ] |
| 8 | `figures/F4_ml_importance.png` | 63 | [ ] |
| 9 | `figures/F5_scm_path.png` | 57 | [ ] |
| 10 | `figures/F6_placebo_rmspe.png` | 73 | [ ] |
| 11 | `figures/F7_covid_counterfactual.png` | 64 | [ ] |
| 12 | `figures/F8_policy_montecarlo.png` | 89 | [ ] |
| 13 | `figures/F9_mac_curve.png` | 59 | [ ] |
| 14 | `results/mechanisms/m1_fare_pass_through.csv` | 0 | [ ] |
| 15 | `results/mechanisms/m2_fuel_did.csv` | 0 | [ ] |
| 16 | `results/mechanisms/m3_segments.csv` | 0 | [ ] |
| 17 | `results/ml/aipw_did.csv` | 0 | [ ] |
| 18 | `results/ml/aipw_state_effects.csv` | 2 | [ ] |
| 19 | `results/ml/cate_by_state.csv` | 0 | [ ] |
| 20 | `results/ml/cate_summary.csv` | 0 | [ ] |
| 21 | `results/ml/ml_cv.csv` | 0 | [ ] |
| 22 | `results/ml/ml_importance.csv` | 0 | [ ] |
| 23 | `results/models/dose_response.csv` | 0 | [ ] |
| 24 | `results/models/event_study_fixed.csv` | 4 | [ ] |
| 25 | `results/models/heterogeneity.csv` | 2 | [ ] |
| 26 | `results/models/main_models.csv` | 4 | [ ] |
| 27 | `results/models/n1_respecified.csv` | 0 | [ ] |
| 28 | `results/models/n2_tost.csv` | 0 | [ ] |
| 29 | `results/models/n3_mde.csv` | 0 | [ ] |
| 30 | `results/models/n4_looo.csv` | 4 | [ ] |
| 31 | `results/models/n4_ri_per_drop.csv` | 0 | [ ] |
| 32 | `results/models/specification_log.csv` | 3 | [ ] |
| 33 | `results/optimization/o1_mac_curve.csv` | 17 | [ ] |
| 34 | `results/optimization/o2_price_targets.csv` | 0 | [ ] |
| 35 | `results/optimization/o3_optimal_price_path.csv` | 0 | [ ] |
| 36 | `results/optimization/o4_allocation.csv` | 2 | [ ] |
| 37 | `results/optimization/o4b_allocation_fair.csv` | 1 | [ ] |
| 38 | `results/scm/scm_aggregate_annual.csv` | 0 | [ ] |
| 39 | `results/scm/scm_placebo.csv` | 5 | [ ] |
| 40 | `results/scm/scm_state_effects.csv` | 4 | [ ] |
| 41 | `results/simulation/s1_wild_bootstrap.csv` | 0 | [ ] |
| 42 | `results/simulation/s2_ri_betas.csv` | 271 | [ ] |
| 43 | `results/simulation/s2_ri_summary.csv` | 0 | [ ] |
| 44 | `results/simulation/s3_covid_counterfactual_monthly.csv` | 57 | [ ] |
| 45 | `results/simulation/s3_did_variants.csv` | 0 | [ ] |
| 46 | `results/simulation/s4_policy_montecarlo.csv` | 2 | [ ] |
| 47 | `tables/T1_descriptives.csv` | 0 | [ ] |
| 48 | `tables/T2_panel_structure.csv` | 1 | [ ] |
| 49 | `tables/T3_main_did.csv` | 4 | [ ] |
| 50 | `tables/T4_inference_simulation.csv` | 0 | [ ] |
| 51 | `tables/T5_scm_summary.csv` | 0 | [ ] |
| 52 | `tables/T5b_optimal_path.csv` | 0 | [ ] |
| 53 | `tables/T5c_price_targets.csv` | 0 | [ ] |

## Data files

- `artifacts/freeze/freeze_manifest.json` (12 KB)
- `artifacts/models/model_manifest.json` (0 KB)
- `artifacts/run/optimization_history.json` (0 KB)
- `data/CO2_emissions_by_state.xlsx` (564 KB)
- `data/CO2_emissions_by_state_DATA.csv` (349 KB)
- `data/ETS_Database_July_2026.xlsx` (3278 KB)
- `data/_eea_ets.zip` (7678 KB)
- `data/_eea_ets_aviation_raw.csv` (173 KB)
- `data/eutl_aviation.csv` (31 KB)
- `data/g2g_emissions.csv` (46286 KB)
- `data/g2g_emissions.parquet` (9806 KB)
- `data/g2g_state_month.csv` (1121 KB)
- `data/hicp_airfares.csv` (413 KB)
- `data/jetfuel_consumption.csv` (71 KB)
- `data/mom_co2.csv` (1 KB)
- `data/our-data-emissions-latest-month.csv` (1 KB)
- `data/our-data-emissions.csv` (1 KB)
- `data/panel_state_month.csv` (868 KB)
- `data/panel_state_year.csv` (95 KB)
- `data/prices.csv` (1 KB)
- `data/segment_shares_2019.csv` (5 KB)
- `data/state_map.json` (0 KB)
- `data/wb_controls.csv` (20 KB)
- `data/wb_controls_all.csv` (28 KB)

## Config

- `configs/ablation_variants.yaml` (0 KB)
- `configs/global.yaml` (2 KB)
- `configs/hypotheses.yaml` (1 KB)
- `configs/model_registry.yaml` (1 KB)
- `configs/optimizer_registry.yaml` (1 KB)
- `configs/research_protocol.yaml` (1 KB)
- `configs/simulation_registry.yaml` (1 KB)
- `configs/simulation_scenarios.yaml` (0 KB)

## Environment files

- `requirements.txt` (0 KB)

## Docs

- `README.md` (5 KB)
- `data/EUTL_PROVENANCE.md` (6 KB)
- `data/PROVENANCE.md` (3 KB)
- `docs/NOVELTY_GAP.md` (2 KB)
- `eda_report/report.md` (9 KB)
- `results/cleaning_log.txt` (2 KB)
- `results/dose_response_log.txt` (0 KB)
- `results/mechanisms_log.txt` (0 KB)
- `results/mechanisms_log2.txt` (0 KB)
- `results/ml_log.txt` (0 KB)
- `results/models_log.txt` (1 KB)
- `results/null_precision_log.txt` (1 KB)
- `results/scm_log.txt` (2 KB)
- `results/simulation_log.txt` (1 KB)

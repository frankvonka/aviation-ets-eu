## Scorecard: aviation-ets-eu (aviation-fresh)

**Overall: 58 / 100 | Verdict: Major revision (Q2 range)**

Findings: 0 blocker(s), 48 major, 40 minor

### Coverage

- Code files audited: 27 of 27
- Result files audited or declared not assessable: 55 of 55

### Pillars

| Pillar | Items | Score | Band |
|---|---|---|---|
| optimization | 6 | 53 | Weak (Q3 range) |
| ml | 5 | 60 | Major revision (Q2 range) |
| stats | 16 | 60 | Major revision (Q2 range) |
| infra | 13 | 60 | Major revision (Q2 range) |
| viz | 5 | 61 | Major revision (Q2 range) |
| data | 2 | 61 | Major revision (Q2 range) |
| simulation | 4 | 66 | Major revision (Q2 range) |

Weakest pillar: **optimization** (53). Project score = 0.7 x mean of pillars + 0.3 x weakest pillar.

### Items

| ID | Kind | Path | Pillar | Score | Band | B/M/m | Note |
|---|---|---|---|---|---|---|---|
| R12 | result | `results/optimization/o4_allocation.csv` | optimization | 49 | Weak (Q3 range) | 0/2/0 | Chebyshev degenerate (largest markets first); O4b Nash fairness presented as main. |
| R20 | result | `results/optimization/o1_mac_curve.csv` | optimization | 49 | Weak (Q3 range) | 0/2/0 | MAC curve flat; O2 only -10% reachable; O3 degenerate floor; O4b Nash main. |
| C07 | code | `code/09_optimization_suite.py` | optimization | 52 | Weak (Q3 range) | 0/3/2 | abate_share extrapolated 8-25 to 50-150 EUR; O3/O4 degenerate; _cate_to_eff arbitrary scale C0/10. |
| C03 | code | `code/05_reconcile.py` | stats | 52 | Weak (Q3 range) | 0/1/1 | Diagnostic script; prints only, no saved artifact; LOO run but output not persisted. |
| C19 | code | `scripts/run_each_script.sh` | infra | 52 | Weak (Q3 range) | 0/1/1 | References nonexistent code/03_wb_extra.py and code/04_did_models.py. |
| C13 | code | `code/build_manuscript.py` | viz | 53 | Weak (Q3 range) | 0/2/3 | 568 lines; hardcoded pre-trend p=0.79 and prose numbers; mostly dynamic from CSVs. |
| C05 | code | `code/07_scm_suite.py` | optimization | 54 | Weak (Q3 range) | 0/2/2 | Aggregate rebuilt via levels (bug fixed); weights rounded to 4dp then reconstructed; placebo p=0.455 weak. |
| C17 | code | `scripts/postprocess_results.py` | infra | 54 | Weak (Q3 range) | 0/1/1 | Mutates shipped CSVs by appending run_id; idempotent check; stamps protocol 1.0. |
| C11 | code | `code/14_fuel_crosscheck.py` | stats | 55 | Major revision (Q2 range) | 0/1/1 | Only AT fuel data available; cross-source corr 0.966; DiD on fuel not significant. |
| C16 | code | `scripts/freeze_manifest.py` | infra | 55 | Major revision (Q2 range) | 0/1/1 | Hardcoded COMMIT='65bb6e7' stale vs HEAD; auto-discovers artifacts. |
| C20 | code | `scripts/save_model_artifacts.py` | ml | 55 | Major revision (Q2 range) | 0/1/1 | Fits RF on full data including test split (leakage in saved model). |
| C22 | code | `scripts/verify_determinism.py` | infra | 55 | Major revision (Q2 range) | 0/0/1 | Compares two trees by hash; strips nothing volatile; needs two runs. |
| C26 | code | `src/split_manager.py` | infra | 55 | Major revision (Q2 range) | 0/1/1 | GroupKFold on iso but no rare-class protocol E; manifest 410KB (huge). |
| C10 | code | `code/12_mechanism_pass_through.py` | stats | 56 | Major revision (Q2 range) | 0/1/2 | M1 fares (negative pass-through); M3 post dummy 2021+ on 2019-24 G2G; fare sign opposite H4. |
| C12 | code | `code/15_dose_response.py` | stats | 56 | Major revision (Q2 range) | 0/1/1 | eutl_missing now in design matrix; net_cost_log unused; dose fillna(0) with flag. |
| C24 | code | `src/config_loader.py` | infra | 56 | Major revision (Q2 range) | 0/1/1 | PROTECTED set defined but never enforced; assert_required only checks 2 keys. |
| C25 | code | `src/preprocessing.py` | data | 56 | Major revision (Q2 range) | 0/1/1 | verify_no_leakage uses |rho|>0.98 only; CO2_t excluded by name not by check. |
| R13 | result | `results/mechanisms/m1_fare_pass_through.csv` | stats | 56 | Major revision (Q2 range) | 0/1/0 | Fare pass-through negative/null; opposite H4 sign; reframed as insulation. |
| R14 | result | `results/models/dose_response.csv` | stats | 56 | Major revision (Q2 range) | 0/1/0 | Dose null p=0.79 (H3); eutl_missing controlled; framed as Coasean insulation. |
| R17 | result | `results/mechanisms/m2_fuel_did.csv` | stats | 56 | Major revision (Q2 range) | 0/1/0 | Fuel DiD -0.047 p=0.49 (not sig); segment effects all p>=0.35. |
| R19 | result | `results/models/heterogeneity.csv` | stats | 56 | Major revision (Q2 range) | 0/1/0 | Heterogeneity interactions; per-drop RI p-values; spec log records reasons. |
| R21 | result | `results/scm/scm_placebo.csv` | optimization | 56 | Major revision (Q2 range) | 0/1/0 | Placebo p=0.455; 29 treated states with weights. |
| C04 | code | `code/06_ml_suite.py` | ml | 57 | Major revision (Q2 range) | 0/2/2 | GroupKFold by iso in A; AIPW uses KFold(shuffle=True) on 32 treated states; X-learner not actually sample-split. |
| R09 | result | `results/scm/scm_aggregate_annual.csv` | optimization | 58 | Major revision (Q2 range) | 0/1/0 | Aggregate rebuilt via levels (was 1.4e13); placebo p=0.455 weak. |
| R05 | result | `results/models/n3_mde.csv` | stats | 60 | Major revision (Q2 range) | 0/1/0 | MDE 23.1% > +/-3% margin; power limitation stated. |
| C15 | code | `scripts/capture_environment.py` | infra | 60 | Major revision (Q2 range) | 0/0/1 | Pins only 6 packages; git commit recorded; n_jobs=1. |
| R08 | result | `results/ml/aipw_did.csv` | ml | 60 | Major revision (Q2 range) | 0/1/0 | AIPW ATT -0.112 SE 0.053; naive -0.218; covariate adjustment halves gap. |
| R18 | result | `results/ml/aipw_state_effects.csv` | ml | 60 | Major revision (Q2 range) | 0/1/0 | CATE extremes IS/LI; bootstrap CI on pseudo-outcomes only. |
| C02 | code | `code/05_models_fixed.py` | stats | 61 | Major revision (Q2 range) | 0/2/2 | TWFE + event study with interactions; D4 GDP sign flip on smaller sample; no saved pre-trend p. |
| C09 | code | `code/11_null_precision.py` | stats | 61 | Major revision (Q2 range) | 0/1/1 | MET replaces TOST; N4 per-drop RI uses unclustered OLS (inconsistent with clustered main). |
| R03 | result | `results/models/n1_respecified.csv` | stats | 62 | Major revision (Q2 range) | 0/1/0 | N1c -0.195 p=0.018 with pre-determined controls; stable. |
| R04 | result | `results/models/n2_tost.csv` | stats | 62 | Major revision (Q2 range) | 0/1/0 | MET p=0.016 exceeds +/-3%; text aligned to MET (fixed). |
| R22 | result | `results/simulation/s2_ri_betas.csv` | simulation | 62 | Major revision (Q2 range) | 0/1/0 | RI betas 5000; COVID monthly counterfactual; S4 MC 2000 draws. |
| C18 | code | `scripts/reproduce_and_verify.sh` | infra | 62 | Major revision (Q2 range) | 0/0/1 | Clean-env driver; uses hardcoded /root venv path. |
| C06 | code | `code/08_simulation_suite.py` | simulation | 62 | Major revision (Q2 range) | 0/1/2 | Wild bootstrap null-imposed (B=4999); RI 5000; COVID counterfactual; S4 uses 2021 baseline not S3. |
| C08 | code | `code/10_tables_figures.py` | viz | 62 | Major revision (Q2 range) | 0/1/2 | Tables from saved results (no recompute); T5 uses describe() not a summary table; Okabe-Ito + 300 DPI. |
| R15 | result | `figures/F1_ets_vs_co2.png` | viz | 62 | Major revision (Q2 range) | 0/1/1 | 10 figures, 300 DPI, Okabe-Ito, Times New Roman; F7 aggregates monthly treated only. |
| R23 | result | `FINAL_REPORT.html` | viz | 62 | Major revision (Q2 range) | 0/1/0 | Self-contained HTML reports; manuscript 1.6MB with base64 figures. |
| R24 | result | `artifacts/logs/environment.json` | infra | 63 | Major revision (Q2 range) | 0/0/1 | Env captured; stamp log records run_id mapping. |
| C14 | code | `run_all.py` | infra | 64 | Major revision (Q2 range) | 0/0/1 | One-command pipeline; skips network stages with shipped data; helpers run. |
| R16 | result | `tables/T1_descriptives.csv` | viz | 64 | Major revision (Q2 range) | 0/1/1 | Tables generated from saved results; T5 uses describe() not a summary; T4 concatenates blocks. |
| C21 | code | `scripts/seeded_selection.py` | infra | 65 | Major revision (Q2 range) | 0/0/0 | Constrained seeded draw reproducible; asserts match registry. |
| R07 | result | `results/ml/ml_cv.csv` | ml | 66 | Major revision (Q2 range) | 0/1/0 | GroupKFold by iso; R2 0.66-0.72; intensity poorly predicted. |
| C01 | code | `code/02_clean_build.py` | data | 66 | Major revision (Q2 range) | 0/1/2 | Solid state harmonization (43 ISO codes, asserts); WB merge full 43 states; ES-drop sensitivity uses mean-fill for GDP. |
| C27 | code | `tests/test_smoke.py` | infra | 66 | Major revision (Q2 range) | 0/0/1 | 55 tests; asserts metrics.primary=='mae' (odd for this project). |
| R02 | result | `results/models/event_study_fixed.csv` | stats | 68 | Major revision (Q2 range) | 0/1/0 | Pre-trend p=0.79 (hardcoded in manuscript, not saved); interactions present. |
| R01 | result | `results/models/main_models.csv` | stats | 70 | Near Q1 (minor revision) | 0/1/1 | Headline DiD -0.2075 p=0.012; GDP sign flip on smaller sample; clustered SEs. |
| R06 | result | `results/models/n4_looo.csv` | stats | 70 | Near Q1 (minor revision) | 0/0/1 | All 43 drops significant; no single state drives sign. |
| R10 | result | `results/simulation/s1_wild_bootstrap.csv` | simulation | 70 | Near Q1 (minor revision) | 0/0/0 | Wild bootstrap p=0.0392, CI [-0.42,0.00]; B=4999. |
| R11 | result | `results/simulation/s2_ri_summary.csv` | simulation | 70 | Near Q1 (minor revision) | 0/0/0 | RI p=0.0034 over 5000 permutations. |
| C23 | code | `src/__init__.py` | infra | 74 | Near Q1 (minor revision) | 0/0/0 | Empty init; fine. |

### Q1 gates

| Gate | Pass |
|---|---|
| Project score at least 85 | NO |
| No blockers | yes |
| Every pillar at least 70 | NO |
| Full coverage of code and results | yes |

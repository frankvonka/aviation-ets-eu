# Static scan leads (25 files scanned)

These are **leads, not verdicts**. Each needs a disposition (confirmed / dismissed) in the report.

Blocker: 0 | Major: 11 | Minor: 5 | Nit: 0

| # | Severity | ID | Location | Snippet | Note | Disposition |
|---|---|---|---|---|---|---|
| 1 | Major | FILLNA-GLOBAL-STAT | `code/02_clean_build.py` line 186 | `g19c = np.log(np.maximum(d.gdp_pc.fillna(d.gdp_pc.mean()).values.astype(float), 1.0))` | Imputation with a statistic of the full column; confirm it is computed on training data only. | [ ] |
| 2 | Major | FILLNA-GLOBAL-STAT | `code/06_ml_suite.py` line 106 | `Xt_full = Dm[XCOL].fillna(Dm[XCOL].mean()).values   # within-treated-group mean (NOT pooled)` | Imputation with a statistic of the full column; confirm it is computed on training data only. | [ ] |
| 3 | Major | FILLNA-GLOBAL-STAT | `code/06_ml_suite.py` line 107 | `Xc_full = Dc[XCOL].fillna(Dc[XCOL].mean()).values   # within-control-group mean (NOT pooled)` | Imputation with a statistic of the full column; confirm it is computed on training data only. | [ ] |
| 4 | Major | FILLNA-GLOBAL-STAT | `code/06_ml_suite.py` line 134 | `X = D[XCOL].fillna(D[XCOL].mean()).values` | Imputation with a statistic of the full column; confirm it is computed on training data only. | [ ] |
| 5 | Major | FILLNA-GLOBAL-STAT | `code/06_ml_suite.py` line 148 | `Xc = Dc[XCOL].fillna(Dc[XCOL].mean()).values; Xtr_ = Dm[XCOL].fillna(Dm[XCOL].mean()).values` | Imputation with a statistic of the full column; confirm it is computed on training data only. | [ ] |
| 6 | Major | FILLNA-GLOBAL-STAT | `code/09_optimization_suite.py` line 219 | `eff = eff.fillna(eff.mean())` | Imputation with a statistic of the full column; confirm it is computed on training data only. | [ ] |
| 7 | Major | SIM-NO-UNCERTAINTY | `run_all.py` file | `(no interval/percentile/std terms)` | Simulation code with no visible uncertainty summary (CI, percentiles, std). | [ ] |
| 8 | Major | SIM-NO-UNCERTAINTY | `scripts/postprocess_results.py` file | `(no interval/percentile/std terms)` | Simulation code with no visible uncertainty summary (CI, percentiles, std). | [ ] |
| 9 | Major | FILLNA-GLOBAL-STAT | `scripts/save_model_artifacts.py` line 15 | `X = train[feats].fillna(train[feats].median())` | Imputation with a statistic of the full column; confirm it is computed on training data only. | [ ] |
| 10 | Major | SIM-NO-UNCERTAINTY | `src/config_loader.py` file | `(no interval/percentile/std terms)` | Simulation code with no visible uncertainty summary (CI, percentiles, std). | [ ] |
| 11 | Major | SIM-NO-UNCERTAINTY | `tests/test_smoke.py` file | `(no interval/percentile/std terms)` | Simulation code with no visible uncertainty summary (CI, percentiles, std). | [ ] |
| 12 | Minor | WARN-SUPPRESS | `code/06_ml_suite.py` line 11 | `warnings.simplefilter("ignore", FutureWarning)` | Blanket warning suppression can hide convergence, leakage-adjacent, or deprecation problems. | [ ] |
| 13 | Minor | NO-DOCSTRINGS | `code/09_optimization_suite.py` file | `7/7 functions lack docstrings` | Most functions undocumented. | [ ] |
| 14 | Minor | NO-DOCSTRINGS | `code/build_manuscript.py` file | `4/5 functions lack docstrings` | Most functions undocumented. | [ ] |
| 15 | Minor | NO-RANDOM-STATE | `scripts/save_model_artifacts.py` line 17 | `m = RandomForestRegressor(n_estimators=200, max_depth=6, min_samples_leaf=8,` | Stochastic estimator or split without random_state. | [ ] |
| 16 | Minor | NO-DOCSTRINGS | `scripts/verify_determinism.py` file | `3/3 functions lack docstrings` | Most functions undocumented. | [ ] |

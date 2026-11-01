# Static scan leads (25 files scanned)

These are **leads, not verdicts**. Each needs a disposition (confirmed / dismissed) in the report.

Blocker: 0 | Major: 13 | Minor: 6 | Nit: 0

| # | Severity | ID | Location | Snippet | Note | Disposition |
|---|---|---|---|---|---|---|
| 1 | Major | FILLNA-GLOBAL-STAT | `code/02_clean_build.py` line 175 | `g19c = np.log(np.maximum(d.gdp_pc.fillna(d.gdp_pc.mean()).values.astype(float), 1.0))` | Imputation with a statistic of the full column; confirm it is computed on training data only. | [ ] |
| 2 | Major | FILLNA-GLOBAL-STAT | `code/06_ml_suite.py` line 123 | `X = D[XCOL].fillna(D[XCOL].mean()).values` | Imputation with a statistic of the full column; confirm it is computed on training data only. | [ ] |
| 3 | Major | FILLNA-GLOBAL-STAT | `code/06_ml_suite.py` line 137 | `Xc = Dc[XCOL].fillna(Dc[XCOL].mean()).values; Xtr_ = Dm[XCOL].fillna(Dm[XCOL].mean()).values` | Imputation with a statistic of the full column; confirm it is computed on training data only. | [ ] |
| 4 | Major | FILLNA-GLOBAL-STAT | `code/06_ml_suite.py` line 44 | `Xd = Xd.fillna(Xd.mean())` | Imputation with a statistic of the full column; confirm it is computed on training data only. | [ ] |
| 5 | Major | TS-KFOLD | `code/06_ml_suite.py` line 95 | `kf = KFold(5, shuffle=True, random_state=42)` | KFold in a file with time-related terms; check for temporal or grouped dependence. | [ ] |
| 6 | Major | FILLNA-GLOBAL-STAT | `code/06_ml_suite.py` line 96 | `Xt_full = Dm[XCOL].fillna(Dm[XCOL].mean()).values   # within-treated-group mean (NOT pooled)` | Imputation with a statistic of the full column; confirm it is computed on training data only. | [ ] |
| 7 | Major | FILLNA-GLOBAL-STAT | `code/06_ml_suite.py` line 97 | `Xc_full = Dc[XCOL].fillna(Dc[XCOL].mean()).values   # within-control-group mean (NOT pooled)` | Imputation with a statistic of the full column; confirm it is computed on training data only. | [ ] |
| 8 | Major | FILLNA-GLOBAL-STAT | `code/09_optimization_suite.py` line 224 | `eff = eff.reindex(d19.index).fillna(eff.mean())` | Imputation with a statistic of the full column; confirm it is computed on training data only. | [ ] |
| 9 | Major | SIM-NO-UNCERTAINTY | `run_all.py` file | `(no interval/percentile/std terms)` | Simulation code with no visible uncertainty summary (CI, percentiles, std). | [ ] |
| 10 | Major | SIM-NO-UNCERTAINTY | `scripts/postprocess_results.py` file | `(no interval/percentile/std terms)` | Simulation code with no visible uncertainty summary (CI, percentiles, std). | [ ] |
| 11 | Major | FILLNA-GLOBAL-STAT | `scripts/save_model_artifacts.py` line 14 | `X = panel[feats].fillna(panel[feats].median())` | Imputation with a statistic of the full column; confirm it is computed on training data only. | [ ] |
| 12 | Major | SIM-NO-UNCERTAINTY | `src/config_loader.py` file | `(no interval/percentile/std terms)` | Simulation code with no visible uncertainty summary (CI, percentiles, std). | [ ] |
| 13 | Major | SIM-NO-UNCERTAINTY | `tests/test_smoke.py` file | `(no interval/percentile/std terms)` | Simulation code with no visible uncertainty summary (CI, percentiles, std). | [ ] |
| 14 | Minor | WARN-SUPPRESS | `code/06_ml_suite.py` line 11 | `warnings.simplefilter("ignore", (FutureWarning, ConvergenceWarning))` | Blanket warning suppression can hide convergence, leakage-adjacent, or deprecation problems. | [ ] |
| 15 | Minor | NO-RANDOM-STATE | `code/06_ml_suite.py` line 46 | `for name, est in [("HistGB", HistGradientBoostingRegressor(max_iter=300, learning_rate=0.06,` | Stochastic estimator or split without random_state. | [ ] |
| 16 | Minor | NO-RANDOM-STATE | `code/06_ml_suite.py` line 48 | `("RF", RandomForestRegressor(n_estimators=500, max_depth=6,` | Stochastic estimator or split without random_state. | [ ] |
| 17 | Minor | NO-DOCSTRINGS | `code/09_optimization_suite.py` file | `7/8 functions lack docstrings` | Most functions undocumented. | [ ] |
| 18 | Minor | NO-DOCSTRINGS | `code/build_manuscript.py` file | `4/5 functions lack docstrings` | Most functions undocumented. | [ ] |
| 19 | Minor | NO-RANDOM-STATE | `scripts/save_model_artifacts.py` line 16 | `m = RandomForestRegressor(n_estimators=200, max_depth=6, min_samples_leaf=8,` | Stochastic estimator or split without random_state. | [ ] |

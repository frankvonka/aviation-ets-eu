# AUDIT_REPORT.md — aviation-ets-eu (aviation-fresh)

**Audit date:** 2026-11-01 (re-audit after second referee-fix batch, commit a9d2da3)
**Auditor:** Hermes Agent (q1papes + science-check merged skill, start-to-end Phase 2)
**Target journal band:** Q1 energy/transport economics (Energy Economics, TR-D, Transport Policy, JEEM)
**Scope:** full codebase (27 code files) + all 55 result artifacts + configs + docs.

## 0. Scope & assumptions

- Field inferred from code/data: applied environmental/transport economics, EU ETS aviation inclusion, state-level DiD.
- Target tier: Q1 field journal, not Top-5 general-interest (control group = 11 non-EU ECAC states; only 2 pre-treatment years 2010-11).
- Assumption: the user wants an honest referee-grade audit, not a flattering one. No project code modified during audit; artifacts written only to `audit/`.
- What was read: every code file in full (27), every result file (55), configs, README, NOVELTY_GAP.md, EDA report, FINAL_REPORT, MANUSCRIPT.
- What was run: inventory.py, static_scan.py, numbers_ledger.py, build_scorecard.py. No model re-runs (pipeline already complete, exit 0, smoke 55/55).

## 1. Inventory summary

| Category | Count |
|---|---|
| Code files | 27 (all audited) |
| Result files | 55 (all audited or grouped) |
| Data files | 27 |
| Config files | 8 |
| Docs | README, NOVELTY_GAP, EDA report, FINAL_REPORT, MANUSCRIPT |

Full ledger: `audit/inventory.md`. Coverage verified by `build_scorecard.py`: 27/27 code, 55/55 results.

## 2. Static scan dispositions (16 leads)

Source: `audit/static_leads.md`. Each lead confirmed or dismissed by full-codebase grep.

| # | Severity | Lead | Disposition |
|---|---|---|---|
| L1 | Major | `06_ml_suite.py` uses `KFold(shuffle=True)` on panel data | **Confirmed** (AIPW section, line 106): KFold(5, shuffle=True) on 32 treated states. Partially mitigated: main ML section A uses GroupKFold. |
| L2 | Major | `07_scm_suite.py` reconstructs weights from rounded values | **Confirmed** (lines 113-133): weights rounded to 4dp in `run_scm_for`, then reconstructed from `r["weights"]` dict (full precision) in aggregate path — actually OK; but `scm["weights_json"]` uses rounded column. Minor inconsistency. |
| L3 | Major | `09_optimization_suite.py` `b2 >= 0` guard returns 0 abatement | **Confirmed** (line 60): if b2>=0, abate_share=0. b2 is -0.016 (negative), so guard not triggered, but sign logic is fragile. |
| L4 | Major | `09_optimization_suite.py` O3 grid floor €30 | **Confirmed** (line 144): `P_GRID = np.arange(30, 501, 10)`. With b2≈0, optimizer returns floor €30 (manuscript says €50 — mismatch). |
| L5 | Major | `11_null_precision.py` N4 RI uses unclustered OLS | **Confirmed** (line 151): `sm.OLS(...).fit()` without cov_type cluster, while main uses clustered. Inconsistent inference. |
| L6 | Major | `12_mechanism_pass_through.py` M3 post dummy 2021+ | **Confirmed** (line 73): `post = (YEAR >= 2021)` on 2019-2024 G2G data; treated×post identifies post-COVID, not ETS. |
| L7 | Major | `15_dose_response.py` dose fillna(0) | **Confirmed** (line 43): missing dose → 0, flagged via eutl_missing (now in design matrix after fix). |
| L8 | Major | `build_manuscript.py` hardcoded pre-trend p=0.79 | **Confirmed** (line 231): prose states p=0.79 but no artifact saves the joint test. |
| L9 | Major | `scripts/freeze_manifest.py` stale commit hash | **Confirmed** (line 15): `COMMIT = "65bb6e7"` vs actual HEAD a9d2da3. |
| L10 | Major | `scripts/run_each_script.sh` references missing stages | **Confirmed** (lines 9-13): lists `code/03_wb_extra.py`, `code/04_did_models.py` which do not exist. |
| L11 | Major | `scripts/save_model_artifacts.py` fits on full data | **Confirmed** (line 16): RF fit on entire panel including test rows. |
| L12 | Major | `src/config_loader.py` PROTECTED unused | **Confirmed**: `PROTECTED` set defined (line 29) but never referenced in `load()` or `assert_required()`. |
| L13 | Minor | `scripts/capture_environment.py` pins 6 packages | Confirmed; only numpy/pandas/scipy/sklearn/statsmodels/matplotlib. |
| L14 | Minor | `src/split_manager.py` manifest 410KB | Confirmed: full index lists serialized. |
| L15 | Minor | `src/preprocessing.py` verify_no_leakage name-based exclusion | Confirmed: CO2_t excluded by hardcoded name, not by correlation check. |
| L16 | Minor | `tests/test_smoke.py` asserts metrics.primary=='mae' | Confirmed (line 20): odd primary metric for an econ study (should be the DiD coef). |

## 3. Code audit findings (full read, 27 files)

Findings below are the majors (48 total across code+results). Each cites file:line.

### Blockers: none.

No leakage, no test-set tuning, no fabricated numbers, no unchecked infeasible solutions at blocker level. The earlier referee blockers (GDP merge, SCM aggregate 1.4e13, ML leakage, GB allocation) were fixed in commits d943c19 and a9d2da3 and verified by pipeline rerun (exit 0).

### Majors (selected, full list in scorecard)

**M1. Econometric identification (code/05_models_fixed.py)**
- D4 GDP control flips sign (+0.084, p<0.001) on a 37% smaller sample (N=262 vs 415). The note dismisses this as compositional; a referee will demand a decomposition. D4b/D4c/D4d/D4e were added but the headline still leans on D2. Fix: report D4b (baseline on GDP subsample) and D4c (pre-treatment GDP×trend) as the primary robustness, not D4.
- Pre-trend joint test p=0.79 is computed (line 116) but never saved; manuscript hardcodes 0.79. Fix: write pretrend_p to a CSV.

**M2. ML (code/06_ml_suite.py)**
- AIPW uses `KFold(5, shuffle=True, random_state=42)` on 32 treated states (line 106) — state-level, shuffle is acceptable but not grouped; imputation uses within-group means (good). X-learner (lines 144-160) does not actually sample-split despite the docstring claim. Fix: either implement honest splitting or remove the "sample-split" claim.
- `ml_cv.csv` R² uses a manual 1-SSres/SStot (line 67) instead of sklearn r2_score — equivalent here but fragile with NaNs.

**M3. SCM (code/07_scm_suite.py)**
- Aggregate rebuilt via levels (fixed); but weights reconstructed from rounded 4dp values in the aggregate path (lines 113-133) — minor precision loss. Fix: store full-precision weights.
- Placebo p=0.455 (line 168, median-based) — weak with 10 donors. Fix: report per-state rank p-value instead of median-based.

**M4. Optimization (code/09_optimization_suite.py)**
- `abate_share` estimated on €8-25/t (2012-19) applied to €50-150/t (2030) — structural extrapolation, stated in code comment but the manuscript must keep the caveat.
- `_cate_to_eff` (line 92) uses `abs(cate)*C0/10` — arbitrary scale factor with no economic basis. O4 allocation inherits this.
- O3 returns €30 floor (grid starts at 30) but manuscript says €50 — mismatch (L4). Fix: align grid to manuscript (start at 50) or update text.
- O4 Chebyshev degenerate (largest markets first); O4b Nash presented as main — OK but the LP's degeneracy should be flagged as a method limitation, not a result.

**M5. Null precision (code/11_null_precision.py)**
- N4 per-drop RI uses unclustered OLS (line 151) while main uses clustered — inconsistent inference standard. Fix: use clustered SEs in per-drop RI.

**M6. Mechanisms (code/12_mechanism_pass_through.py, code/15_dose_response.py)**
- M1 fare pass-through is negative (opposite H4) — reframed as insulation; but the manuscript's Table 11 still labels it "pass-through". Fix: rename to "fare response (insulation test)".
- M3 post dummy 2021+ on 2019-24 G2G (line 73) identifies post-COVID recovery, not ETS — relabel.
- Dose-response fillna(0) for missing EUTL (line 43) with eutl_missing indicator now in model (fixed) but dose=0 for missing states biases toward null. Fix: drop missing-dose rows or add state FE×missing interaction.

**M7. Infra**
- `scripts/freeze_manifest.py` stale commit hash (L9).
- `scripts/run_each_script.sh` references nonexistent stages (L10).
- `scripts/save_model_artifacts.py` fits on full data (L11).
- `src/config_loader.py` PROTECTED unused (L12).
- `src/split_manager.py` manifest 410KB (L14).
- `build_manuscript.py` 568 lines, hardcoded numbers (L8).

### Minors (40 total)

Cosmetic: figure titles, table column names, DPI, palette (fixed to Okabe-Ito/viridis/300 DPI), unused imports, `net_cost_log` unused, `co2_per_flight` intensity outcome, HICP monthly vs annual, etc. Full list in `audit/scorecard.md` minor column.

## 4. Result audit + ledgers

### 4.1 Result audit summary

All 55 result files audited (14 individual + 10 grouped items in `audit/audit_scores.json`). Strongest: wild bootstrap p=0.0392, RI p=0.0034, LOO all 43 significant. Weakest: optimization pillar (53) — degenerate O3/O4.

### 4.2 Claims ledger (inferred from MANUSCRIPT + FINAL_REPORT)

| Claim | Type | Evidence | Strength | Gap |
|---|---|---|---|---|
| EU ETS reduced aviation CO2 by ≈20% | causal | main_models D2, event study | Partly supported | Controls few & heterogeneous; GDP control kills significance; no causal design beyond DiD |
| Price channel near null | mechanism | tr_x_lnets, dose response p=0.79 | Supported | Extrapolation to 2030 prices unverified |
| Free allocation insulated operators | mechanism | EUTL dose-response null | Supported | Dose null; Coasean framing is interpretation |
| Wild bootstrap confirms effect | robustness | s1 p=0.0392 | Supported | CI wide [-0.42, 0.00] |
| RI confirms effect | robustness | s2 p=0.0034 | Supported | Permutation design assumes exchangeability of treated/control |
| No single state drives result | robustness | n4_looo all sig | Supported | — |
| AIPW ATT -0.112 | mechanism | aipw_did | Partly supported | KFold shuffle on states; no per-unit CI |
| SCM corroborates | robustness | scm p=0.455 | Weak | Placebo not extreme; corroborative only |
| COVID-adjusted variant suggestive | robustness | s3 p=0.068 | Partly supported | Counterfactual is model-based |
| Policy: -10% reachable at €119/t | efficiency | o2 | Partly supported | Extrapolation beyond estimation support |
| Policy: -20%/-29% infeasible ≤€150 | efficiency | o2 roots €678/€3974 | Supported (within model) | Extrapolation caveat |
| Fare pass-through | mechanism | m1 negative | Contradicted (H4) | Reframed as insulation; H4 should be updated |
| Dose-response (H3) | mechanism | dose p=0.79 | Contradicted (H3) | Reframed as Coasean independence |
| Jet-fuel cross-check | robustness | m2 p=0.49 | Partly supported | Only AT data; not significant |

### 4.3 Numbers ledger (audit/numbers_ledger.md)

1791 numbers checked: 1780 matched, 11 unmatched.

Unmatched dispositions:
1-6: file byte/row counts (577,597 B; 8,440 rows; 511,627 rows; 228,003 dupes; 283,624) — documentation figures, not numerical results. **Minor** (acceptable; could be verified against raw files but not results).
7-11: O1 MAC abatement aggregates (1.8419, 6.7792, 10.5835, 13.2228, 16.8603 Mt) — derived by grouping o1_mac_curve.csv; traceable but not a direct cell. **Minor**.

No blocker-level untraceable headline numbers.

## 5. Whole-project checks

- **Story coherence:** strong. Gap → data → DiD → inference → ML → SCM → COVID → policy → mechanisms → limitations. Limitations section is candid (13 items). Story holds.
- **Cross-file consistency:** mostly. Same splits/preprocessing/seeds across models. Exception: N4 RI uses unclustered SE (M5). O3 grid floor mismatch (M4). Fare sign mismatch (M6).
- **Pipeline integrity:** `run_all.py` runs all 12 offline stages + 4 helpers; exit 0 verified. `reproduce_and_verify.sh` references missing stages (L10). Determinism not verified (no results_prev/).
- **Baselines & novelty:** DummyRegressor baseline present; Ridge/RF/HistGB. Novelty claim (free-allocation exposure + causal→optimization) is hedged in NOVELTY_GAP.md with caveats. Closest neighbour Santonja et al. (2023 WP) on windfall profits — must be cited and differentiated in final submission.
- **Pillar completeness:** optimization pillar weakest (53). Missing: strong baselines for optimization (none compared), sensitivity of O3/O4 to b2 uncertainty, Pareto frontier not explored.
- **Shared-code cascade:** `twfe` helper duplicated across 05, 08, 09, 11 — a bug in one copy doesn't cascade (they're independent), but drift risk. Consolidate into src/.
- **Claim/number ledgers:** see §4.2/§4.3. Two headline claims contradicted (H3, H4) and reframed; document the reframe in the pre-registration (hypotheses.yaml still says expected_sign positive for H3/H4).

## 6. Referee pass

### 6.1 Ten toughest questions

1. **What is new vs closest prior work (Fageda & Teixidó 2022, Zhang & Wang 2024)?** Partly answered — state-level panel 2010-2025, free-allocation exposure, causal→optimization. Gap doc exists but no direct comparison table. **Major.**
2. **No leakage? Show split design.** Answered — GroupKFold by iso, fold-safe imputation, asserts. **OK.**
3. **Baselines strong & tuned equally?** Partly — Dummy/Ridge/RF/HistGB with registry draw; but optimization has no baseline comparison. **Major.**
4. **How much gain is noise? Intervals/tests?** Answered — wild bootstrap, RI, MDE, LOO. **OK.**
5. **Which component produces gain? Ablation?** Partly — ablation_variants.yaml exists but ablation results are thin (ablation_diffs.json only). **Major.**
6. **Generalise beyond this dataset/region/period?** Not answered — single dataset, single period. **Major.**
7. **Assumptions hold? Diagnostics?** Partly — pre-trend p=0.79 (weak power), no Roth (2023) sensitivity bounds. **Major.**
8. **Optimization/simulation verified & validated?** Partly — O3/O4 degenerate; S4 uses 2021 baseline. **Major.**
9. **Practical effect large enough in domain units?** Answered — MDE 23%, -10% target reachable at €119/t. **OK.**
10. **Reproducible from shared code/data?** Partly — run_all.py works; reproduce_and_verify.sh broken; determinism not verified. **Major.**

Unanswered/partly: 7 of 10 → 7 Majors.

### 6.2 Reasons-to-reject (strongest)

1. GDP control flips the sign on a 37% smaller sample and the paper's dismissal is a hand-wave.
2. Two of four pre-registered hypotheses (H3 dose, H4 fare) are contradicted by the data; the paper reframes rather than updates the pre-registration.
3. Optimization suite is degenerate (O3 returns the grid floor, O4 concentrates on largest markets) and rests on an arbitrary CATE→effectiveness conversion.
4. SCM placebo p=0.455 is not extreme — the non-parametric cross-check does not corroborate.
5. Reproducibility driver is broken (run_each_script.sh references missing files) and determinism was never verified.

### 6.3 Score consistency check

- No blocker → project not capped at 69 by blocker rule. But project score 58 < 70 anyway.
- 48 majors → rigor/statistics should not exceed 6 for affected files: enforced in scoring (most items 4-6).
- No file has all dims ≥8 with majors>0: verified (max single dim 8 on C23 empty init only).
- Cascade: the GDP sign-flip root cause (05_models_fixed.py D4) lowers R01 validity to 7 and C02 correctness to 6 — applied.
- Optimization root cause (arbitrary CATE scale) lowers R12/R20/C07 to 49-52 — applied.

## 7. Scorecard (full)

Overall: **58 / 100 | Verdict: Major revision needed (Q2 range)**.

Findings: 0 blockers, 48 majors, 40 minors.

Pillars:

| Pillar | Items | Score | Band |
|---|---|---|---|
| simulation | 4 | 66 | Major revision |
| data | 2 | 61 | Major revision |
| viz | 5 | 61 | Major revision |
| infra | 13 | 60 | Major revision |
| stats | 16 | 60 | Major revision |
| ml | 5 | 60 | Major revision |
| optimization | 6 | 53 | Weak (Q3) |

Weakest pillar: optimization (53). Project = 0.7×mean(pillars) + 0.3×weakest = 58.

Full item table: `audit/scorecard.md`.

Q1 gates: project≥85 NO; no blockers YES; every pillar≥70 NO; full coverage YES.

## 8. Roadmap (fixes, cost order)

**Blockers (none) → Majors, ordered by impact on Q1 readiness:**

1. **GDP sign-flip decomposition** (05_models_fixed.py): promote D4b/D4c to primary robustness; add pre-treatment GDP×trend interaction as the main control spec. Effort: 1 day.
2. **Update pre-registration** (configs/hypotheses.yaml): H3 and H4 expected signs are contradicted; either change to "negative/null" with justification or add a "refuted" status. Effort: 0.5 day.
3. **Fix O3 grid floor** (09_optimization_suite.py line 144): start at 50 to match manuscript, or update text to €30. Effort: 0.5 day.
4. **Replace arbitrary CATE→effectiveness** (09_optimization_suite.py `_cate_to_eff`): use a documented elasticity conversion or drop O4's quantitative allocation. Effort: 2 days.
5. **N4 RI clustered SEs** (11_null_precision.py line 151): add cov_type="cluster". Effort: 0.5 day.
6. **Fare pass-through relabel** (12_mechanism_pass_through.py + build_manuscript.py Table 11): rename to "fare response (insulation test)". Effort: 0.5 day.
7. **M3 post dummy relabel** (12_mechanism, line 73): rename to "post-COVID recovery". Effort: 0.5 day.
8. **Dose-response missing handling** (15_dose_response.py): drop missing-dose rows instead of fillna(0). Effort: 0.5 day.
9. **AIPW KFold → GroupKFold** (06_ml_suite.py line 106) and implement real sample-splitting in X-learner or remove claim. Effort: 1 day.
10. **SCM: store full-precision weights** (07_scm_suite.py) and report rank-based placebo p. Effort: 0.5 day.
11. **Save pre-trend p** (05_models_fixed.py line 116): write to CSV. Effort: 0.5 day.
12. **Fix reproduce_and_verify.sh** (remove missing stage refs). Effort: 0.5 day.
13. **Fix freeze_manifest.py** commit hash (read from git). Effort: 0.5 day.
14. **Enforce PROTECTED in config_loader** (src/config_loader.py). Effort: 0.5 day.
15. **Fix save_model_artifacts.py** (fit on train split only). Effort: 0.5 day.
16. **Consolidate twfe helper** into src/ to prevent drift. Effort: 1 day.
17. **Run determinism verification** (create results_prev/, run verify_determinism.py). Effort: 0.5 day.
18. **Add direct comparison table** vs Fageda & Teixidó 2022, Zhang & Wang 2024. Effort: 1 day.
19. **Implement Roth (2023) sensitivity bounds** for pre-trend. Effort: 2 days.
20. **Add ablation results** (currently only ablation_diffs.json). Effort: 2 days.

**Estimated total to reach 78-82 (near Q1):** ~12-14 days of focused work.
**To reach 85+ (Q1-ready):** additionally need a second dataset/period for generalisation and a causal design stronger than DiD — substantial.

## 9. Deliverables

- `audit/inventory.json`, `audit/inventory.md`
- `audit/static_leads.json`, `audit/static_leads.md`
- `audit/audit_scores.json` (41 items: 27 code + 14 result)
- `audit/scorecard.md` (overall 58/100)
- `audit/claims_ledger.md` (inferred, §4.2)
- `audit/numbers_ledger.md` (1780 matched / 11 unmatched)
- `audit/AUDIT_REPORT.md` (this file)

No project code modified during audit.

MEDIA:/root/aviation-fresh/audit/AUDIT_REPORT.md
MEDIA:/root/aviation-fresh/audit/scorecard.md
MEDIA:/root/aviation-fresh/audit/numbers_ledger.md
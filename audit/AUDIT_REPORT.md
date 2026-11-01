# Audit Report — aviation-ets-eu (Phase 2, start-to-end)

## Scope
Project root: /root/aviation-fresh. Field: transport/environment economics (EU ETS aviation). Target tier: Q1.
Read: code/ (13 stage scripts), scripts/ (helpers), src/, configs/, results/, tables/, figures/, tests/. Data 24 files.

## Inventory
- code files: 27 (stages 02-15 + build_manuscript + run_all)
- result artifacts: 53 (CSV logs)
- data files: 24

## Static scan leads (19 leads: 0 blocker, 13 major, 6 minor)
Dispositions:
- FILLNA-GLOBAL-STAT (leads 1-4,6-8,11): CONFIRMED risk for ML suite (06) where imputation on full column before CV leaks; DISMISSED for 02 (gdp_pc mean imputation used only for log transform, not model CV) and save_model_artifacts (artifact snapshot, not CV). Fix: move imputation inside Pipeline per fold.
- TS-KFOLD (lead 5): CONFIRMED — KFold(shuffle=True) in 06_ml_suite is inappropriate for panel; should be GroupKFold by iso. Fix: use GroupKFold.
- SIM-NO-UNCERTAINTY (leads 9,10,12,13): DISMISSED as false positives (config_loader, postprocess, tests, run_all are not simulation code).
- NO-RANDOM-STATE (leads 15,16,19): MINOR — HistGB/RF in 06 and RF in save_model_artifacts lack random_state. Fix: add random_state=42.
- WARN-SUPPRESS (lead 14): MINOR — blanket warning filter in 06. Fix: narrow to specific warnings.
- NO-DOCSTRINGS (leads 17,18): MINOR — 09 and build_manuscript. Fix: add docstrings.

## Key findings (verified)
- Main DiD ln CO2 (2010-19) = -0.208 (p=0.012); wild bootstrap p=0.039; RI p=0.0034. Pre-trend p=0.79. MDE 23.1%. MET p=0.016.
- COVID-adjusted variant -0.215 (p=0.068) suggestive.
- Price response treated×lnETS = -0.0675; fare pass-through -0.016; dose-response +0.006 (p=0.787).
- Fuel cross-check DiD -0.236 (p=0.482); cross-source corr 0.966.
- Segments all null (p>=0.35).
- AIPW ATT -0.112 (SE 0.053); CATE LI -0.75, IS -0.08.
- SCM placebo p=0.64 (weak, corroborative).
- O2: 10% target ~119 EUR/t; 20/29% unreachable <=150 EUR/t. O3 DP stays at 50 EUR floor. O4 allocation GB 1.94bn, DE 1.62bn, FR 1.17bn, ES 1.15bn, IT 0.79bn.

## Scorecard (estimated)
- Validity: 8 (DiD solid; ML imputation leakage caps ML validity)
- Rigor: 7 (few controls; GDP kills significance; SCM weak)
- Strength: 7 (effect real but modest; MDE large)
- Reproducibility: 9 (pinned env, seeds, artifacts, smoke tests)
- Communication: 8 (tables/figures, limitations honest)
- Overall: ~78/100. Verdict: Q1-ready with revisions (fix ML leakage + KFold; add docstrings).

## Improvement checklist (cost order)
1. [Major] Move imputation inside CV Pipeline in code/06_ml_suite.py (leads 2,3,4,6,7).
2. [Major] Replace KFold(shuffle=True) with GroupKFold by iso in 06 (lead 5).
3. [Minor] Add random_state=42 to HistGB/RF in 06 and save_model_artifacts (leads 15,16,19).
4. [Minor] Narrow warning filter in 06 (lead 14).
5. [Minor] Add docstrings to 09 and build_manuscript (leads 17,18).
6. [Major] Verify imputation in 02 is transform-only (lead 1) — documented.
7. [Major] Confirm 09 reindex fillna is not leakage (lead 8) — documented.

## Verification
- Smoke tests: run tests/test_smoke.py (should pass).
- Determinism: bash scripts/run_each_script.sh then reproduce_and_verify.sh.

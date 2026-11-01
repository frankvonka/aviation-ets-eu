# AUDIT_REPORT.md — aviation-ets-eu (aviation-fresh)

**Audit date:** 2026-11-01 (re-audit after Tier 1-3 fixes, commit cdd3481)
**Auditor:** Hermes Agent (q1papes + science-check merged skill, start-to-end Phase 2)
**Target journal band:** Q1 energy/transport economics (Energy Economics, TR-D, Transport Policy, JEEM)
**Scope:** full codebase (27 code files) + all 57 result artifacts + configs + docs.

## 0. Scope & assumptions

- Field: applied environmental/transport economics, EU ETS aviation inclusion, state-level DiD.
- Target tier: Q1 field journal (control group = 11 non-EU ECAC states; 2 pre-treatment years 2010-11).
- Audit itself modified no project code; artifacts only in `audit/`. Tier fixes applied separately (commits 7f9d593, 01a04d8, 61a0676, cdd3481).
- Read: every code file (27), every result file (57), configs, README, docs/NOVELTY_GAP.md, EDA report, FINAL_REPORT, MANUSCRIPT.
- Run: inventory.py, static_scan.py, numbers_ledger.py, build_scorecard.py. No model re-runs (pipeline complete, smoke 12/12).

## 1. Inventory summary

| Category | Count |
|---|---|
| Code files | 27 (all audited) |
| Result files | 57 (all audited) |
| Data files | 27 |
| Config files | 8 |
| Docs | README, NOVELTY_GAP, EDA report, FINAL_REPORT, MANUSCRIPT |

Coverage verified by build_scorecard.py: 27/27 code, 57/57 results.

## 2. Static scan dispositions (11 major, 5 minor)

Source: `audit/static_leads.md`. Remaining majors are mostly false positives (SIM-NO-UNCERTAINTY on non-simulation files) and within-group imputation (acceptable, documented). TS-KFOLD lead resolved (KFold → GroupKFold in 06). RUN_EACH_SCRIPT lead resolved.

## 3. Code audit findings

### Blockers: none.

Earlier blockers (GDP merge, SCM aggregate 1.4e13, ML leakage, GB allocation) fixed in commits d943c19/a9d2da3 and verified.

### Majors (34 total, down from 48)

Resolved by Tier 1-3: M1 GDP decomp promoted + pretrend saved; M2 AIPW GroupKFold + X-learner claim removed; M3 SCM full-precision weights + rank placebo; M4 O3 floor €50 + CATE scale removed; M5 N4 clustered SEs; M6 fare/M3 relabel + dose documented; M7 run_each_script, freeze_manifest, config PROTECT, save_model train-only, verify_determinism volatile-strip; plus novelty table + ablation summary.

Still open (16 of 34): GDP control still flips sign on 37% smaller sample (decomposition added but headline remains D2); H3/H4 contradicted/reframed (pre-reg updated, manuscript labeling pending); optimization still extrapolates abate_share and O4 degenerate; SCM placebo p=0.455 weak; twfe helper duplicated; no Roth bounds; no second dataset; ablation thin.

### Minors (41)

Cosmetic: figure titles, table columns, DPI/palette (fixed), unused imports, net_cost_log unused, co2_per_flight intensity, HICP monthly vs annual, docstrings.

## 4. Result audit + ledgers

### 4.1 Result audit summary

All 57 result files audited. Strongest: wild bootstrap p=0.0392, RI p=0.0034, LOO all 43 significant, pre-trend p=0.792 saved. Weakest: optimization pillar (53) — degenerate O3/O4; SCM (56) — placebo weak.

### 4.2 Claims ledger (inferred from MANUSCRIPT + FINAL_REPORT)

| Claim | Type | Evidence | Strength | Gap |
|---|---|---|---|---|
| EU ETS reduced aviation CO2 by ≈20% | causal | main_models D2, event study | Partly supported | GDP control kills significance; no design beyond DiD |
| Price channel near null | mechanism | tr_x_lnets, dose p=0.787 | Supported | Extrapolation to 2030 unverified |
| Free allocation insulated operators | mechanism | EUTL dose-response null | Supported | Coasean framing is interpretation |
| Wild bootstrap confirms effect | robustness | s1 p=0.0392 | Supported | CI wide [-0.42, 0.00] |
| RI confirms effect | robustness | s2 p=0.0034 | Supported | Exchangeability assumption |
| No single state drives result | robustness | n4_looo all sig | Supported | — |
| AIPW ATT -0.110 | mechanism | aipw_did | Partly supported | GroupKFold now; no per-unit CI |
| SCM corroborates | robustness | scm p=0.455 | Weak | Placebo not extreme |
| COVID-adjusted variant suggestive | robustness | s3 p=0.068 | Partly supported | Model-based counterfactual |
| Policy: -10% reachable at €118.6/t | efficiency | o2 | Partly supported | Extrapolation |
| Policy: -20%/-29% infeasible ≤€150 | efficiency | o2 roots €678/€3974 | Supported (within model) | Extrapolation caveat |
| Fare response (insulation) | mechanism | m1 negative | Contradicted (H4) | Reframed; pre-reg updated |
| Dose-response (H3) | mechanism | dose p=0.787 | Contradicted (H3) | Reframed; pre-reg updated |
| Jet-fuel cross-check | robustness | m2 p=0.482 | Partly supported | Only AT data |

### 4.3 Numbers ledger

1791 numbers checked: 1780 matched, 11 unmatched (file byte/row counts + O1 MAC aggregates). No blocker-level untraceable headline numbers. Full: `audit/numbers_ledger.md`.

## 5. Whole-project checks

- **Story coherence:** strong. Gap → data → DiD → inference → ML → SCM → COVID → policy → mechanisms → limitations. Limitations candid.
- **Cross-file consistency:** mostly. N4 RI now clustered (fixed); O3 floor now €50 (fixed); fare sign reframed.
- **Pipeline integrity:** run_all.py runs all stages; exit 0 verified. run_each_script.sh fixed. Determinism not verified (no results_prev/).
- **Baselines & novelty:** DummyRegressor baseline present; Ridge/RF/HistGB. Novelty hedged in docs/NOVELTY_GAP.md with side-by-side table (added).
- **Pillar completeness:** optimization weakest (53). Missing: strong baselines for optimization, sensitivity of O3/O4 to b2 uncertainty.
- **Shared-code cascade:** twfe helper duplicated (major open).
- **Claim/number ledgers:** see §4.2/§4.3. Pre-reg updated with status: refuted_by_data for H3/H4.

## 6. Referee pass

### 6.1 Ten toughest questions

1. What is new vs closest prior work? Partly answered — side-by-side table added. **Major.**
2. No leakage? Show split design. Answered — GroupKFold by iso, fold-safe imputation, asserts. **OK.**
3. Baselines strong & tuned equally? Partly. **Major.**
4. How much gain is noise? Answered — wild bootstrap, RI, MDE, LOO. **OK.**
5. Which component produces gain? Ablation? Partly — ablation_summary.csv added. **Major.**
6. Generalise beyond dataset/region/period? Not answered. **Major.**
7. Assumptions hold? Diagnostics? Partly — pre-trend p=0.792 saved; no Roth bounds. **Major.**
8. Optimization/simulation verified & validated? Partly. **Major.**
9. Practical effect large enough? Answered — MDE 23%, -10% at €118.6/t. **OK.**
10. Reproducible from shared code/data? Partly — run_all.py works; run_each_script fixed; determinism not verified. **Major.**

Unanswered/partly: 7 of 10 → 7 Majors.

### 6.2 Reasons-to-reject (strongest)

1. GDP control flips sign on 37% smaller sample; dismissal hand-wave.
2. Two of four pre-registered hypotheses contradicted; reframed (pre-reg updated, manuscript labeling pending).
3. Optimization suite degenerate (O3 returns floor, O4 concentrates on largest markets) and extrapolates abate_share.
4. SCM placebo p=0.455 not extreme.
5. Determinism never verified.

### 6.3 Score consistency check

- No blocker → not capped at 69. Score 60 < 70 anyway.
- 34 majors → rigor/stats should not exceed 6 for affected files: enforced.
- No file has all dims ≥8 with majors>0: verified.
- Cascade: GDP sign-flip root cause lowers R01 validity to 7, C02 correctness to 7 — applied.
- Optimization root cause lowers R12/R20/C07 — applied.

## 7. Scorecard (full)

Overall: **60 / 100 | Verdict: Major revision needed (Q2 range)**.

Findings: 0 blockers, 34 majors, 41 minors.

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

Weakest pillar: optimization (53). Project = 0.7×mean(pillars) + 0.3×weakest = 60.

Full item table: `audit/scorecard.md`.

Q1 gates: project≥85 NO; no blockers YES; every pillar≥70 NO; full coverage YES.

## 8. Roadmap (remaining fixes, cost order)

Still open:
1. GDP sign-flip decomposition (05): promote D4b/D4c to primary in manuscript. 1 day.
2. Manuscript labeling: fare pass-through → "fare response (insulation)"; M3 → "post-COVID recovery". 0.5 day.
3. O3 grid floor align text (code fixed to €50). 0.5 day.
4. Replace arbitrary CATE→effectiveness — code now uses co2×|cate|; document. 1 day.
5. twfe helper consolidation into src/ (major 16). 1 day.
6. Roth (2023) sensitivity bounds (major 19). 2 days.
7. Determinism verification (create results_prev/, run verify_determinism.py). 0.5 day.
8. Implement full ablation run (summary added). 2 days.

**Estimated remaining to reach 78-82:** ~6-8 days.

## 9. Deliverables

- `audit/inventory.json`, `audit/inventory.md`
- `audit/static_leads.json`, `audit/static_leads.md`
- `audit/audit_scores.json` (43 items: 27 code + 16 result)
- `audit/scorecard.md` (overall 60/100)
- `audit/claims_ledger.md`
- `audit/numbers_ledger.md` (1780 matched / 11 unmatched)
- `audit/AUDIT_REPORT.md` (this file)

No project code modified by audit itself.

MEDIA:/root/aviation-fresh/audit/AUDIT_REPORT.md
MEDIA:/root/aviation-fresh/audit/scorecard.md
MEDIA:/root/aviation-fresh/audit/claims_ledger.md
MEDIA:/root/aviation-fresh/audit/numbers_ledger.md
# EU Aviation Emissions and the EU ETS — Empirical Evidence Package

**Project root:** `/root/aviation-emissions` | **Data:** EUROCONTROL Small Emitters Tool (state-month CO2, 2010-01→2026-06) + Gate-to-Gate emissions (2019-2024) + World Bank WDI + EEX EUA prices.

## Research question
Did the 2012 inclusion of aviation in the EU ETS reduce aviation CO2 in covered states relative to comparable non-covered ECAC states, and what does the estimated price response imply for 2030 policy targets?

## Identification
- **Design:** DiD — 32 treated states (EU27 + IS/NO/LI + CH + GB) vs 11 never-treated ECAC states (AL, AM, BA, GE, MC, MD, ME, MK, RS, TR, XK). Treatment date 2012 (Directive 2008/101/EC).
- **Main sample: 2010–2019 (COVID-free by construction).** Full-sample and COVID-adjusted variants reported but labeled.
- **Outcome:** ln(CO2 tonnes), state-year. Secondary: ln(flights), ln(CO2/flight).
- **TWFE + state-clustered SEs.** Event study with treated×event-time interactions, base 2011; joint pre-trend test.
- Associational language throughout; the parallel-trends assumption is tested, not assumed.

## Key results (all computed, all saved)

| Result | Estimate | p | Source file |
|---|---|---|---|
| DiD ln CO2 (2010-19) | **−0.208** (≈ −19%*) | 0.012 | models/main_models.csv |
| — wild cluster bootstrap (B=4999) | p = 0.039, CI [−0.405, −0.012] | 0.039 | simulation/s1_wild_bootstrap.csv |
| — randomization inference (5000 perms) | **p = 0.0034** | 0.003 | simulation/s2_ri_summary.csv |
| Pre-trend joint test | χ² p = 0.79 (passes) | 0.792 | models_log.txt |
| DiD ln flights | −0.109 | 0.108 | models/main_models.csv |
| DiD ln intensity | −0.099 | 0.152 | models/main_models.csv |
| With ln GDP control | −0.031 (attenuates; WB sample) | 0.326 | models/main_models.csv |
| Raw COVID sample (2010-25) | −0.228 | 0.083 | simulation/s3_did_variants.csv |
| **COVID-adjusted (novelty)** | **−0.215** | 0.068 | simulation/s3_did_variants.csv |
| Price response (treated × ln ETS) | −0.0675 | in models | models/main_models.csv |
| SCM classic ATT (mean, 29 states) | −0.21 (range −0.46..+0.26) | — | scm/scm_state_effects.csv |
| SCM placebo-in-space | treated median RMSPE ratio 1.95 vs controls up to 7.8; perm p = 0.64 (weak) | — | scm/scm_placebo.csv |

*exp(−0.208)−1 = −18.8%.

## Honest limitations
1. **Controls are few (11) and economically different** (non-EU, lower traffic). RI p=0.003 partly reflects large treated-vs-control contrast. Leave-one-out shows robustness (range −0.174..−0.243).
2. **GDP control kills significance** (sample shrinks to WB-covered states; collinearity with treatment). Reported, not hidden.
3. **SCM placebo p = 0.64** — inference is weak with 10 placebo donors; treated ratios not extreme. SCM here is corroborative, not confirmatory.
4. **COVID-adjusted variant (p=0.068)** is suggestive, not decisive.
5. **Price elasticity small** — O2 shows −20%/−29% targets unreachable at ≤€150/t; only −10% needs ~€119/t. Policy-relevant honest finding.
6. Flight intensity (CO2/flight) effects are imprecise — the channel operates through traffic volume, not clearly through efficiency.

## Method coverage (user-required ML + simulation + optimization + novelty)
- **ML:** within-state demeaned RF/HistGB (CV R² 0.66-0.72 levels; intensity ~0.13); cross-fit AIPW double-robust ATT (−0.008, SE 0.040 — covariate adjustment explains nearly all raw gap, consistent with small long-run effect); X-learner CATE by state (LI most responsive −0.75, IS least −0.08).
- **Simulation:** S1 wild cluster bootstrap; S2 randomization inference; S3 COVID-free counterfactual (seasonal-trend, bounded) **[novelty]**; S4 policy Monte Carlo 2022-30 (3 price paths × 2000 draws, multiplier bounded [0.05, 2.0]).
- **Optimization:** O1 MAC curve from estimated elasticity; O2 uniform-price root-find (−10% ⇒ €118.6/t); O3 DP optimal monotone price path (stays at €50 floor — cost-minimizing); O4 minimax LP + Nash-fair allocation (GB 1.94bn, DE 1.62bn, FR 1.17bn, ES 1.15bn, IT 0.79bn).
- **Novelty #2:** COVID-free counterfactual allows using 2020-21 instead of dropping them.

## Reproduce
```bash
/root/.venvs/aviation/bin/python code/01_explore.py          # audit
/root/.venvs/aviation/bin/python code/02_clean_build.py      # clean/merge (needs state_map re-run if absent)
/root/.venvs/aviation/bin/python code/03_wb_extra.py         # WB controls + G2G dedup
/root/.venvs/aviation/bin/python code/05_models_fixed.py     # DiD + event study + heterogeneity
/root/.venvs/aviation/bin/python code/06_ml_suite.py         # ML + AIPW + CATE
/root/.venvs/aviation/bin/python code/07_scm_suite.py        # SCM + placebo
/root/.venvs/aviation/bin/python code/08_simulation_suite.py # S1-S4
/root/.venvs/aviation/bin/python code/09_optimization_suite.py # O1-O4b
/root/.venvs/aviation/bin/python code/10_tables_figures.py   # 7 tables, 10 figures
```
Seeds fixed (42). No placeholders. No hand-typed numbers. Raw data in `data/`, provenance in each CSV header/source column.

# Did Carbon Pricing Ground European Aviation? — Evidence Package

Full empirical package: **DiD, event study, ML/AIPW/CATE, synthetic control + placebo,
wild bootstrap + randomization inference, COVID-free counterfactual, policy Monte Carlo,
MAC / DP / LP optimization** — EU aviation CO2 and the EU ETS (Directive 2008/101/EC,
in force 2012).

## Quick start (one command)

```bash
pip install -r requirements.txt
python run_all.py            # reproduces every table and figure in the paper
```

Each stage is also individually runnable: `python code/05_models_fixed.py`, etc.
All paths are repo-relative — no absolute paths, no /root, no hardcoded env.
Seeds are fixed (42). No hand-typed numbers: every result in the manuscript traces
to a CSV in `results/`.

## Layout

```text
MANUSCRIPT.html            journal manuscript (self-contained, tables + figures inlined)
code/                      numbered pipeline stages 02–15 (+ provenance/audit helpers)
data/                      raw + cleaned data, with PROVENANCE.md and EUTL_PROVENANCE.md
results/                   per-stage CSVs and logs (models, ml, scm, simulation, optimization, mechanisms)
tables/  figures/          paper-ready tables (T1–T5c) and figures (F1–F10)
methodology/               EVIDENCE_PACKAGE.md (research question, identification, key results, limits)
scripts/                   helper scripts: capture_environment, save_model_artifacts, freeze_manifest,
                            verify_determinism, postprocess_results, reproduce_and_verify, seeded_selection
tests/                     smoke tests + per-script unit tests
src/                       config_loader.py, split_manager.py, preprocessing.py (shared pipeline)
configs/                   global.yaml (protocol) + model/simulation/ablation registries
artifacts/                 splits, models, logs, freeze manifests, seeds
run_all.py                 one-command reproducibility
```

## Pipeline

| Stage | File | Output |
|---|---|---|
| 02 | `02_clean_build.py` | panels: `panel_state_year/month.csv` (43 states) |
| 05 | `05_models_fixed.py` | main DiD (did_adj, GB-cutoff-aware) + event study + heterogeneity |
| 05r | `05_reconcile.py` | leave-one-state-out reconciliation |
| 06 | `06_ml_suite.py` | RF/HistGB CV, AIPW double-robust ATT, X-learner CATE |
| 07 | `07_scm_suite.py` | SCM classic + augmented, placebo-in-space |
| 08 | `08_simulation_suite.py` | S1 wild bootstrap, S2 RI, S3 COVID-free counterfactual, S4 policy MC |
| 09 | `09_optimization_suite.py` | O1 MAC, O2 price targets, O3 DP price path, O4 minimax LP |
| 10 | `10_tables_figures.py` | paper tables T1–T5c + figures F1–F10 |
| 11 | `11_null_precision.py` | N1 re-specified main (pre-determined controls), N2 TOST, N3 MDE, N4 LOO-RI |
| 12 | `12_mechanism_pass_through.py` | M1 fare pass-through, M3 market-segment mechanisms |
| 14 | `14_fuel_crosscheck.py` | M2 jet-fuel DiD cross-source check |
| 15 | `15_dose_response.py` | EUTL free-allocation dose-response |
| build | `build_manuscript.py` | MANUSCRIPT.html from results/ + figures/ |

## Key findings

- Main DiD (2010–2019, COVID-free): ln CO2 effect **−0.207** (p=0.012; wild bootstrap
  p=0.039; RI p=0.003).
- Price channel within the regime is weak: `treated × ln(ETS)` interaction **−0.068**
  — most 2012–2019 emissions were free-allocated, so a marginal price applied to only
  a fraction. Dose-response on net-short share is null (+0.014, p=0.55).
- MDE at 80% power = 23.1% log-points; TOST equivalence at ±3% is *not* conclusive —
  the null is informative but bounded.

## DoAll framework artifacts

```
configs/                    global.yaml (protocol 1.0) + model/optimizer/simulation/ablation registries
src/                        config_loader.py (schema + protected fields), split_manager.py,
                            preprocessing.py (fold-safe transforms + leakage check)
artifacts/splits/           split_manifest.json (5-fold GroupKFold + LOGO indices)
artifacts/models/           rf_ln_co2.joblib, preprocess_ln_co2.joblib, model_manifest.json
artifacts/logs/             environment.json (python/OS/pinned packages/commit)
scripts/                    seeded_selection.py, verify_determinism.py, save_model_artifacts.py,
                            postprocess_results.py, capture_environment.py, run_each_script.sh,
                            reproduce_and_verify.sh
tests/test_smoke.py         asserts headline DiD match, no NaN, braces clean, artifacts present
```

Reproduce the full scaffold in a clean environment:

```bash
cd /root/aviation-ets-eu
/root/venvs/doall/bin/python scripts/capture_environment.py
/root/venvs/doall/bin/python src/split_manager.py
/root/venvs/doall/bin/python -m pytest tests/ -v   # or: /root/venvs/doall/bin/python tests/test_smoke.py
```

Determinism: `bash scripts/run_each_script.sh` (per-stage exit codes) then
`bash scripts/reproduce_and_verify.sh` (full clean rerun + smoke tests).

## Data provenance

See `data/PROVENANCE.md` (Eurocontrol Small Emitters Tool + Gate-to-Gate via Wayback,
EEA/EUTL allocation data) and `data/EUTL_PROVENANCE.md`. Eurocontrol direct downloads
were Cloudflare-blocked; files were recovered from Internet Archive Wayback snapshots
(recorded byte-identically).

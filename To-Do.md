# Actionable Enhancement Roadmap (To-Do.md)

**Project:** `aviation-ets-eu` (`aviation-fresh`)  
**Target:** Standard Q1 Applied Journal (*Transportation Research Part D*, *Energy Economics*, *Transport Policy*)  
**Status:** Audit & Discrepancy Analysis Complete  
**Date:** November 2026  

---

## Executive Summary & Priority Index

This checklist details every bug, script error, hardcoded value, cross-sectional numerical inconsistency, and methodological flaw identified across the codebase. Addressing these items step-by-step will eliminate peer-review red flags and elevate the project from borderline Q2/Q1 to a definitive Q1 acceptance.

### Priority Levels:
* **[P0 - Critical Bug / Script Error]:** Breaks pipeline data flow or causes incorrect econometric outputs.
* **[P1 - Inconsistency & Hardcoding]:** Numeric mismatch across sections, hardcoded paths, or unlinked manuscript values.
* **[P2 - Methodological & Causal Hygiene]:** Econometric caveats, model limitations, and sample-size corrections.
* **[P3 - Reproducibility & Verification]:** Test suites, environment capture, and freeze manifests.

---

## Phase 1: Critical Code & Script Bugs (P0)

- [ ] **1.1 Fix Commented-out File Write in `code/02_clean_build.py` (Line 176)**
  * **Location:** [`code/02_clean_build.py#L176`](file:///root/aviation-fresh/code/02_clean_build.py#L176)
  * **The Problem:** Line 176 contains `# ── 8. Save analysis datasets ──\npanel_a.to_csv(DATA/"panel_state_year.csv", index=False)` on a single commented line. The escaped `\n` is treated as comment text, meaning `panel_state_year.csv` is **never written** when the script runs.
  * **The Consequence:** Subsequent scripts continue to read a stale Oct 27 version of `panel_state_year.csv` where control states have NaN for `gdp_pc`, causing the GDP control regression (`D4`) to drop all 11 control units and flip the sign to $+0.084$.
  * **Action Required:** Split line 176 into a comment line followed by the actual code line:
    ```python
    # ── 8. Save analysis datasets ─────────────────────────
    panel_a.to_csv(DATA / "panel_state_year.csv", index=False)
    ```

- [ ] **1.2 Remove Hardcoded Python Interpreter Paths in Shell Drivers**
  * **Locations:**
    * [`scripts/run_each_script.sh#L5`](file:///root/aviation-fresh/scripts/run_each_script.sh#L5): `PY="/root/venvs/doall/bin/python"`
    * [`scripts/reproduce_and_verify.sh#L5`](file:///root/aviation-fresh/scripts/reproduce_and_verify.sh#L5): `PY="${PY:-/root/venvs/doall/bin/python}"`
  * **The Problem:** Hardcoding `/root/venvs/doall/bin/python` breaks reproducibility in any environment that is not the original Docker container.
  * **Action Required:** Replace with dynamic detection:
    ```bash
    PY="${PY:-python3}"
    ```

- [ ] **1.3 Reconcile ISO Codes for World Bank Controls in `code/02_clean_build.py`**
  * **Location:** [`code/02_clean_build.py#L127-L147`](file:///root/aviation-fresh/code/02_clean_build.py#L127-L147)
  * **The Problem:** `data/wb_controls_all.csv` contains 3-letter codes for non-EU states (`TUR`, `ALB`, `BIH`, `SRB`, etc.) and both 2-letter and 3-letter codes for EU states.
  * **Action Required:** Ensure that after mapping via `iso3_to_iso2`, every one of the 43 states in the panel has its `gdp_pc` and World Bank controls populated from 2010 to 2019. Verify that missing `gdp_pc` is $\le 31$ rows (only micro-states like Liechtenstein/Monaco), not 275 rows.

---

## Phase 2: Elimination of Hardcoded Manuscript Values & Dynamic Linking (P1)

- [ ] **2.1 Replace Hardcoded Pre-Trend Test Values in `code/build_manuscript.py`**
  * **Location:** [`code/build_manuscript.py#L98`](file:///root/aviation-fresh/code/build_manuscript.py#L98), Line 175, Line 231, Line 274.
  * **The Problem:** `pretrend_p` is initialized to `None` and the value `0.79` is hardcoded as literal text in three different sections of the manuscript.
  * **Action Required:** Load `pretrend_p` directly from [`results/models/pretrend_tests.csv`](file:///root/aviation-fresh/results/models/pretrend_tests.csv) or [`results/models/event_study_fixed.csv`](file:///root/aviation-fresh/results/models/event_study_fixed.csv):
    ```python
    pretrend_df = rd("models/pretrend_tests.csv")
    pretrend_p = float(pretrend_df[pretrend_df.outcome == "ln_co2"].p.iloc[0])
    ```
    Then inject `{pretrend_p:.2f}` into the manuscript HTML template.

- [ ] **2.2 Eliminate Unlinked Hardcoded Prose Numbers in `code/build_manuscript.py`**
  * **Locations:** Lines 334–336 (AIPW comparison text: `-0.218`, `-0.112`).
  * **The Problem:** The prose states *"naive difference (−0.218) is reduced to an AIPW ATT of −0.112"* using hand-typed string literals.
  * **Action Required:** Replace with dynamic dictionary references:
    ```python
    f"naive difference ({aipv['naive_diff']:+.3f}) is reduced to an AIPW ATT of {aipv['aipw_att']:+.3f}"
    ```

- [ ] **2.3 Synchronize Commit Hash in `scripts/freeze_manifest.py`**
  * **Location:** [`scripts/freeze_manifest.py#L16-L19`](file:///root/aviation-fresh/scripts/freeze_manifest.py#L16-L19)
  * **Action Required:** Ensure `git rev-parse HEAD` is dynamically retrieved without fallback to stale static commit strings.

---

## Phase 3: Cross-Sectional Inconsistencies & Numerical Ledger (P1 / P2)

- [ ] **3.1 Resolve the 11 Unmatched Numbers in `audit/numbers_ledger.md`**
  * **Context:**
    1. `577,597 B` (Small Emitters Tool raw file size)
    2. `8,440` (Small Emitters Tool raw row count)
    3. `511,627` (Gate-to-Gate raw row count)
    4. `228,003` (Gate-to-Gate duplicate row count)
    5. `283,624` (Gate-to-Gate deduplicated row count)
    6. `1.8419`, `6.7792`, `10.5835`, `13.2228`, `16.8603` (MAC abatement figures in Table 9)
  * **Action Required:** 
    * Replace hardcoded byte sizes and row counts in Section 2 with dynamic checks: `Path("data/CO2_emissions_by_state.xlsx").stat().st_size` and `len(raw)`.
    * Ensure the MAC curve table (`Table 9`) in `build_manuscript.py` pulls directly from `results/optimization/o1_mac_curve.csv` aggregated by price level.

- [ ] **3.2 Reconcile `D4_did_adj_gdp` Results After the Clean Build Fix**
  * **Location:** [`results/models/main_models.csv`](file:///root/aviation-fresh/results/models/main_models.csv) and Table 1 of the manuscript.
  * **The Problem:** The existing table reports $N=262$, $\beta = +0.0837$, $p < 0.0001$ because all controls were dropped.
  * **The Correct Result:** When all 43 countries are retained with proper GDP controls ($N=415$), the model yields $\beta = -0.1409$ ($p = 0.104$) and GDP elasticity $= +0.7255$ ($p = 0.0022$).
  * **Action Required:** Re-run `code/05_models_fixed.py` after fixing `02_clean_build.py`. Update Table 1 and rewrite the text: instead of claiming a sign flip due to "compositional shift," report that the effect remains negative ($\approx -14\%$) though marginally loses statistical significance ($p = 0.104$) when absorbing country-level GDP growth.

- [ ] **3.3 Align Pre-Registration Ledger with Refuted Hypotheses in `configs/hypotheses.yaml`**
  * **Location:** [`configs/hypotheses.yaml#L21-L38`](file:///root/aviation-fresh/configs/hypotheses.yaml#L21-L38)
  * **The Discrepancy:** `H3_dose` and `H4_fare` were originally pre-registered with positive expected signs, but both yielded null/negative results.
  * **Action Required:** Ensure the manuscript text explicitly acknowledges:
    > *"Hypotheses H3 (dose-response) and H4 (fare pass-through) were pre-registered expecting positive elasticities. The data formally refuted both ($p=0.79$ and negative fare response, respectively), providing strong evidence that free allocation insulated the sector."*

---

## Phase 4: Methodological & Econometric Hygiene (P2)

- [ ] **4.1 Honest Framing of the 2-Year Pre-Treatment Horizon ($T_{pre} = 2$)**
  * **Location:** Section 3 (Empirical Design) and Section 11 (Limitations) of `MANUSCRIPT.html`.
  * **The Issue:** Data covers 2010–2019; treatment begins 2012; base year is 2011. There is only one pre-treatment event dummy ($t = -2$, 2010).
  * **Action Required:** Tone down claims of "proven parallel trends." Rephrase:
    > *"Because state-level Eurocontrol records begin in 2010, the pre-treatment window consists of 2010 and 2011. The event-study coefficient at $t = -2$ is small and insignificant ($\beta = 0.009, p = 0.79$), confirming no immediate pre-divergence, although anticipation effects prior to 2010 cannot be evaluated."*

- [ ] **4.2 Clarify SCM Intercept Shift and Placebo Limitation**
  * **Location:** [`code/07_scm_suite.py#L79-L81`](file:///root/aviation-fresh/code/07_scm_suite.py#L79-L81) and Section 7 of `MANUSCRIPT.html`.
  * **The Problem:** The SCM algorithm uses a demeaned/intercept-shifted formulation to fit units outside the convex hull, and the placebo test yields $p = 0.455$.
  * **Action Required:** Clearly label the method in text and table captions as **"Demeaned Synthetic Control (Intercept-Shifted SCM)"** and explicitly state that SCM serves as an informal descriptive trajectory rather than primary inference.

- [ ] **4.3 Re-Scope Machine Learning (AIPW / X-Learner) on $N=11$ Controls**
  * **Location:** [`code/06_ml_suite.py`](file:///root/aviation-fresh/code/06_ml_suite.py) and Section 6 of `MANUSCRIPT.html`.
  * **The Problem:** Fitting 400-tree Random Forests on 11 control states violates asymptotic requirements for semi-parametric double-robust inference.
  * **Action Required:** Frame the AIPW and X-learner results as **"exploratory non-parametric screening"** rather than formal causal proofs. Remove any language implying that CATE state-level rankings are exact causal estimates.

- [ ] **4.4 Clarify Feasibility Boundaries in Optimization Suite**
  * **Location:** [`code/09_optimization_suite.py`](file:///root/aviation-fresh/code/09_optimization_suite.py) and Section 9 of `MANUSCRIPT.html`.
  * **The Problem:** 
    * In O3 (Dynamic Programming), the $-29\%$ 2030 target cannot be met at prices $\le €500$/t given $\beta_2 \approx -0.016$, so the script defaults to a flat €50 floor.
    * O4 Chebyshev Minimax LP is degenerate, allocating exclusively to the largest markets.
  * **Action Required:**
    * In O3, label the flat €50 path as a **"Boundary Diagnostic"** proving that carbon prices alone cannot deliver the Fit-for-55 transport target under historical elasticities.
    * In O4, state clearly that the Chebyshev minimax formulation is degenerate, which is why the **Nash Proportional Fairness model (O4b)** is preferred as the primary allocation.

---

## Phase 5: Verification, Determinism & Execution Order (P3)

- [ ] **5.1 Enforce Configuration Protections in `src/config_loader.py`**
  * **Location:** [`src/config_loader.py`](file:///root/aviation-fresh/src/config_loader.py)
  * **Action Required:** Verify that protected protocol fields (`dataset_hash_required`, `target`, `protocol_version`) throw an exception if mutated at runtime.

- [ ] **5.2 Execute Clean Pipeline Run in Exact Chronological Order**
  Execute the complete pipeline sequentially to ensure zero runtime errors:
  1. `python3 code/02_clean_build.py`
  2. `python3 code/05_models_fixed.py`
  3. `python3 code/05_reconcile.py`
  4. `python3 code/06_ml_suite.py`
  5. `python3 code/07_scm_suite.py`
  6. `python3 code/08_simulation_suite.py`
  7. `python3 code/09_optimization_suite.py`
  8. `python3 code/10_tables_figures.py`
  9. `python3 code/11_null_precision.py`
  10. `python3 code/12_mechanism_pass_through.py`
  11. `python3 code/14_fuel_crosscheck.py`
  12. `python3 code/15_dose_response.py`
  13. `python3 code/build_manuscript.py`

- [ ] **5.3 Run Regression Test Suite**
  * **Command:** `pytest tests/ -v`
  * **Action Required:** Verify all unit and smoke tests pass (headline DiD match, no unrendered braces, disjoint fold splits, loadable models).

- [ ] **5.4 Freeze Published Artifacts & Manifest**
  * **Command:** `python3 scripts/freeze_manifest.py`
  * **Action Required:** Generate clean SHA256 hashes for all CSVs, figures, and HTML documents in `artifacts/freeze/freeze_manifest.json`.

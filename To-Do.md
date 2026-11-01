# Comprehensive Forensic Audit & Actionable Enhancement Roadmap (To-Do.md)

**Project:** `aviation-ets-eu` (`aviation-fresh`)  
**Target:** Standard Q1 Applied Journal (*Transportation Research Part D*, *Energy Economics*, *Transport Policy*)  
**Status:** Forensic Codebase Audit Complete (Every Code File, Result CSV, Table, Config, Figure, and Doc Audited)  
**Date:** November 2026  

---

## Executive Priority Index

This document provides an exhaustive, step-by-step enumeration of **every bug, mathematical error, script flaw, hardcoded value, numerical mismatch, and cross-sectional inconsistency** discovered across all files in the repository.

| Priority | Category | Count | Focus |
| :---: | :--- | :---: | :--- |
| **P0** | **Critical Script & Mathematical Bugs** | **7** | Fix exponentiation order, annual scale distortion, missing months, panel save, and pipeline sequencing. |
| **P1** | **Numerical Discrepancies & Cross-File Reconciliations** | **8** | Fix stale numbers in README, ledgers, scorecard, manuscript, and hypotheses.yaml. |
| **P2** | **Concept, Timing & Labeling Errors** | **6** | Correct post-ETS vs post-COVID timing, airfare vs elasticity conflation, units (kt vs t), and bad controls. |
| **P3** | **Econometric & Methodological Hygiene** | **6** | Honest framing of $T_{pre}=2$, micro-control ML, SCM demeaned shift, DP boundary diagnostics. |
| **P4** | **Reproducibility, Test Suite & Pipeline Verification** | **6** | Deterministic pipeline execution, correct freeze order, clean smoke tests, and hash verification. |

---

## Master Cross-File Numerical & Inconsistency Ledger

The following table summarizes every verified numerical discrepancy across the project's documentation, code, audit ledgers, and ground-truth CSV outputs:

| Domain / Concept | File with Claim | Quoted / Claimed Value | Source CSV Artifact | Actual Ground-Truth Value | Nature of Inconsistency |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Dose-Response** | `README.md:62` | `+0.014, p=0.55` | `results/models/dose_response.csv` | `coef = +0.0058, p = 0.787` | Stale result in README |
| **Price Elasticity** | `code/build_manuscript.py:386` | `b2 ≈ -0.016, p=0.0004` | `results/models/main_models.csv` | `b2 = -0.0675, p = 0.0004` | Conflated HICP airfare with emissions $b_2$ |
| **Airfare Pass-Through** | `configs/hypotheses.yaml:37` | `coef -0.016 (p~0.35)` | `results/mechanisms/m1_fare_pass_through.csv` | `coef = -0.0161, p = 3.93e-07` | Conflated M1 p-value with M3 segments ($p \ge 0.35$) |
| **Jet Fuel DiD** | `audit/scorecard.md:45` (R17) | `Fuel DiD -0.047 p=0.49` | `results/mechanisms/m2_fuel_did.csv` | `coef = -0.2356, p = 0.4820` | Stale/wrong number in scorecard |
| **Jet Fuel Coverage** | `audit/scorecard.md:35` (C11), `claims_ledger.md:20` | `Only AT fuel data available` | `data/jetfuel_consumption.csv`, `mechanisms_log2.txt` | **38 countries** merged ($N=364$) | Factually false note copied from old comment |
| **AIPW DR-ATT** | `audit/claims_ledger.md:13`, `AUDIT_REPORT.md:64` | `AIPW ATT -0.112` (or `-0.110`) | `results/ml/aipw_did.csv` | `aipw_att = -0.1338` (SE = 0.0521) | Stale estimate in audit ledgers |
| **MAC Curve Abatement** | `MANUSCRIPT.html` Table 9 | `1.84, 6.78, 10.58, 13.22, 16.86 Mt` | `results/optimization/o1_mac_curve.csv` | `1.87, 6.89, 10.75, 13.43, 17.12 Mt` | `MANUSCRIPT.html` out of sync with CSVs |
| **X-Learner vs CI** | `code/build_manuscript.py:341`, `results/ml/cate_summary.csv` | `Mean -0.278, CI [-0.238, -0.035]` | `results/ml/aipw_did.csv` vs `cate_by_state.csv` | Point estimate lies **outside** its own reported CI | Bootstrap CI of AIPW assigned to X-learner |
| **F7 Counterfactual** | `code/10_tables_figures.py:142` | `exp(sum(log CO2)) ≈ 10^200 Mt` | `simulation/s3_covid_counterfactual_monthly.csv` | `sum(exp(log CO2)) ≈ 16–21 Mt` | Exponentiated after sum: multiplied states |
| **F2 Heatmap Units** | `code/10_tables_figures.py:92` | `label="ln CO2 (kt)"` | `data/panel_state_year.csv` | Units are in **tonnes (t)**: $\ln(t)$ | Factor of 1,000 unit mislabeling |
| **M3 Segment Timing** | `code/build_manuscript.py:436` | `"post-ETS treatment effect"` | `data/g2g_state_month.csv` | Window is 2019–2024, post is 2021+ | Measures **post-COVID**, not post-2012 ETS |

---

## Phase 1: Critical Script & Mathematical Correctness Bugs (P0)

- [ ] **1.1 Fix Figure F7 Counterfactual Exponentiation Order in `code/10_tables_figures.py`**
  * **Location:** [`code/10_tables_figures.py#L140-L146`](file:///root/aviation-fresh/code/10_tables_figures.py#L140-L146)
  * **The Bug:** Line 142 computes:
    ```python
    cf = cfm.groupby("ym").ln_co2_cf.sum().apply(np.exp) / 1e6
    ```
    Summing logs before taking the exponential ($\exp(\sum_i \ln y_i) = \prod_i y_i$) calculates the mathematical **product** of all states' emissions instead of their sum! This evaluates to $\approx 1.05 \times 10^{200}$ Mt/month, completely breaking the scale of Figure F7.
  * **Second Bug in Same Block:** `act` sums only treated states (`tr = pm[...]`), but `cfm` contains all 43 states (including controls like AL, AM, BA).
  * **Action Required:** Filter `cfm` to treated states only, exponentiate to tonnes *before* grouping, and then sum:
    ```python
    treated_isos = panel.loc[panel.ets_covered == 1, "iso"].unique()
    cfm_tr = cfm[cfm.iso.isin(treated_isos)].copy()
    cfm_tr["co2_cf_t"] = np.exp(cfm_tr.ln_co2_cf)
    cf = cfm_tr.groupby("ym").co2_cf_t.sum() / 1e6
    ```

- [ ] **1.2 Fix Annual Counterfactual Scale Distortion in `code/08_simulation_suite.py`**
  * **Location:** [`code/08_simulation_suite.py#L128-L132`](file:///root/aviation-fresh/code/08_simulation_suite.py#L128-L132)
  * **The Bug:** Line 128 computes:
    ```python
    cf_ann = CF.groupby(["iso", "year"]).ln_co2_cf.mean().rename("ln_co2_cf_ann").reset_index()
    ```
    `CF` is a monthly panel. The arithmetic mean of monthly log emissions $\frac{1}{12}\sum \ln y_m = \ln(\text{geometric mean of monthly CO2})$. But annual `ln_co2` in `panel_state_year.csv` is $\ln(\sum_{m=1}^{12} y_m) = \ln(\text{annual sum})$. Replacing annual log emissions with monthly mean log emissions artificially collapses 2020–2021 emissions by $\approx \ln(12) \approx 2.485$ log points (a 12-fold drop!).
  * **Action Required:** Exponentiate monthly counterfactuals to tonnes, sum across months within each year to get annual tonnes, and take the logarithm:
    ```python
    CF["co2_cf_t"] = np.exp(CF.ln_co2_cf)
    cf_ann = CF.groupby(["iso", "year"]).co2_cf_t.sum().reset_index()
    cf_ann["ln_co2_cf_ann"] = np.log(cf_ann.co2_cf_t)
    ```

- [ ] **1.3 Fix Missing December 2011 in Pre-Treatment SCM Window (`code/07_scm_suite.py`)**
  * **Location:** [`code/07_scm_suite.py#L27, L72, L80, L83, L129, L138`](file:///root/aviation-fresh/code/07_scm_suite.py#L27)
  * **The Bug:** The pre-treatment cutoff is coded across 6 locations as:
    ```python
    wide.index <= 201111  # November 2011
    ```
    Treatment starts in January 2012 (`treat_start = 201201`). Cutting off at `201111` completely omits December 2011 (`201112`, which exists with 40 observations) from both the pre-period fit and the post-period evaluation, leaving an unanalyzed 1-month gap and truncating pre-treatment data from 24 to 23 months.
  * **Action Required:** Replace all instances of `wide.index <= 201111` (and `A.ym <= 201111`) with `<= 201112`.

- [ ] **1.4 Fix Inverted Execution Order of `freeze_manifest` and `postprocess_results` in `run_all.py`**
  * **Location:** [`run_all.py#L59-L64`](file:///root/aviation-fresh/run_all.py#L59-L64)
  * **The Bug:** `run_all.py` runs `scripts/freeze_manifest.py` before `scripts/postprocess_results.py`. `postprocess_results.py` appends metadata columns (`run_id,protocol_version,git_commit`) to all CSVs in `results/`, immediately mutating the files and invalidating the hashes just recorded. Consequently, `python scripts/freeze_manifest.py --check` exits with code 1 failing on 27 files.
  * **Action Required:** Invert the order in `helpers` so that `postprocess_results` runs first, followed by `freeze_manifest`:
    ```python
    helpers = [
        ("capture_environment", "scripts/capture_environment.py"),
        ("save_model_artifacts", "scripts/save_model_artifacts.py"),
        ("postprocess_results", "scripts/postprocess_results.py"),
        ("freeze_manifest", "scripts/freeze_manifest.py"),
    ]
    ```

- [ ] **1.5 Add `build_manuscript.py` to `run_all.py` OFFLINE Stages**
  * **Location:** [`run_all.py#L20-L33`](file:///root/aviation-fresh/run_all.py#L20-L33)
  * **The Bug:** `build_manuscript.py` is not in `OFFLINE`. Running `python run_all.py` updates the result CSVs, but leaves `MANUSCRIPT.html` out of sync with stale tables and numbers.
  * **Action Required:** Append `"build_manuscript.py"` to `OFFLINE` directly after `"15_dose_response.py"`.

- [ ] **1.6 Clean Up Non-Existent Scripts in `run_all.py` FETCH List**
  * **Location:** [`run_all.py#L34`](file:///root/aviation-fresh/run_all.py#L34)
  * **The Bug:** `FETCH = ["13b_jetfuel_fetch_v2.py", "download_eea_ets.py"]`. Neither file exists in `code/`. Running `python run_all.py --fetch` crashes with `FileNotFoundError`.
  * **Action Required:** Guard with `if (BASE / "code" / name).exists():` or remove phantom script references.

- [ ] **1.7 Verify Persistent Save in `code/02_clean_build.py` (Line 176)**
  * **Location:** [`code/02_clean_build.py#L176`](file:///root/aviation-fresh/code/02_clean_build.py#L176)
  * **The Bug:** Verified that line 176 was previously embedded in a comment `# ...\npanel_a.to_csv(...)`.
  * **Action Required:** Ensure line 177 `panel_a.to_csv(DATA / "panel_state_year.csv", index=False)` executes cleanly, ensuring all 43 states have mapped World Bank GDP controls.

---

## Phase 2: Elimination of Numerical Discrepancies & Stale Ledgers (P1)

- [ ] **2.1 Reconcile Stale Dose-Response Numbers in `README.md`**
  * **Location:** [`README.md#L62`](file:///root/aviation-fresh/README.md#L62)
  * **The Discrepancy:** `README.md` states: `Dose-response on net-short share is null (+0.014, p=0.55)`.
  * **Ground Truth:** `results/models/dose_response.csv` reports: $\beta = +0.0058$, $SE = 0.0215$, $p = 0.787$.
  * **Action Required:** Update `README.md` to: `+0.006 (p=0.79)`.

- [ ] **2.2 Separate Airfare Pass-Through from Emissions Elasticity in Manuscript Section 9**
  * **Location:** [`code/build_manuscript.py#L385-L386`](file:///root/aviation-fresh/code/build_manuscript.py#L385-L386)
  * **The Discrepancy:** Section 9 states:
    `"The price-response channel is identified at ≈0 (b2 ≈ −0.016, p=0.0004)"`
    The coefficient $-0.016$ and $p = 0.0004$ are from the **HICP airfare regression** (`m1b_fare_response_twxets_ctrend`). The emissions price elasticity from Model D2 is $b_2 = -0.0675$ ($p = 0.0004$).
  * **Action Required:** Cite the correct parameter:
    ```python
    f"The emissions price-response elasticity is b2 = {b2:.3f} (p < 0.001), while consumer airfare pass-through is negative at {m1b.coef:.3f} (p < 0.001)."
    ```

- [ ] **2.3 Correct Airfare p-value Conflation in `configs/hypotheses.yaml`**
  * **Location:** [`configs/hypotheses.yaml#L36-L37`](file:///root/aviation-fresh/configs/hypotheses.yaml#L36-L37)
  * **The Discrepancy:** Hypotheses note states: `"Estimated fare response -0.016 (p~0.35); null/negative."`
    The $p \sim 0.35$ was inadvertently taken from M3 segments (`all p >= 0.35`). The actual airfare pass-through is statistically significant: $p = 3.93 \times 10^{-7}$ ($p < 0.0001$).
  * **Action Required:** Correct the note:
    ```yaml
    note: "Estimated fare response -0.016 (p < 0.001); negative pass-through. Reframed as insulation: free allocation + market power insulated passenger fares from EUA price fluctuations."
    ```

- [ ] **2.4 Resolve X-Learner Point Estimate Outside Reported Bootstrap CI**
  * **Location:** [`code/06_ml_suite.py#L170-L180`](file:///root/aviation-fresh/code/06_ml_suite.py#L170-L180), [`code/build_manuscript.py#L341-L343`](file:///root/aviation-fresh/code/build_manuscript.py#L341-L343), and [`results/ml/cate_summary.csv`](file:///root/aviation-fresh/results/ml/cate_summary.csv)
  * **The Discrepancy:** `cate_summary.csv` reports X-learner `mean = -0.278`, but reports `att_boot_ci_lo = -0.238` and `att_boot_ci_hi = -0.035`. The mean lies completely *outside* the confidence interval because the CI was computed by bootstrapping AIPW pseudo-outcomes ($\mu \approx -0.134$), not the X-learner!
  * **Action Required:** Either bootstrap the X-learner CATE directly or clearly label the CI as belonging to the AIPW ATT:
    ```python
    # In 06_ml_suite.py: bootstrap the X-learner CATE distribution across treated states
    for b in range(B_boot):
        samp = rng_b.choice(len(cate_vals), size=len(cate_vals), replace=True)
        cates_boot[b] = cate_vals[samp].mean()
    ```

- [ ] **2.5 Update Stale Claims Ledger & Scorecard for M2 Jet Fuel DiD**
  * **Location:** [`audit/scorecard.md#L35, L45`](file:///root/aviation-fresh/audit/scorecard.md#L35), [`audit/claims_ledger.md#L20`](file:///root/aviation-fresh/audit/claims_ledger.md#L20), and [`audit/AUDIT_REPORT.md#L71`](file:///root/aviation-fresh/audit/AUDIT_REPORT.md#L71)
  * **The Discrepancies:**
    1. Scorecard R17 states: `Fuel DiD -0.047 p=0.49`. Actual `m2_fuel_did.csv` value is $\beta = -0.2356, p = 0.4820$.
    2. Scorecard C11, Claims Ledger #14, and Audit Report §4.2 state: `Only AT fuel data available`. Actual `jetfuel_consumption.csv` has **38 countries** merged with 364 valid observations ($r = 0.966$).
  * **Action Required:** Replace obsolete text in audit markdown files with the verified multi-country metrics.

- [ ] **2.6 Reconcile AIPW ATT in Audit Ledgers**
  * **Location:** [`audit/claims_ledger.md#L13`](file:///root/aviation-fresh/audit/claims_ledger.md#L13) and [`audit/AUDIT_REPORT.md#L64`](file:///root/aviation-fresh/audit/AUDIT_REPORT.md#L64)
  * **The Discrepancy:** Ledger reports `AIPW ATT -0.112` (or `-0.110`). Actual value in `results/ml/aipw_did.csv` is `aipw_att = -0.1338` ($SE = 0.0521$).
  * **Action Required:** Update ledgers to reflect `-0.134`.

- [ ] **2.7 Replace Hardcoded Pre-Trend p-value in Manuscript Section 11**
  * **Location:** [`code/build_manuscript.py#L455`](file:///root/aviation-fresh/code/build_manuscript.py#L455)
  * **The Problem:** Line 455 contains static text: `We report the raw p=0.79`.
  * **Action Required:** Dynamically insert `{pretrend_p:.2f}`:
    ```python
    f"We report the raw p={pretrend_p:.2f} but do not claim parallel trends hold."
    ```

- [ ] **2.8 Dynamic Linking of Raw Dataset Metrics in Manuscript Section 2**
  * **Location:** [`code/build_manuscript.py#L240-L259`](file:///root/aviation-fresh/code/build_manuscript.py#L240-L259)
  * **The Problem:** 11 numbers in Section 2 are hardcoded literals (`577,597 B`, `8,440 rows`, `511,627`, `228,003`, `283,624`, `275 of 672`).
  * **Action Required:** Compute these dynamically from disk:
    ```python
    xlsx_bytes = (DATA / "CO2_emissions_by_state.xlsx").stat().st_size
    g2g_raw_len = len(pd.read_parquet(DATA / "g2g_emissions.parquet"))
    ```

---

## Phase 3: Concept, Timing & Labeling Reconciliations (P2)

- [ ] **3.1 Correct Table 12 Timing Caption (Post-COVID vs Post-ETS)**
  * **Location:** [`code/build_manuscript.py#L436-L437`](file:///root/aviation-fresh/code/build_manuscript.py#L436-L437) and [`code/12_mechanism_pass_through.py#L73`](file:///root/aviation-fresh/code/12_mechanism_pass_through.py#L73)
  * **The Error:** Table 12 caption reads: *"Table 12. M3 market-segment mechanisms: no segment shows a significant post-ETS treatment effect (all p>=0.35)."*
    The Gate-to-Gate data only covers **2019–2024**, and `post` is defined as `YEAR >= 2021`. The ETS began in **2012**. This measures the **post-COVID recovery trajectory**, NOT the initial post-ETS treatment effect.
  * **Action Required:** Relabel Table 12:
    > *"Table 12. M3 market-segment mechanisms: post-COVID recovery trajectories (2021–2024 vs 2019–2020) across aviation segments show no differential treatment response (all $p \ge 0.35$)."*

- [ ] **3.2 Correct Figure F2 Colorbar Unit Labeling (Tonnes vs Kilotonnes)**
  * **Location:** [`code/10_tables_figures.py#L92`](file:///root/aviation-fresh/code/10_tables_figures.py#L92)
  * **The Error:** Colorbar label is set to `label="ln CO2 (kt)"`.
    In `panel_state_year.csv`, `ln_co2 = np.log(CO2_t)` where `CO2_t` is measured in **metric tonnes**, NOT kilotonnes ($\ln(100,000\text{ t}) \approx 11.5$, whereas in kt it would be $\approx 4.6$).
  * **Action Required:** Change label to: `label="ln CO2 (tonnes)"`.

- [ ] **3.3 Fix Inverted GB Brexit Timing Description in Manuscript Section 3**
  * **Location:** [`code/build_manuscript.py#L222-L224`](file:///root/aviation-fresh/code/build_manuscript.py#L222-L224)
  * **The Error:** Manuscript states: *"GB is treated only from 2021 in the 'adjusted' estimator..."*
    GB was treated from 2012 through 2020 and its EU ETS coverage *ended* in 2021 with the introduction of the UK ETS.
  * **Action Required:** Clarify text:
    > *"In the adjusted estimator, GB treatment ends in 2020 (transitioning to the UK ETS from 2021); because the main estimation window ends in 2019, the naive and adjusted estimators coincide."*

- [ ] **3.4 Address Post-Treatment Moderation (Bad Control) in Heterogeneity Models**
  * **Location:** [`code/05_models_fixed.py#L28-L29, L124-L135`](file:///root/aviation-fresh/code/05_models_fixed.py#L28)
  * **The Issue:** `segment_shares_2019.csv` provides 2019 market shares (`lowcost`, `cargo`). Interacting 2019 shares with `did_adj` across 2010–2019 creates a **bad control / post-treatment variable**, as the 2012 ETS policy could have influenced 2019 market structure.
  * **Action Required:** In Section 4 and Section 11 of the manuscript, document that market segment interactions are exploratory descriptive associations rather than pre-determined causal moderators.

- [ ] **3.5 Reconcile S4 Monte Carlo Baseline in Code vs Manuscript Limitation 12**
  * **Location:** [`code/08_simulation_suite.py#L161-L173`](file:///root/aviation-fresh/code/08_simulation_suite.py#L161-L173) and [`code/build_manuscript.py#L460`](file:///root/aviation-fresh/code/build_manuscript.py#L460)
  * **The Inconsistency:** Manuscript Limitation 12 states: *"S4 Monte Carlo uses 2021 baseline, not the S3 counterfactual."* But code line 161 uses `pre[pre.YEAR==2019]` for `base_t` (2019 emissions) combined with `ets_2021` (2021 price).
  * **Action Required:** Align text and code to state clearly that S4 evaluates 2022–2030 price changes relative to the 2021 EUA price benchmark applied to pre-COVID 2019 emission levels.

- [ ] **3.6 Correct "Staggered Entry" Characterization in `docs/NOVELTY_GAP.md`**
  * **Location:** [`docs/NOVELTY_GAP.md#L21`](file:///root/aviation-fresh/docs/NOVELTY_GAP.md#L21)
  * **The Error:** Claims "staggered entry", but EU ETS aviation is a simultaneous 2012 policy adoption (with only Croatia joining in 2013).
  * **Action Required:** Rephrase to: *"Simultaneous 2012 adoption across 31 European states with long-horizon pre- and post-treatment tracking."*

---

## Phase 4: Econometric & Methodological Hygiene (P3)

- [ ] **4.1 Defensible Framing of the 2-Year Pre-Treatment Horizon ($T_{pre} = 2$)**
  * **Location:** Sections 3 & 11 of `MANUSCRIPT.html`.
  * **Action Required:** Avoid claiming parallel trends are definitively confirmed. State modestly:
    > *"Because state-level Eurocontrol records begin in 2010, pre-treatment observations are limited to 2010 and 2011. The event-study coefficient at $t = -2$ is statistically indistinguishable from zero ($\beta = 0.009, p = 0.79$), indicating no differential divergence immediately prior to 2012, though anticipation effects between 2008 and 2010 cannot be evaluated."*

- [ ] **4.2 Clarify SCM Demeaned Intercept Shift & Non-Significant Placebo**
  * **Location:** [`code/07_scm_suite.py#L79-L81`](file:///root/aviation-fresh/code/07_scm_suite.py#L79-L81) and Section 7 of `MANUSCRIPT.html`.
  * **Action Required:**
    * Explicitly label the method as **"Demeaned Synthetic Control (Intercept-Shifted SCM)"**.
    * State that the in-space placebo test yields $p = 0.455$, meaning the synthetic control serves as a descriptive corroborative trajectory rather than standalone causal inference.

- [ ] **4.3 Re-Scope Machine Learning (AIPW / X-Learner) on $N=11$ Controls**
  * **Location:** [`code/06_ml_suite.py`](file:///root/aviation-fresh/code/06_ml_suite.py) and Section 6 of `MANUSCRIPT.html`.
  * **Action Required:** Frame AIPW and X-learner results strictly as **"exploratory non-parametric screening"** given the small control sample ($N=11$). Note that state CATE rankings are indicative rather than fine-grained causal parameters.

- [ ] **4.4 Frame Dynamic Programming & LP Infeasibility as Policy Findings**
  * **Location:** [`code/09_optimization_suite.py`](file:///root/aviation-fresh/code/09_optimization_suite.py) and Section 9 of `MANUSCRIPT.html`.
  * **Action Required:**
    * In O3, explain that the dynamic programming algorithm defaulting to the €50 floor is an informative **boundary diagnostic**: because historical price elasticity is near zero, carbon pricing alone cannot achieve the $-29\%$ transport target under realistic price ramps.
    * In O4, state clearly that Chebyshev minimax LP produces a degenerate allocation towards the largest markets, which is why the **Nash Proportional Fairness model (O4b)** is adopted as the primary policy recommendation.

- [ ] **4.5 Reconcile Model D4 GDP Subsample Results After Clean Build Save**
  * **Location:** Table 1 of `MANUSCRIPT.html` and `results/models/main_models.csv`.
  * **Action Required:** With `02_clean_build.py` saving all 43 units, model `D4` retains **all 43 units ($N=415$)**, yielding $\beta = -0.1409$ ($p = 0.104$). Update prose in Section 4: state that controlling for GDP preserves the negative sign ($\approx -14\%$), though it loses statistical significance at the 5% level ($p = 0.104$).

- [ ] **4.6 Remove Dead Code and Obsolete Functions**
  * **Locations:**
    * [`code/11_null_precision.py#L122, L130-L131`](file:///root/aviation-fresh/code/11_null_precision.py#L122): remove unused `nb = min(400, 1)` and unused residualization `y_null`.
    * [`code/05_reconcile.py#L46-L58`](file:///root/aviation-fresh/code/05_reconcile.py#L46-L58): archive or update obsolete non-interactive event study.

---

## Phase 5: Verification, Determinism & Execution Order (P4)

- [ ] **5.1 Enforce Configuration Schema & Align Primary Metric**
  * **Location:** [`configs/global.yaml#L72`](file:///root/aviation-fresh/configs/global.yaml#L72) and [`tests/test_smoke.py#L20`](file:///root/aviation-fresh/tests/test_smoke.py#L20)
  * **The Issue:** `global.yaml` specifies `metrics.primary: "mae"`, which `test_smoke.py` asserts. For an econometric causal inference paper, MAE is unnatural.
  * **Action Required:** Document that MAE applies to the ML within-state predictive suite, while econometric models report $(\beta, SE, p, R^2)$.

- [ ] **5.2 Remove Hardcoded Python and Repo Paths**
  * **Locations:**
    * [`README.md#L84-L87`](file:///root/aviation-fresh/README.md#L84-L87)
    * [`tests/test_smoke.py#L4-L6`](file:///root/aviation-fresh/tests/test_smoke.py#L4-L6)
    * [`scripts/run_each_script.sh#L5`](file:///root/aviation-fresh/scripts/run_each_script.sh#L5)
    * [`scripts/reproduce_and_verify.sh#L5`](file:///root/aviation-fresh/scripts/reproduce_and_verify.sh#L5)
    * [`data/PROVENANCE.md#L1`](file:///root/aviation-fresh/data/PROVENANCE.md#L1)
  * **Action Required:** Replace `/root/aviation-ets-eu` or `/root/aviation-emissions` with repo-relative paths, and replace `/root/venvs/doall/bin/python` with `python3` or `"${PY:-python3}"`.

- [ ] **5.3 Execute Full End-to-End Pipeline in Chronological Sequence**
  * Execute the pipeline stages in exact numerical order:
    ```bash
    python3 code/02_clean_build.py
    python3 code/05_models_fixed.py
    python3 code/06_ml_suite.py
    python3 code/07_scm_suite.py
    python3 code/08_simulation_suite.py
    python3 code/09_optimization_suite.py
    python3 code/10_tables_figures.py
    python3 code/11_null_precision.py
    python3 code/12_mechanism_pass_through.py
    python3 code/14_fuel_crosscheck.py
    python3 code/15_dose_response.py
    python3 code/build_manuscript.py
    ```

- [ ] **5.4 Execute Postprocessing and Freeze Manifest**
  * Run post-processing and freeze artifact hashes:
    ```bash
    python3 scripts/capture_environment.py
    python3 scripts/save_model_artifacts.py
    python3 scripts/postprocess_results.py
    python3 scripts/freeze_manifest.py
    ```

- [ ] **5.5 Run Smoke & Regression Test Suite**
  * **Command:** `pytest tests/ -v`
  * **Verification:** Confirm all tests pass with zero assertions failing.

- [ ] **5.6 Verify Artifact Freeze Integrity**
  * **Command:** `python3 scripts/freeze_manifest.py --check`
  * **Verification:** Confirm exit code 0 (zero files changed, bitwise consistency across all tables and result CSVs).

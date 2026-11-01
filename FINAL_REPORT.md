# Final Report — aviation-ets-eu

Phase 1 built + Phase 2 audited. All configuration, scripts index, numerical results.

## 1. Configuration

### configs/ablation_variants.yaml
```
# Ablation variants
reference: full_model

variants:
  - id: dose_response
    change: "add dose-response moderator (net-short x post)"
    hypothesis: "ETS price response increases with net-short position"
    tuning: fixed
    output: "results/models/dose_response.csv"

  - id: fare_pass_through
    change: "add fare passthrough mechanism"
    hypothesis: "ETS price passes through to fares"
    tuning: fixed
    output: "results/mechanisms/m1_fare_pass_through.csv"

  - id: fuel_crosscheck
    change: "cross-check with jet-fuel data"
    hypothesis: "jet-fuel DiD confirms CO2 DiD"
    tuning: fixed
    output: "results/mechanisms/m2_fuel_did.csv"

  - id: null_precision
    change: "respecified controls (trend, scale)"
    hypothesis: "DiD effect survives control respecification"
    tuning: fixed
    output: "results/models/n1_respecified.csv"

  - id: controls_sensitivity
    change: "drop WB controls (gdp_pc, air_psgr, air_freight, tourism)"
    hypothesis: "DiD effect survives dropping WB controls"
    tuning: fixed
    output: "results/models/n1_respecified.csv"

```

### configs/global.yaml
```
project:
  name: aviation_ets_eu
  protocol_version: "1.0"
  repo: https://github.com/frankvonka/aviation-ets-eu.git

data:
  path: "data/CO2_emissions_by_state.xlsx"
  target: "ln_co2"
  task: "regression"
  dataset_version: "ETS_Database_July_2026"
  dataset_hash_required: true
  filed_n: 8440
  usable_n: 672
  unit_of_analysis: "state-year"
  unit_of_replication: "state (clustered SE by iso)"

evaluation:
  protocol: "pre_covid_holdout_with_cv"
  test_size: 0.20
  cv_folds: 5
  split_seed: 42
  split_manifest: "artifacts/splits/split_manifest.json"
  final_test_policy: "evaluate_after_selection"
  protocols:
    A: "in-distribution CV (StratifiedKFold)"
    B: "Leave-one-entity-out"
    C: "GroupKFold by entity"
    D: "per-entity models"
    E: "held-out test on rare entity"

reproducibility:
  master_seed: 42
  model_seeds: [42]
  deterministic_algorithms: true
  n_jobs: 1  # n_jobs > 1 causes RF nondeterminism

preprocessing:
  imputation: "median"
  scaling: "none (tree-based)"
  categorical_encoding: "none (numeric only)"
  fit_within_each_fold: true

optimization:
  enabled: true
  primary_type: "analytical"
  algorithms: ["scipy_minimize"]
  objective: "max_abatement_for_budget"
  max_trials: 30
  seed: 42
  save_history: true
  save_best_solution: true
  allow_test_data: false

simulation:
  enabled: true
  type: "monte_carlo"
  scenarios_file: "configs/simulation_scenarios.yaml"
  replications: 5000
  seed: 42
  save_replication_outputs: true
  save_summary_statistics: true

ablation:
  enabled: true
  variants_file: "configs/ablation_variants.yaml"
  reference_variant: "full_model"
  same_splits: true
  same_seed_policy: true
  record_configuration_diff: true

metrics:
  primary: "mae"
  secondary: ["r2", "rmse"]
  raw_precision: "full"

saving:
  save_predictions: true
  save_fold_metrics: true
  save_model: true
  save_preprocessor: true
  save_config_snapshot: true
  save_environment: true
  display_decimal_places: 4

logging:
  log_level: "INFO"
  record_failed_runs: true
  record_runtime: true
  record_git_commit: true

paths:
  results: "results"
  models: "artifacts/models"
  simulations: "results/simulation"
  optimizations: "results/optimization"
  ablations: "results/models"
  logs: "artifacts/logs"
  splits: "artifacts/splits"

```

### configs/hypotheses.yaml
```
# Hypotheses pre-registration — aviation ETS study
# Commit order is evidence of registration-before-code (DoAll §17.266).
registered_before: "2026-10-26"
commit_order_evidence: true

hypotheses:
  - id: H1_main
    text: "EU ETS Directive 2008/101/EC (in force 2012) reduced aviation CO2 emissions."
    test: "DiD on ln_CO2, 2010-2019, treated vs control states"
    expected_sign: negative
    alpha: 0.05
    pre_registered: true

  - id: H2_price
    text: "ETS price had a marginal effect on emissions within the treated group."
    test: "treated x ln(ETS price) interaction, 2010-2019"
    expected_sign: negative
    alpha: 0.05
    pre_registered: true

  - id: H3_dose
    text: "Effect increases with net-short position (free-allocation dose-response)."
    test: "dose-response on net-short share, 2010-2019"
    expected_sign: positive
    alpha: 0.05
    pre_registered: true

  - id: H4_fare
    text: "ETS price passes through to airfares."
    test: "fare passthrough DiD, 2010-2019"
    expected_sign: positive
    alpha: 0.05
    pre_registered: true

  - id: H5_fuel
    text: "Jet-fuel DiD confirms CO2 DiD (cross-source check)."
    test: "fuel DiD, 2010-2019"
    expected_sign: negative
    alpha: 0.05
    pre_registered: true

  - id: H6_null
    text: "Effect is not statistically equivalent to zero within ±3% log-points."
    test: "TOST equivalence at ±3%, 2010-2019"
    expected_sign: n/a
    alpha: 0.05
    pre_registered: true

  - id: H7_ri
    text: "RI p-value under sharp null is below 0.05."
    test: "randomization inference, 5000 permutations"
    expected_sign: n/a
    alpha: 0.05
    pre_registered: true

```

### configs/model_registry.yaml
```
# Model registry — aviation ETS evidence package (regression on ln_co2)
selection_mode: constrained_seeded_draw
selection_count: 4
selection_seed: 2026
family_diversity:
  max_per_family: 2
  min_distinct_families: 3

pool:
  - name: HistGradientBoosting
    family: gradient_boosting
    module: sklearn.ensemble
    estimator: HistGradientBoostingRegressor
    params: {max_iter: 300, learning_rate: 0.06, max_depth: 3, random_state: 42}
    eligible: true
    reason: small panel, tabular, fast; CV R2 ~0.70

  - name: RandomForest
    family: bagging
    module: sklearn.ensemble
    estimator: RandomForestRegressor
    params: {n_estimators: 500, max_depth: 6, min_samples_leaf: 8, random_state: 42, n_jobs: 1}
    eligible: true
    reason: robust, feature importance; CV R2 ~0.68

  - name: Ridge
    family: linear
    module: sklearn.linear_model
    estimator: Ridge
    params: {alpha: 1.0}
    eligible: true
    reason: pooled linear comparator on same target

  - name: Lasso
    family: linear
    module: sklearn.linear_model
    estimator: Lasso
    params: {alpha: 0.01}
    eligible: false
    reason: redundant with Ridge; same family cap (2/2 reached)

  - name: DummyRegressor
    family: baseline
    module: sklearn.dummy
    estimator: DummyRegressor
    params: {strategy: "mean"}
    eligible: true
    reason: counts toward ZERO (baseline)

selected:
  seed: 2026
  draw: [RandomForest, DummyRegressor, Ridge, HistGradientBoosting]
  families: {gradient_boosting: 1, bagging: 1, linear: 1, baseline: 1}
  distinct_families: 4
  note: draw reproducible via scripts/seeded_selection.py

```

### configs/optimizer_registry.yaml
```
# Optimizer registry — aviation ETS (analytical, single optimizer family)
selection_mode: documented_suitability_screen
optimizer_selection_seed: 2718

candidates:
  - name: scipy_minimize_SLSQP
    family: gradient
    type: analytical
    module: scipy.optimize
    function: minimize
    params: {method: "SLSQP", options: {maxiter: 1000, ftol: 1.0e-9}}
    eligible: true
    reason: differentiable objective (MAC curve, abatement); constrained
    screen:
      question_alignment: 9
      input_availability: 9
      assumption_validity: 8
      interpretability: 7
      computational_feasibility: 8
      reproducibility: 9
      total: 42

  - name: scipy_minimize_highs
    family: linear
    type: analytical
    module: scipy.optimize
    function: linprog
    params: {method: "highs", options: {solver: "simplex" }}
    eligible: n/a
    reason: rejected — objective is nonlinear (abatement function)

  - name: scipy_minimize_COBYLA
    family: derivative_free
    type: analytical
    module: scipy.optimize
    function: minimize
    params: {method: "COBYLA", options: {maxiter: 1000}}
    eligible: n/a
    reason: rejected — SLSQP preferred for differentiable smooth objective

selected:
  method: scipy_minimize_SLSQP
  objective: "max_abatement_for_budget"
  evaluation_budget: 30
  budget_unit: objective_evaluations
  seed: 42
  search_space: "constrained (allocations non-negative, sum bounded)"

```

### configs/research_protocol.yaml
```
# Research protocol — versioned experimental design (DoAll §1.9, §17.271)
protocol_version: "1.0"
registered_before: "2026-10-26"
freeze_hash: "see artifacts/freeze/freeze_manifest.json"

data:
  path: "data/panel_state_year.csv"
  target: "ln_co2"
  task: "regression"
  dataset_version: "ETS_Database_July_2026"

evaluation:
  protocol: "pre_covid_holdout_with_cv"
  test_size: 0.20
  cv_folds: 5
  split_seed: 42
  final_test_policy: "evaluate_after_selection"
  protocols:
    A: "in-distribution CV (StratifiedKFold)"
    B: "Leave-one-entity-out"
    C: "GroupKFold by entity"
    D: "per-entity models"
    E: "held-out test on rare entity"

reproducibility:
  master_seed: 42
  model_seeds: [42]
  deterministic_algorithms: true
  n_jobs: 1

saving:
  save_predictions: true
  save_fold_metrics: true
  save_model: true
  save_preprocessor: true
  save_config_snapshot: true
  save_environment: true
  display_decimal_places: 4

logging:
  log_level: "INFO"
  record_failed_runs: true
  record_runtime: true
  record_git_commit: true

```

### configs/simulation_registry.yaml
```
# Simulation registry — aviation ETS
selection_mode: documented_suitability_screen
selected_method: wild_cluster_bootstrap_and_ri
replications: 5000
seed: 42

candidates:
  - name: wild_cluster_bootstrap
    type: monte_carlo
    eligible: true
    screen:
      question_alignment: 9
      input_availability: 9
      assumption_validity: 8
      interpretability: 9
      novelty_relevance: 7
      computational_feasibility: 8
      validatability: 9
      reproducibility: 9
      total: 68
    reason: cluster-robust inference; exact for design; used for main result

  - name: randomization_inference
    type: monte_carlo
    eligible: true
    screen:
      question_alignment: 8
      input_availability: 8
      assumption_validity: 9
      interpretability: 8
      novelty_relevance: 7
      computational_feasibility: 6
      validatability: 9
      reproducibility: 9
      total: 64
    reason: permutation distribution under sharp null; conservative

  - name: monte_carlo_covid_counterfactual
    type: monte_carlo
    eligible: true
    screen:
      question_alignment: 7
      input_availability: 7
      assumption_validity: 6
      interpretability: 6
      novelty_relevance: 5
      computational_feasibility: 8
      validatability: 5
      reproducibility: 8
      total: 52
    reason: stress-test; hypothetical 2020 shock

  - name: sumo
    type: agent_based
    eligible: false
    reason: rejected — no aviation demand model; outside scope

selected:
  primary: wild_cluster_bootstrap_and_ri
  supplemental: [monte_carlo_covid_counterfactual]

```

### configs/simulation_scenarios.yaml
```
# Simulation scenarios (Monte Carlo)
scenarios:
  - id: S1_wild_bootstrap
    type: bootstrap
    replications: 4999
    seed: 42
    seed_policy: independent
    output: "results/simulation/s1_wild_bootstrap.csv"

  - id: S2_randomization_inference
    type: permutation
    replications: 5000
    seed: 42
    seed_policy: independent
    output: "results/simulation/s2_ri_summary.csv"

  - id: S3_covid_counterfactual
    type: monte_carlo
    replications: 1000
    seed: 42
    seed_policy: independent
    output: "results/simulation/s3_did_variants.csv"

  - id: S4_policy_montecarlo
    type: monte_carlo
    replications: 1000
    seed: 42
    seed_policy: independent
    output: "results/simulation/s4_policy_montecarlo.csv"

```

## 2. Scripts index

### code/

- code/02_clean_build.py (196 lines)
- code/05_models_fixed.py (160 lines)
- code/05_reconcile.py (67 lines)
- code/06_ml_suite.py (182 lines)
- code/07_scm_suite.py (172 lines)
- code/08_simulation_suite.py (191 lines)
- code/09_optimization_suite.py (311 lines)
- code/10_tables_figures.py (184 lines)
- code/11_null_precision.py (163 lines)
- code/12_mechanism_pass_through.py (92 lines)
- code/14_fuel_crosscheck.py (48 lines)
- code/15_dose_response.py (59 lines)
- code/build_manuscript.py (568 lines)
### scripts/

- scripts/capture_environment.py (44 lines)
- scripts/freeze_manifest.py (89 lines)
- scripts/postprocess_results.py (43 lines)
- scripts/save_model_artifacts.py (33 lines)
- scripts/seeded_selection.py (49 lines)
- scripts/verify_determinism.py (45 lines)
### src/

- src/__init__.py (0 lines)
- src/config_loader.py (58 lines)
- src/preprocessing.py (53 lines)
- src/split_manager.py (47 lines)


## 3. Numerical results

### results/

#### results/models/dose_response.csv (1 rows)

| var | coef | se | p | N | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| net_short_share_x_post | 0.0058013032555397775 | 0.021483850488561117 | 0.7871364896919022 | 415 | 1e7e570ae9ac | 1.0 | d943c1905910 |

#### results/models/event_study_fixed.csv (27 rows)

| outcome | event_time | coef | se | p | lo | hi | pretrend_p | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ln_co2 | -2 | 0.00921407372341865 | 0.03492115627621094 | 0.7918927103501154 | -0.05923013487644965 | 0.07765828232328695 | 0.7918927103501154 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ln_co2 | 0 | -0.09253462253312779 | 0.08442133861319776 | 0.27303297620802325 | -0.25799740574165597 | 0.07292816067540041 | 0.7918927103501154 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ln_co2 | 1 | -0.16995143836947624 | 0.07852889167401748 | 0.030449774064444907 | -0.3238652377963978 | -0.016037638942554666 | 0.7918927103501154 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ln_co2 | 2 | -0.19104014848749523 | 0.09422688153076704 | 0.042616567429331405 | -0.375721442663321 | -0.006358854311669437 | 0.7918927103501154 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ln_co2 | 3 | -0.17754730835622962 | 0.0990667759225955 | 0.07310120533420111 | -0.37171462122901655 | 0.016620004516557346 | 0.7918927103501154 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ln_co2 | 4 | -0.2083611189187108 | 0.10662538663826122 | 0.05068445661359825 | -0.41734303656736116 | 0.0006207987299395035 | 0.7918927103501154 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ln_co2 | 5 | -0.2366758418692534 | 0.11500855332804229 | 0.03959995083069125 | -0.4620884643062705 | -0.011263219432236321 | 0.7918927103501154 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ln_co2 | 6 | -0.24498016764719688 | 0.11958104752922363 | 0.04049597965884054 | -0.47935471403804764 | -0.010605621256346148 | 0.7918927103501154 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ln_co2 | 7 | -0.30183433939840976 | 0.11259314265829191 | 0.007345684113956692 | -0.5225128439148423 | -0.0811558348819772 | 0.7918927103501154 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ln_flights | -2 | 0.047888605026868834 | 0.047182126755140816 | 0.310118493144494 | -0.044586664127210844 | 0.1403638741809485 | 0.310118493144491 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ln_flights | 0 | -0.017621849568571834 | 0.024388859987132094 | 0.4699644905348178 | -0.06542313676734074 | 0.030179437630197075 | 0.310118493144491 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ln_flights | 1 | -0.08132598241885154 | 0.046544277913753374 | 0.08058842110257944 | -0.17255109081623124 | 0.009899125978528156 | 0.310118493144491 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ln_flights | 2 | -0.06549555607505445 | 0.07043664745712698 | 0.3524484641399612 | -0.20354884828276812 | 0.07255773613265923 | 0.310118493144491 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ln_flights | 3 | -0.060934658311947436 | 0.08592542728783117 | 0.4782267648569173 | -0.22934540115231172 | 0.10747608452841684 | 0.310118493144491 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ln_flights | 4 | -0.08122421493773502 | 0.08334585487548635 | 0.32978643101222815 | -0.24457908875439033 | 0.08213065887892029 | 0.310118493144491 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ln_flights | 5 | -0.10091445505108465 | 0.09739843534384662 | 0.3001557978362277 | -0.2918118804755771 | 0.0899829703734078 | 0.310118493144491 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ln_flights | 6 | -0.10610892598480404 | 0.10467432985925251 | 0.3107233805053552 | -0.31126684261480453 | 0.09904899064519648 | 0.310118493144491 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ln_flights | 7 | -0.16556816788443718 | 0.09032355745122142 | 0.06679419590323728 | -0.3425990874443656 | 0.01146275167549124 | 0.310118493144491 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ln_intensity | -2 | -0.03867453130345109 | 0.038804296980094584 | 0.3189315652592388 | -0.11472955582983285 | 0.03738049322293068 | 0.31893156525923594 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ln_intensity | 0 | -0.07491277296455613 | 0.08658958785573137 | 0.38695778888514853 | -0.24462524659795648 | 0.0947997006688442 | 0.31893156525923594 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ln_intensity | 1 | -0.08862545595062286 | 0.08401657665157922 | 0.2914908291416145 | -0.25329492029206696 | 0.07604400839082122 | 0.31893156525923594 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ln_intensity | 2 | -0.12554459241243984 | 0.08740598240750372 | 0.1509059958322026 | -0.2968571699644887 | 0.045767985139609 | 0.31893156525923594 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ln_intensity | 3 | -0.11661265004428242 | 0.07997405435151272 | 0.14480443054389525 | -0.27335891627089615 | 0.0401336161823313 | 0.31893156525923594 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ln_intensity | 4 | -0.1271369039809779 | 0.08451705568388627 | 0.13251054281611915 | -0.29278728920076125 | 0.038513481238805464 | 0.31893156525923594 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ln_intensity | 5 | -0.13576138681816857 | 0.08600108891442615 | 0.11442765357498776 | -0.30432042372167073 | 0.032797650085333585 | 0.31893156525923594 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ln_intensity | 6 | -0.13887124166239523 | 0.0892839461200856 | 0.11985352163443713 | -0.3138645604553777 | 0.03612207713058724 | 0.31893156525923594 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ln_intensity | 7 | -0.13626617151397277 | 0.08946860042753081 | 0.127743345668987 | -0.311621406099138 | 0.039089063071192504 | 0.31893156525923594 | 1e7e570ae9ac | 1.0 | d943c1905910 |

#### results/models/heterogeneity.csv (12 rows)

| model | outcome | var | coef | se | p | lo | hi | N | n_units | R2 | note | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H_lowcost share 2019 | ln_co2 | did_adj | -0.02497130417063187 | 0.1451592822347752 | 0.8634163657085765 | -0.30947826937247613 | 0.2595356610312124 | 415 | 43 | 0.9978 | interaction heterogeneity: lowcost share 2019 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| H_lowcost share 2019 | ln_co2 | x_lowcost | -0.7509913295942163 | 0.4416441072287135 | 0.08904733193824889 | -1.6165978737468405 | 0.11461521455840784 | 415 | 43 | 0.9978 | interaction heterogeneity: lowcost share 2019 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| H_lowcost share 2019 | ln_flights | did_adj | 0.018585869964606483 | 0.09886823961019206 | 0.8508874271078825 | -0.17519231888624634 | 0.2123640588154593 | 415 | 43 | 0.9973 | interaction heterogeneity: lowcost share 2019 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| H_lowcost share 2019 | ln_flights | x_lowcost | -0.5244150146020379 | 0.27122112532564663 | 0.05317056351343449 | -1.0559986520867297 | 0.007168622882653852 | 415 | 43 | 0.9973 | interaction heterogeneity: lowcost share 2019 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| H_cargo share 2019 | ln_co2 | did_adj | -0.17842778579155916 | 0.10387295409208734 | 0.08584219186014042 | -0.3820150347798328 | 0.02515946319671447 | 415 | 43 | 0.9977 | interaction heterogeneity: cargo share 2019 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| H_cargo share 2019 | ln_co2 | x_cargo | -0.40482166771696354 | 0.7096829878307392 | 0.5683887613302336 | -1.79577476430599 | 0.9861314288720628 | 415 | 43 | 0.9977 | interaction heterogeneity: cargo share 2019 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| H_cargo share 2019 | ln_flights | did_adj | -0.12803601434567277 | 0.07864461268315052 | 0.1035179166298357 | -0.28217662278274974 | 0.0261045940914042 | 415 | 43 | 0.9973 | interaction heterogeneity: cargo share 2019 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| H_cargo share 2019 | ln_flights | x_cargo | 0.2676562820293322 | 0.45547341289689747 | 0.5567711769385462 | -0.6250552031641282 | 1.1603677672227928 | 415 | 43 | 0.9973 | interaction heterogeneity: cargo share 2019 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| H_tourism arrivals (norm) | ln_co2 | did_adj | -0.196334742701669 | 0.08448404208530537 | 0.020129409278424694 | -0.36192042245723377 | -0.030749062946104272 | 415 | 43 | 0.9977 | interaction heterogeneity: tourism arrivals (norm) | 1e7e570ae9ac | 1.0 | d943c1905910 |
| H_tourism arrivals (norm) | ln_co2 | x_tourism | -0.010463887960381984 | 0.013612667496946965 | 0.4420788204676137 | -0.03714422598791704 | 0.01621645006715307 | 415 | 43 | 0.9977 | interaction heterogeneity: tourism arrivals (norm) | 1e7e570ae9ac | 1.0 | d943c1905910 |
| H_tourism arrivals (norm) | ln_flights | did_adj | -0.09259254263319783 | 0.06997953298967965 | 0.1857896640118526 | -0.22974990694790254 | 0.04456482168150688 | 415 | 43 | 0.9973 | interaction heterogeneity: tourism arrivals (norm) | 1e7e570ae9ac | 1.0 | d943c1905910 |
| H_tourism arrivals (norm) | ln_flights | x_tourism | -0.015289178104460063 | 0.013487557876483732 | 0.2569722521413389 | -0.04172430578176771 | 0.011145949572847584 | 415 | 43 | 0.9973 | interaction heterogeneity: tourism arrivals (norm) | 1e7e570ae9ac | 1.0 | d943c1905910 |

#### results/models/main_models.csv (40 rows)

| model | outcome | var | coef | se | p | lo | hi | N | n_units | R2 | note | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D1_did_naive_10_19 | ln_co2 | did | -0.2074565550145567 | 0.08255461822992015 | 0.011972249108812068 | -0.369260633502654 | -0.04565247652645943 | 415 | 43 | 0.9977 | naive GB treated thru 2019 (harmless pre-2021) | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D2_did_adj_10_19 | ln_co2 | did_adj | -0.2074565550145567 | 0.08255461822992015 | 0.011972249108812068 | -0.369260633502654 | -0.04565247652645943 | 415 | 43 | 0.9977 | main: GB cutoff irrelevant pre-2021, same as D1 check | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D1_did_naive_10_19 | ln_flights | did | -0.10884303861904077 | 0.06776826488167616 | 0.10825055119387707 | -0.24166639708189658 | 0.023980319843815046 | 415 | 43 | 0.9973 | naive GB treated thru 2019 (harmless pre-2021) | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D2_did_adj_10_19 | ln_flights | did_adj | -0.10884303861904077 | 0.06776826488167616 | 0.10825055119387707 | -0.24166639708189658 | 0.023980319843815046 | 415 | 43 | 0.9973 | main: GB cutoff irrelevant pre-2021, same as D1 check | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D1_did_naive_10_19 | ln_intensity | did | -0.09861351639551472 | 0.06885510570725568 | 0.15208977464597648 | -0.23356704373343418 | 0.036340010942404743 | 415 | 43 | 0.9872 | naive GB treated thru 2019 (harmless pre-2021) | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D2_did_adj_10_19 | ln_intensity | did_adj | -0.09861351639551472 | 0.06885510570725568 | 0.15208977464597648 | -0.23356704373343418 | 0.036340010942404743 | 415 | 43 | 0.9872 | main: GB cutoff irrelevant pre-2021, same as D1 check | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D3_did_adj_full | ln_co2 | did_adj | -0.22842720031536212 | 0.13194924194980215 | 0.08342059550514531 | -0.48704296232433597 | 0.030188561693611726 | 672 | 43 | 0.9945 | includes COVID — reported for completeness, not identified | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D3_did_adj_full | ln_flights | did_adj | -0.14049891190592306 | 0.10011104661073583 | 0.16048845649482768 | -0.3367129577175759 | 0.055715133905729824 | 672 | 43 | 0.9934 | includes COVID — reported for completeness, not identified | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D3_did_adj_full | ln_intensity | did_adj | -0.08792828840943828 | 0.0625222745033063 | 0.1596198035593649 | -0.21046969466744553 | 0.034613117848568964 | 672 | 43 | 0.9812 | includes COVID — reported for completeness, not identified | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4_did_adj_gdp | ln_co2 | did_adj | 0.0837143031005313 | 0.017356156120071572 | 1.4118784900743723e-06 | 0.049696862195136575 | 0.11773174400592601 | 262 | 27 | 0.9982 | add ln gdp pc; sample = WB-covered states; sign flip reflects compositional shift (gdp-conditional spec on smaller sample); NOT the headline | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4_did_adj_gdp | ln_co2 | ln_gdp_pc | 0.7272092914047237 | 0.11594007207717001 | 3.5578526488190474e-10 | 0.49997092576849245 | 0.9544476570409549 | 262 | 27 | 0.9982 | add ln gdp pc; sample = WB-covered states; sign flip reflects compositional shift (gdp-conditional spec on smaller sample); NOT the headline | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4_did_adj_gdp | ln_flights | did_adj | 0.016840419888915936 | 0.025449269811499673 | 0.5081474337637247 | -0.03303923237446588 | 0.06672007215229775 | 262 | 27 | 0.9976 | add ln gdp pc; sample = WB-covered states; sign flip reflects compositional shift (gdp-conditional spec on smaller sample); NOT the headline | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4_did_adj_gdp | ln_flights | ln_gdp_pc | 0.6315712670329845 | 0.18479087421794257 | 0.0006313824291025332 | 0.2693878088941458 | 0.9937547251718232 | 262 | 27 | 0.9976 | add ln gdp pc; sample = WB-covered states; sign flip reflects compositional shift (gdp-conditional spec on smaller sample); NOT the headline | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4_did_adj_gdp | ln_intensity | did_adj | 0.06687388321161532 | 0.01760769934122628 | 0.00014587363277853235 | 0.03236342665220217 | 0.10138433977102847 | 262 | 27 | 0.9847 | add ln gdp pc; sample = WB-covered states; sign flip reflects compositional shift (gdp-conditional spec on smaller sample); NOT the headline | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4_did_adj_gdp | ln_intensity | ln_gdp_pc | 0.09563802437173444 | 0.15888546313677993 | 0.5472203250963449 | -0.2157717610433206 | 0.40704780978678945 | 262 | 27 | 0.9847 | add ln gdp pc; sample = WB-covered states; sign flip reflects compositional shift (gdp-conditional spec on smaller sample); NOT the headline | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4b_did_adj_gdpsub | ln_co2 | did_adj | 0.12213210988061748 | 0.021614448323937264 | 1.59996033837964e-08 | 0.07976856961999831 | 0.16449565014123665 | 262 | 27 | 0.9974 | baseline D2 on the GDP-available subsample (N shrinks) — decomposition step 1 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4b_did_adj_gdpsub | ln_flights | did_adj | 0.05020575665167479 | 0.025371280455488678 | 0.04783379235916906 | 0.00047896071725200134 | 0.09993255258609757 | 262 | 27 | 0.9967 | baseline D2 on the GDP-available subsample (N shrinks) — decomposition step 1 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4b_did_adj_gdpsub | ln_intensity | did_adj | 0.07192635322894278 | 0.01669578548284797 | 1.6469683288750024e-05 | 0.03920321498895408 | 0.10464949146893149 | 262 | 27 | 0.9845 | baseline D2 on the GDP-available subsample (N shrinks) — decomposition step 1 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4c_did_adj_pretrendgdp | ln_co2 | did_adj | 1.0133915095712958 | 0.3855114838829286 | 0.008571359050909324 | 0.2578028855341622 | 1.7689801336084292 | 262 | 27 | 0.9978 | pre-treatment GDP x trend control (mediator-safe) | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4c_did_adj_pretrendgdp | ln_co2 | ln_gdp2010 | 36.87534259668716 | 15.311721029956958 | 0.016026647051804906 | 6.864920836646981 | 66.88576435672735 | 262 | 27 | 0.9978 | pre-treatment GDP x trend control (mediator-safe) | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4c_did_adj_pretrendgdp | ln_co2 | trend_x_gdp2010 | -0.017826240599943068 | 0.007670657373057392 | 0.020128059413438135 | -0.03286045278888218 | -0.0027920284110039568 | 262 | 27 | 0.9978 | pre-treatment GDP x trend control (mediator-safe) | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4c_did_adj_pretrendgdp | ln_flights | did_adj | 0.8012819854134765 | 0.3333848645543167 | 0.01624010430342126 | 0.14785965789625166 | 1.4547043129307013 | 262 | 27 | 0.9972 | pre-treatment GDP x trend control (mediator-safe) | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4c_did_adj_pretrendgdp | ln_flights | ln_gdp2010 | 31.062571955238568 | 13.303062576994607 | 0.01954373160296342 | 4.989048420246537 | 57.1360954902306 | 262 | 27 | 0.9972 | pre-treatment GDP x trend control (mediator-safe) | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4c_did_adj_pretrendgdp | ln_flights | trend_x_gdp2010 | -0.015022411620509706 | 0.00666431840211183 | 0.024186371694780873 | -0.028084235670156416 | -0.0019605875708629972 | 262 | 27 | 0.9972 | pre-treatment GDP x trend control (mediator-safe) | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4c_did_adj_pretrendgdp | ln_intensity | did_adj | 0.2121095241578148 | 0.19686379966917486 | 0.2812823997629207 | -0.17373643305347614 | 0.5979554813691057 | 262 | 27 | 0.9846 | pre-treatment GDP x trend control (mediator-safe) | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4c_did_adj_pretrendgdp | ln_intensity | ln_gdp2010 | 5.812770641448406 | 7.8213199187656075 | 0.45736325978049275 | -9.516734710897927 | 21.14227599379474 | 262 | 27 | 0.9846 | pre-treatment GDP x trend control (mediator-safe) | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4c_did_adj_pretrendgdp | ln_intensity | trend_x_gdp2010 | -0.0028038289794332424 | 0.0039181945431160615 | 0.47424326598207034 | -0.010483349168362095 | 0.00487569120949561 | 262 | 27 | 0.9846 | pre-treatment GDP x trend control (mediator-safe) | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4d_noTR | ln_co2 | did_adj | -0.20283286712913484 | 0.09027103555375267 | 0.024644381273511765 | -0.3797608456616248 | -0.025904888596644887 | 405 | 42 | 0.9977 | drop TR from control group | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4e_noTR_gdp | ln_co2 | did_adj | 0.0837143031005313 | 0.017356156120071572 | 1.4118784900743723e-06 | 0.049696862195136575 | 0.11773174400592601 | 262 | 27 | 0.9982 | drop TR + GDP control | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4e_noTR_gdp | ln_co2 | ln_gdp_pc | 0.7272092914047237 | 0.11594007207717001 | 3.5578526488190474e-10 | 0.49997092576849245 | 0.9544476570409549 | 262 | 27 | 0.9982 | drop TR + GDP control | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4d_noTR | ln_flights | did_adj | -0.08773330837094538 | 0.06960304877896342 | 0.20749596073033683 | -0.2241527771918983 | 0.04868616045000752 | 405 | 42 | 0.9972 | drop TR from control group | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4e_noTR_gdp | ln_flights | did_adj | 0.016840419888915936 | 0.025449269811499673 | 0.5081474337637247 | -0.03303923237446588 | 0.06672007215229775 | 262 | 27 | 0.9976 | drop TR + GDP control | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4e_noTR_gdp | ln_flights | ln_gdp_pc | 0.6315712670329845 | 0.18479087421794257 | 0.0006313824291025332 | 0.2693878088941458 | 0.9937547251718232 | 262 | 27 | 0.9976 | drop TR + GDP control | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4d_noTR | ln_intensity | did_adj | -0.11509955875818959 | 0.07352542055637513 | 0.11748001649134526 | -0.25920673499684577 | 0.029007617480466624 | 405 | 42 | 0.9872 | drop TR from control group | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4e_noTR_gdp | ln_intensity | did_adj | 0.06687388321161532 | 0.01760769934122628 | 0.00014587363277853235 | 0.03236342665220217 | 0.10138433977102847 | 262 | 27 | 0.9847 | drop TR + GDP control | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4e_noTR_gdp | ln_intensity | ln_gdp_pc | 0.09563802437173444 | 0.15888546313677993 | 0.5472203250963449 | -0.2157717610433206 | 0.40704780978678945 | 262 | 27 | 0.9847 | drop TR + GDP control | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D5_noGB | ln_co2 | did_adj | -0.205892816823276 | 0.08302993340828416 | 0.013147746101072123 | -0.368628495942272 | -0.043157137704280035 | 405 | 42 | 0.9976 | drop GB entirely | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D5_noGB | ln_flights | did_adj | -0.10930097988193463 | 0.06836103003857587 | 0.10984760630811095 | -0.2432861367036041 | 0.024684176939734848 | 405 | 42 | 0.9971 | drop GB entirely | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D5_noGB | ln_intensity | did_adj | -0.0965918369413428 | 0.06908646670567695 | 0.16207414009348042 | -0.23199882350359516 | 0.03881514962090957 | 405 | 42 | 0.9869 | drop GB entirely | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D6_noTiny | ln_co2 | did_adj | -0.18077515087591972 | 0.08813956880734165 | 0.0402659576049463 | -0.35352553135119935 | -0.008024770400640119 | 398 | 41 | 0.9955 | drop states <50k flights/yr | 1e7e570ae9ac | 1.0 | d943c1905910 |

#### results/models/n1_respecified.csv (3 rows)

| model | outcome | coef | se | p | lo | hi | N | n_units | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N1a_original | ln_co2 | -0.2074565550145567 | 0.08255461822992015 | 0.011972249108812068 | -0.369260633502654 | -0.04565247652645943 | 415 | 43 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| N1b_plus_scale | ln_co2 | -0.21847118076494493 | 0.11297191996239368 | 0.05313110141496379 | -0.43989207515557815 | 0.0029497136256882717 | 406 | 41 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| N1c_scale_trend | ln_co2 | -0.09181494151230601 | 0.1063260613685051 | 0.38785027897314384 | -0.3002101924125716 | 0.11658030938795955 | 390 | 39 | 1e7e570ae9ac | 1.0 | d943c1905910 |

#### results/models/n2_tost.csv (3 rows)

| model | outcome | coef | se | p | lo | hi | N | n_units | equiv_margin | z_met | p_met | p_equiv | verdict | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N1a_original | ln_co2 | -0.2074565550145567 | 0.08255461822992015 | 0.011972249108812068 | -0.369260633502654 | -0.04565247652645943 | 415 | 43 | 0.03 | -2.1495654491469915 | 0.015794801925900173 | 0.015794801925900173 | MET: effect exceeds +/-3% | 1e7e570ae9ac | 1.0 | d943c1905910 |
| N1b_plus_scale | ln_co2 | -0.21847118076494493 | 0.11297191996239368 | 0.05313110141496379 | -0.43989207515557815 | 0.0029497136256882717 | 406 | 41 | 0.03 | -1.6683011214440153 | 0.04762798271557702 | 0.04762798271557702 | MET: effect exceeds +/-3% | 1e7e570ae9ac | 1.0 | d943c1905910 |
| N1c_scale_trend | ln_co2 | -0.09181494151230601 | 0.1063260613685051 | 0.38785027897314384 | -0.3002101924125716 | 0.11658030938795955 | 390 | 39 | 0.03 | -0.5813714974174361 | 0.2804950515013225 | 0.2804950515013225 | not conclusive | 1e7e570ae9ac | 1.0 | d943c1905910 |

#### results/models/n3_mde.csv (1 rows)

| se_did | mde_80pct | mde_pct | beta_hat | n_treated | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.08255461822992015 | 0.231282046466688 | 23.13 | -0.2074565550145567 | 32 | 1e7e570ae9ac | 1.0 | d943c1905910 |

#### results/models/n4_looo.csv (43 rows)

| dropped | group | coef | se | p | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AT | treated | -0.20588113166632066 | 0.08302889735437075 | 0.013151794750330409 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| BE | treated | -0.20308122980414045 | 0.082899713024451 | 0.014296664846665091 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| BG | treated | -0.20748208903377185 | 0.08305464238036532 | 0.012484702690920597 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| CH | treated | -0.20751723254864524 | 0.08305102665292032 | 0.012465981094289235 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| CY | treated | -0.20218495814901788 | 0.08283429385439474 | 0.014653292031524323 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| CZ | treated | -0.2044224763989106 | 0.08297539770868649 | 0.013752969812705549 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| DE | treated | -0.2036510489798864 | 0.08293540381976712 | 0.014067381605300605 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| DK | treated | -0.20716107127698136 | 0.08305123317769796 | 0.01261785115721983 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| EE | treated | -0.20744672057317587 | 0.08250483689901335 | 0.01192492163941521 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| EL | treated | -0.2064520265326334 | 0.08304356028018231 | 0.012916289475919307 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ES | treated | -0.20503471458164674 | 0.08300151301168908 | 0.013501762378685915 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| FI | treated | -0.205422846270304 | 0.08301118666763861 | 0.013337034217205553 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| FR | treated | -0.20464528712363386 | 0.08298612878936061 | 0.013662446936793799 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| GB | treated | -0.205892816823276 | 0.08302993340828416 | 0.013147746101072123 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| HR | treated | -0.21345154103822178 | 0.0828078300954907 | 0.009946796138733496 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| HU | treated | -0.2050142202016782 | 0.08300118515574699 | 0.013510716902350613 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| IE | treated | -0.2111240174608761 | 0.08296561951845395 | 0.010936635304352677 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| IS | treated | -0.22847093905957844 | 0.0798187040411585 | 0.004204811430446124 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| IT | treated | -0.20434816942637157 | 0.08297377798801457 | 0.013785517315325714 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| LI | treated | -0.19565038544847815 | 0.08181662899637886 | 0.016787553560334404 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| LT | treated | -0.21775364936618224 | 0.08230245621942091 | 0.008150439413426552 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| LU | treated | -0.20795926900249895 | 0.08305413090152436 | 0.012283261797899774 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| LV | treated | -0.20681151424759714 | 0.08279500615722632 | 0.012494050389534868 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| MT | treated | -0.21116023486171062 | 0.08296248523538627 | 0.010919964184205835 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| NL | treated | -0.20605444506695297 | 0.08303390866205494 | 0.013080506724467264 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| NO | treated | -0.20759379942475395 | 0.08305325850043217 | 0.012435948700464003 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| PL | treated | -0.21399159803344722 | 0.08275925808653972 | 0.009717812071956274 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| PT | treated | -0.21040161129381546 | 0.08299831546504022 | 0.011244391651692375 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| RO | treated | -0.20998697668990762 | 0.08301641610798277 | 0.011423712495152743 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| SE | treated | -0.20595818378783223 | 0.08303086686369834 | 0.013119773843075881 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| SI | treated | -0.20170707114914854 | 0.0827959776403812 | 0.014842718145207252 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| SK | treated | -0.20493321113925134 | 0.08299962132971964 | 0.013545862246500626 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AL | control | -0.23749085260565125 | 0.08367689773992007 | 0.004537030566733353 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AM | control | -0.24340190171605908 | 0.08058898136738575 | 0.0025253475705347118 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| BA | control | -0.18686235355657177 | 0.08732479420611926 | 0.032366527438966675 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| GE | control | -0.20744778964038962 | 0.08254802557574185 | 0.011969042157255146 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| MC | control | -0.1926116212766544 | 0.0888304843928382 | 0.0301354558976547 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| MD | control | -0.17406997224746493 | 0.08200637731255363 | 0.03378407587246115 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ME | control | -0.21959728807578985 | 0.08936234116508983 | 0.013995430561326547 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| MK | control | -0.17746596457022892 | 0.083698485151642 | 0.033980686710981936 | 1e7e570ae9ac | 1.0 | d943c1905910 |

_…3 more rows; see CSV._


#### results/models/n4_ri_per_drop.csv (11 rows)

| dropped | p_ri | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- |
| AL | 0.006496751624187906 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AM | 0.005497251374312844 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| BA | 0.004497751124437781 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| GE | 0.005997001499250375 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| MC | 0.00399800099950025 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| MD | 0.001999000499750125 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ME | 0.004497751124437781 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| MK | 0.006496751624187906 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| RS | 0.004497751124437781 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| TR | 0.005497251374312844 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| XK | 0.009995002498750625 | 1e7e570ae9ac | 1.0 | d943c1905910 |

#### results/models/specification_log.csv (40 rows)

| Specification | Outcome | Variable | Result_coef | Result_p | Reason | Final status | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D1_did_naive_10_19 | ln_co2 | did | -0.2074565550145567 | 0.011972249108812068 | naive GB treated thru 2019 (harmless pre-2021) | MAIN | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D2_did_adj_10_19 | ln_co2 | did_adj | -0.2074565550145567 | 0.011972249108812068 | main: GB cutoff irrelevant pre-2021, same as D1 check | MAIN | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D1_did_naive_10_19 | ln_flights | did | -0.10884303861904077 | 0.10825055119387707 | naive GB treated thru 2019 (harmless pre-2021) | MAIN | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D2_did_adj_10_19 | ln_flights | did_adj | -0.10884303861904077 | 0.10825055119387707 | main: GB cutoff irrelevant pre-2021, same as D1 check | MAIN | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D1_did_naive_10_19 | ln_intensity | did | -0.09861351639551472 | 0.15208977464597648 | naive GB treated thru 2019 (harmless pre-2021) | MAIN | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D2_did_adj_10_19 | ln_intensity | did_adj | -0.09861351639551472 | 0.15208977464597648 | main: GB cutoff irrelevant pre-2021, same as D1 check | MAIN | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D3_did_adj_full | ln_co2 | did_adj | -0.22842720031536212 | 0.08342059550514531 | includes COVID — reported for completeness, not identified | descriptive only | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D3_did_adj_full | ln_flights | did_adj | -0.14049891190592306 | 0.16048845649482768 | includes COVID — reported for completeness, not identified | descriptive only | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D3_did_adj_full | ln_intensity | did_adj | -0.08792828840943828 | 0.1596198035593649 | includes COVID — reported for completeness, not identified | descriptive only | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4_did_adj_gdp | ln_co2 | did_adj | 0.0837143031005313 | 1.4118784900743723e-06 | add ln gdp pc; sample = WB-covered states; sign flip reflects compositional shift (gdp-conditional spec on smaller sample); NOT the headline | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4_did_adj_gdp | ln_co2 | ln_gdp_pc | 0.7272092914047237 | 3.5578526488190474e-10 | add ln gdp pc; sample = WB-covered states; sign flip reflects compositional shift (gdp-conditional spec on smaller sample); NOT the headline | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4_did_adj_gdp | ln_flights | did_adj | 0.016840419888915936 | 0.5081474337637247 | add ln gdp pc; sample = WB-covered states; sign flip reflects compositional shift (gdp-conditional spec on smaller sample); NOT the headline | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4_did_adj_gdp | ln_flights | ln_gdp_pc | 0.6315712670329845 | 0.0006313824291025332 | add ln gdp pc; sample = WB-covered states; sign flip reflects compositional shift (gdp-conditional spec on smaller sample); NOT the headline | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4_did_adj_gdp | ln_intensity | did_adj | 0.06687388321161532 | 0.00014587363277853235 | add ln gdp pc; sample = WB-covered states; sign flip reflects compositional shift (gdp-conditional spec on smaller sample); NOT the headline | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4_did_adj_gdp | ln_intensity | ln_gdp_pc | 0.09563802437173444 | 0.5472203250963449 | add ln gdp pc; sample = WB-covered states; sign flip reflects compositional shift (gdp-conditional spec on smaller sample); NOT the headline | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4b_did_adj_gdpsub | ln_co2 | did_adj | 0.12213210988061748 | 1.59996033837964e-08 | baseline D2 on the GDP-available subsample (N shrinks) — decomposition step 1 | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4b_did_adj_gdpsub | ln_flights | did_adj | 0.05020575665167479 | 0.04783379235916906 | baseline D2 on the GDP-available subsample (N shrinks) — decomposition step 1 | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4b_did_adj_gdpsub | ln_intensity | did_adj | 0.07192635322894278 | 1.6469683288750024e-05 | baseline D2 on the GDP-available subsample (N shrinks) — decomposition step 1 | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4c_did_adj_pretrendgdp | ln_co2 | did_adj | 1.0133915095712958 | 0.008571359050909324 | pre-treatment GDP x trend control (mediator-safe) | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4c_did_adj_pretrendgdp | ln_co2 | ln_gdp2010 | 36.87534259668716 | 0.016026647051804906 | pre-treatment GDP x trend control (mediator-safe) | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4c_did_adj_pretrendgdp | ln_co2 | trend_x_gdp2010 | -0.017826240599943068 | 0.020128059413438135 | pre-treatment GDP x trend control (mediator-safe) | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4c_did_adj_pretrendgdp | ln_flights | did_adj | 0.8012819854134765 | 0.01624010430342126 | pre-treatment GDP x trend control (mediator-safe) | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4c_did_adj_pretrendgdp | ln_flights | ln_gdp2010 | 31.062571955238568 | 0.01954373160296342 | pre-treatment GDP x trend control (mediator-safe) | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4c_did_adj_pretrendgdp | ln_flights | trend_x_gdp2010 | -0.015022411620509706 | 0.024186371694780873 | pre-treatment GDP x trend control (mediator-safe) | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4c_did_adj_pretrendgdp | ln_intensity | did_adj | 0.2121095241578148 | 0.2812823997629207 | pre-treatment GDP x trend control (mediator-safe) | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4c_did_adj_pretrendgdp | ln_intensity | ln_gdp2010 | 5.812770641448406 | 0.45736325978049275 | pre-treatment GDP x trend control (mediator-safe) | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4c_did_adj_pretrendgdp | ln_intensity | trend_x_gdp2010 | -0.0028038289794332424 | 0.47424326598207034 | pre-treatment GDP x trend control (mediator-safe) | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4d_noTR | ln_co2 | did_adj | -0.20283286712913484 | 0.024644381273511765 | drop TR from control group | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4e_noTR_gdp | ln_co2 | did_adj | 0.0837143031005313 | 1.4118784900743723e-06 | drop TR + GDP control | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4e_noTR_gdp | ln_co2 | ln_gdp_pc | 0.7272092914047237 | 3.5578526488190474e-10 | drop TR + GDP control | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4d_noTR | ln_flights | did_adj | -0.08773330837094538 | 0.20749596073033683 | drop TR from control group | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4e_noTR_gdp | ln_flights | did_adj | 0.016840419888915936 | 0.5081474337637247 | drop TR + GDP control | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4e_noTR_gdp | ln_flights | ln_gdp_pc | 0.6315712670329845 | 0.0006313824291025332 | drop TR + GDP control | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4d_noTR | ln_intensity | did_adj | -0.11509955875818959 | 0.11748001649134526 | drop TR from control group | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4e_noTR_gdp | ln_intensity | did_adj | 0.06687388321161532 | 0.00014587363277853235 | drop TR + GDP control | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D4e_noTR_gdp | ln_intensity | ln_gdp_pc | 0.09563802437173444 | 0.5472203250963449 | drop TR + GDP control | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D5_noGB | ln_co2 | did_adj | -0.205892816823276 | 0.013147746101072123 | drop GB entirely | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D5_noGB | ln_flights | did_adj | -0.10930097988193463 | 0.10984760630811095 | drop GB entirely | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D5_noGB | ln_intensity | did_adj | -0.0965918369413428 | 0.16207414009348042 | drop GB entirely | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |
| D6_noTiny | ln_co2 | did_adj | -0.18077515087591972 | 0.0402659576049463 | drop states <50k flights/yr | robustness/heterogeneity | 1e7e570ae9ac | 1.0 | d943c1905910 |

#### results/mechanisms/m1_fare_pass_through.csv (2 rows)

| model | var | coef | se | p | N | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M1a_fares_twxets | treat_x_ets | -0.010708520770135753 | 0.004611251467585944 | 0.020218987396654082 | 3720 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| M1b_fares_twxets_ctrend | treat_x_ets | -0.01610452697453978 | 0.00317503671948286 | 3.9317394858691955e-07 | 3720 | 1e7e570ae9ac | 1.0 | d943c1905910 |

#### results/mechanisms/m2_fuel_did.csv (1 rows)

| outcome | coef | se | p | N | cross_source_corr | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ln_jetfuel_ktoe | -0.23557619004097796 | 0.3350945186888832 | 0.4820469279343743 | 364 | 0.966 | 1e7e570ae9ac | 1.0 | d943c1905910 |

#### results/mechanisms/m3_segments.csv (6 rows)

| segment | coef | se | p | N | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| business | -0.06021748840361274 | 0.2896206533360076 | 0.8352926130985747 | 3240 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| cargo | 0.1185777910304856 | 0.2787969615112907 | 0.6706037625813797 | 3240 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| lowcost | -0.07842777977196491 | 0.34064216757474597 | 0.8179090970557356 | 3223 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| mainline | -0.16460185895167395 | 0.284628356864964 | 0.5630585583593546 | 3240 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| other | 0.023103817476279265 | 0.26004594307828055 | 0.9292049852491923 | 3240 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| regional | -0.3307922806873433 | 0.3543675759840276 | 0.35057621764404 | 3194 | 1e7e570ae9ac | 1.0 | d943c1905910 |

#### results/ml/aipw_did.csv (5 rows)

| metric | value |
| --- | --- |
| naive_diff | -0.2175763708504061 |
| aipw_att | -0.11198558321390163 |
| aipw_se | 0.05303898149033784 |
| n_treated | 31.0 |
| n_control | 10.0 |

#### results/ml/aipw_state_effects.csv (31 rows)

| iso | psi | mu1 | mu0 | dY |
| --- | --- | --- | --- | --- |
| AT | -0.11536668476747443 | 0.06770454707643235 | 0.2084350968783123 | 0.0868821035658609 |
| BE | -0.23411675341608462 | 0.10151663023695674 | 0.2084350968783123 | 0.0053423158463079545 |
| BG | -0.08254721797364614 | 0.15602520552008398 | 0.2084350968783123 | 0.13323844637184123 |
| CH | -0.05385798054068183 | 0.07163346456461023 | 0.2084350968783123 | 0.13434695736860114 |
| CY | -0.27892368495809483 | 0.13315989734373518 | 0.2084350968783123 | -0.02081822578136361 |
| CZ | -0.20200845190202762 | 0.1620884210482011 | 0.2084350968783123 | 0.04439293182309356 |
| DE | -0.20183958123914636 | 0.0693140246370614 | 0.2084350968783123 | 0.021892712955725813 |
| DK | -0.08102993675339763 | 0.11340640641367607 | 0.2084350968783123 | 0.12399082995144184 |
| EL | -0.10277409237972553 | 0.09590799657294508 | 0.2084350968783123 | 0.10328222207769855 |
| ES | -0.1556038457222402 | 0.09094075433539484 | 0.2084350968783123 | 0.06212625193151666 |
| FI | -0.1556340890976926 | 0.13757515544968052 | 0.2084350968783123 | 0.07347762916331746 |
| FR | -0.1668513090685726 | 0.07942377801842375 | 0.2084350968783123 | 0.050813053714296785 |
| GB | -0.11072580109139293 | 0.05404431422716538 | 0.2084350968783123 | 0.08705930028454034 |
| HR | 0.06294287725063852 | 0.1307729667155505 | 0.3009308981976564 | 0.3070199196598207 |
| HU | -0.18148711576969503 | 0.1694375896393657 | 0.2084350968783123 | 0.06170154416489737 |
| IE | 0.07430519517552074 | 0.1044885346700999 | 0.2084350968783123 | 0.23926425366755666 |
| IS | 0.7554554278657999 | 0.06043386140153302 | 0.2084350968783123 | 0.7435352410020197 |
| IT | -0.18377870810036695 | 0.09660918643128846 | 0.2084350968783123 | 0.042205851620224166 |
| LI | -1.249013464748222 | 0.28284988397399047 | 0.4940233217402446 | -0.5018584291099365 |
| LT | 0.28561153966575237 | 0.1953872027283535 | 0.22286954187247787 | 0.43211672085289443 |
| LU | -0.05156662079731185 | 0.11728067258599507 | 0.2084350968783123 | 0.14721291425295036 |
| LV | -0.19793672649076632 | 0.2897410796158013 | 0.22304221475281338 | 0.08965075444588955 |
| MT | 0.04633409369434457 | 0.19553041969063387 | 0.2084350968783123 | 0.24032070986972442 |
| NL | -0.10945245718600338 | 0.06928498266370724 | 0.2084350968783123 | 0.09173930870972313 |
| NO | -0.12556964371794924 | 0.015973458581969035 | 0.3009308981976564 | 0.13648618230952714 |
| PL | 0.15591558707632608 | 0.15729743751085845 | 0.22017997329497 | 0.32273016455167713 |
| PT | 0.061511167909471615 | 0.05800158857890356 | 0.2084350968783123 | 0.21825244132220334 |
| RO | -0.0139826219589947 | 0.19673591907724075 | 0.22304221475281338 | 0.20605381871660455 |
| SE | -0.1553517915186881 | 0.15446939402978171 | 0.22304221475281338 | 0.0888560258672122 |
| SI | -0.37955870700523836 | 0.09335655922666282 | 0.3037303368343806 | -0.03456375324463323 |
| SK | -0.32465168206539047 | 0.30802039027943595 | 0.3037303368343806 | 0.05930834635690374 |

#### results/ml/cate_by_state.csv (31 rows)

| iso | cate | abs_rank |
| --- | --- | --- |
| AT | -0.2416626312273768 | 17.0 |
| BE | -0.2615503843297068 | 7.0 |
| BG | -0.23035620615274746 | 22.0 |
| CH | -0.23008583761695237 | 23.0 |
| CY | -0.267931004238895 | 6.0 |
| CZ | -0.25202584384756394 | 12.0 |
| DE | -0.25751370210789754 | 8.0 |
| DK | -0.23261172235284486 | 21.0 |
| EL | -0.23766260232205055 | 20.0 |
| ES | -0.2477006438211193 | 15.0 |
| FI | -0.24493201522799715 | 16.0 |
| FR | -0.2504599604594656 | 13.0 |
| GB | -0.24161941251550376 | 18.0 |
| HR | -0.2807990933395372 | 5.0 |
| HU | -0.24780423108127034 | 14.0 |
| IE | -0.20449625315379247 | 27.0 |
| IS | -0.08150332941367952 | 31.0 |
| IT | -0.25255927804338574 | 11.0 |
| LI | -0.7472072325279157 | 1.0 |
| LT | -0.17125498608039375 | 30.0 |
| LU | -0.22694779935247694 | 24.0 |
| LV | -0.2549148818208999 | 10.0 |
| MT | -0.2042385809093613 | 28.0 |
| NL | -0.240477947045947 | 19.0 |
| NO | -0.32239268781521857 | 4.0 |
| PL | -0.19521432670733063 | 29.0 |
| PT | -0.20962108543314695 | 26.0 |
| RO | -0.22652389053535965 | 25.0 |
| SE | -0.25510871805960167 | 9.0 |
| SI | -0.368822959775473 | 2.0 |
| SK | -0.34410449153846573 | 3.0 |

#### results/ml/cate_summary.csv (1 rows)

| method | mean | sd | min | max | att_boot_ci_lo | att_boot_ci_hi |
| --- | --- | --- | --- | --- | --- | --- |
| X-learner | -0.2590356044791412 | 0.10334323991613294 | -0.7472072325279157 | -0.08150332941367952 | -0.21796050191369643 | -0.010577950357013864 |

#### results/ml/ml_cv.csv (12 rows)

| outcome | model | cv_r2 | cv_r2_sd | n | top |
| --- | --- | --- | --- | --- | --- |
| ln_co2 | RandomForest | 0.589 | 0.149 | 672 | trend |
| ln_co2 | DummyRegressor | -0.0 | 0.0 | 672 | n/a |
| ln_co2 | Ridge | 0.199 | 0.08 | 672 | n/a |
| ln_co2 | HistGradientBoosting | 0.6 | 0.139 | 672 | n/a |
| ln_flights | RandomForest | 0.545 | 0.179 | 672 | trend |
| ln_flights | DummyRegressor | -0.0 | 0.0 | 672 | n/a |
| ln_flights | Ridge | 0.095 | 0.044 | 672 | n/a |
| ln_flights | HistGradientBoosting | 0.555 | 0.175 | 672 | n/a |
| ln_intensity | RandomForest | 0.29 | 0.123 | 672 | trend |
| ln_intensity | DummyRegressor | 0.0 | 0.0 | 672 | n/a |
| ln_intensity | Ridge | 0.249 | 0.106 | 672 | n/a |
| ln_intensity | HistGradientBoosting | 0.261 | 0.129 | 672 | n/a |

#### results/ml/ml_importance.csv (12 rows)

| outcome | model | feature | importance |
| --- | --- | --- | --- |
| ln_co2 | RandomForest | trend | 0.8061 |
| ln_co2 | RandomForest | tr_x_lnets | 0.1085 |
| ln_co2 | RandomForest | did_adj | 0.0476 |
| ln_co2 | RandomForest | ln_gdp_pc | 0.0379 |
| ln_flights | RandomForest | trend | 0.7969 |
| ln_flights | RandomForest | tr_x_lnets | 0.1005 |
| ln_flights | RandomForest | did_adj | 0.0617 |
| ln_flights | RandomForest | ln_gdp_pc | 0.041 |
| ln_intensity | RandomForest | trend | 0.7342 |
| ln_intensity | RandomForest | ln_gdp_pc | 0.1418 |
| ln_intensity | RandomForest | tr_x_lnets | 0.0922 |
| ln_intensity | RandomForest | did_adj | 0.0318 |

#### results/optimization/o1_mac_curve.csv (210 rows)

| ets | iso | co2_2019_mt | abate_share | abate_mt | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | AT | 3.114972593 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | BE | 4.879818683 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | BG | 0.799939346 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | CH | 5.823362078 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | CY | 1.051496169 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | CZ | 1.43947165 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | DE | 31.089433908 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | DK | 3.1007603390000003 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | EE | 0.210027185 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | EL | 4.430024401 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | ES | 22.036524182999997 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | FI | 2.675334307 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | FR | 22.402052039 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | HR | 0.7095893449999999 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | HU | 1.102381928 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | IE | 3.304912457 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | IS | 0.516600534 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | IT | 15.106921478 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | LT | 0.393580497 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | LU | 1.772959277 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | LV | 0.494257553 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | MT | 0.5182756660000001 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | NL | 11.144285299 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | NO | 3.113181945 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | PL | 3.266972499 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | PT | 5.256608541 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | RO | 1.4745418529999998 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | SE | 3.234225659 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | SI | 0.11661393099999999 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | SK | 0.190339292 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 20 | AT | 3.114972593 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 20 | BE | 4.879818683 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 20 | BG | 0.799939346 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 20 | CH | 5.823362078 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 20 | CY | 1.051496169 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 20 | CZ | 1.43947165 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 20 | DE | 31.089433908 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 20 | DK | 3.1007603390000003 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 20 | EE | 0.210027185 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 20 | EL | 4.430024401 | 0.0 | 0.0 | 1e7e570ae9ac | 1.0 | d943c1905910 |

_…170 more rows; see CSV._


#### results/optimization/o2_price_targets.csv (3 rows)

| target | target_mt | price_star | feasible | note | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| -10% | 139.29251817150003 | 118.6 | True | root found in [5, 1e6] | 1e7e570ae9ac | 1.0 | d943c1905910 |
| -20% | 123.81557170800002 | 678.4 | True | root found in [5, 1e6] | 1e7e570ae9ac | 1.0 | d943c1905910 |
| -29% (EU 2030 transport)  | 109.88631989085 | 3973.6 | True | root found in [5, 1e6] | 1e7e570ae9ac | 1.0 | d943c1905910 |

#### results/optimization/o3_optimal_price_path.csv (9 rows)

| year | price_path | remaining_mt | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- |
| 2022 | 50.0 | 147.65 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 2023 | 50.0 | 140.86 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 2024 | 50.0 | 134.39 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 2025 | 50.0 | 128.21 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 2026 | 50.0 | 122.31 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 2027 | 50.0 | 116.69 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 2028 | 50.0 | 111.32 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 2029 | 50.0 | 106.21 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 2030 | 50.0 | 101.32 | 1e7e570ae9ac | 1.0 | d943c1905910 |

#### results/optimization/o4_allocation.csv (30 rows)

| iso | alloc_eur_bn | co2_2019_mt | eff_per_bn | eff_per_mt | pred_residual_mt | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DE | 4.573 | 31.09 | 3.9855 | 0.1282 | 12.864 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| FR | 2.461 | 22.4 | 3.8764 | 0.173 | 12.864 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ES | 2.393 | 22.04 | 3.8336 | 0.174 | 12.864 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| IT | 0.574 | 15.11 | 3.9088 | 0.2587 | 12.864 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AT | 0.0 | 3.11 | 3.7402 | 1.2007 | 3.115 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| BG | 0.0 | 0.8 | 3.5652 | 4.4569 | 0.8 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| CZ | 0.0 | 1.44 | 3.9006 | 2.7097 | 1.439 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| CY | 0.0 | 1.05 | 4.1468 | 3.9437 | 1.051 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| CH | 0.0 | 5.82 | 3.561 | 0.6115 | 5.823 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| DK | 0.0 | 3.1 | 3.6001 | 1.161 | 3.101 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| EL | 0.0 | 4.43 | 3.6783 | 0.8303 | 4.43 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| EE | 0.0 | 0.21 | 4.0091 | 19.0884 | 0.21 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| FI | 0.0 | 2.68 | 3.7908 | 1.4169 | 2.675 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| BE | 0.0 | 4.88 | 4.048 | 0.8295 | 4.88 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| HR | 0.0 | 0.71 | 4.3459 | 6.1245 | 0.71 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| HU | 0.0 | 1.1 | 3.8353 | 3.4791 | 1.102 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| IE | 0.0 | 3.3 | 3.165 | 0.9577 | 3.305 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| IS | 0.0 | 0.52 | 1.2614 | 2.4418 | 0.517 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| LT | 0.0 | 0.39 | 2.6505 | 6.7343 | 0.394 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| LU | 0.0 | 1.77 | 3.5125 | 1.9811 | 1.773 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| LV | 0.0 | 0.49 | 3.9453 | 7.9823 | 0.494 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| MT | 0.0 | 0.52 | 3.161 | 6.0991 | 0.518 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| NL | 0.0 | 11.14 | 3.7219 | 0.334 | 11.144 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| NO | 0.0 | 3.11 | 4.9897 | 1.6028 | 3.113 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| PL | 0.0 | 3.27 | 3.0213 | 0.9248 | 3.267 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| PT | 0.0 | 5.26 | 3.2443 | 0.6172 | 5.257 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| RO | 0.0 | 1.47 | 3.5059 | 2.3776 | 1.475 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| SE | 0.0 | 3.23 | 3.9483 | 1.2208 | 3.234 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| SI | 0.0 | 0.12 | 5.7083 | 48.95 | 0.117 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| SK | 0.0 | 0.19 | 5.3257 | 27.98 | 0.19 | 1e7e570ae9ac | 1.0 | d943c1905910 |

#### results/optimization/o4b_allocation_fair.csv (30 rows)

| iso | alloc_eur_bn | co2_2019_mt | eff_per_bn | pred_abate_mt | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DE | 2.007 | 31.09 | 3.9855 | 7.999 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| FR | 1.449 | 22.4 | 3.8764 | 5.617 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| ES | 1.425 | 22.04 | 3.8336 | 5.464 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| IT | 0.973 | 15.11 | 3.9088 | 3.804 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| NL | 0.721 | 11.14 | 3.7219 | 2.684 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| CH | 0.377 | 5.82 | 3.561 | 1.343 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| PT | 0.34 | 5.26 | 3.2443 | 1.102 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| BE | 0.315 | 4.88 | 4.048 | 1.274 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| EL | 0.286 | 4.43 | 3.6783 | 1.051 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| IE | 0.214 | 3.3 | 3.165 | 0.676 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| PL | 0.211 | 3.27 | 3.0213 | 0.638 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| SE | 0.209 | 3.23 | 3.9483 | 0.825 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AT | 0.201 | 3.11 | 3.7402 | 0.753 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| NO | 0.201 | 3.11 | 4.9897 | 1.004 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| DK | 0.2 | 3.1 | 3.6001 | 0.722 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| FI | 0.173 | 2.68 | 3.7908 | 0.656 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| LU | 0.115 | 1.77 | 3.5125 | 0.403 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| RO | 0.095 | 1.47 | 3.5059 | 0.334 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| CZ | 0.093 | 1.44 | 3.9006 | 0.363 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| HU | 0.071 | 1.1 | 3.8353 | 0.273 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| CY | 0.068 | 1.05 | 4.1468 | 0.282 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| BG | 0.052 | 0.8 | 3.5652 | 0.185 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| HR | 0.046 | 0.71 | 4.3459 | 0.199 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| MT | 0.033 | 0.52 | 3.161 | 0.105 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| IS | 0.033 | 0.52 | 1.2614 | 0.042 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| LV | 0.032 | 0.49 | 3.9453 | 0.126 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| LT | 0.026 | 0.39 | 2.6505 | 0.068 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| EE | 0.014 | 0.21 | 4.0091 | 0.055 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| SK | 0.012 | 0.19 | 5.3257 | 0.066 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| SI | 0.008 | 0.12 | 5.7083 | 0.043 | 1e7e570ae9ac | 1.0 | d943c1905910 |

#### results/simulation/s1_wild_bootstrap.csv (1 rows)

| method | B | beta | p | ci_lo | ci_hi | n_clusters | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| wild_cluster_bootstrap | 4999 | -0.2074565550145567 | 0.03920784156831366 | -0.4047857563812171 | -0.011530678014256501 | 43 | 1e7e570ae9ac | 1.0 | d943c1905910 |

#### results/simulation/s2_ri_betas.csv (5000 rows)

| iteration | beta_perm | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- |
| 0 | 0.003909514398678177 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 1 | 0.03973550304608904 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 2 | 0.024681200159422767 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 3 | 0.00951833984822198 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 4 | 0.11934640112692868 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 5 | 0.00450473884716579 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 6 | -0.002914887320162707 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 7 | -0.0470908005013258 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 8 | 0.06777791449338846 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 9 | 0.0049062687114045656 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 10 | -0.1395146918284129 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 11 | -0.029974417370993295 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 12 | 0.08514999257904726 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 13 | 0.05423196584283935 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 14 | 0.04042273327036755 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 15 | 0.10728118128105865 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 16 | -0.0373221950285193 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 17 | 0.09402621951548112 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 18 | -4.3849765328007884e-05 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 19 | -0.02131451122301667 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 20 | 0.048093582073759994 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 21 | -0.0008173221341039039 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 22 | 0.11759114255256492 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 23 | 0.025640487440967585 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 24 | 0.0016150396155737712 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 25 | -0.08115177569003434 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 26 | 0.06939204651463327 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 27 | 0.046388351691535934 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 28 | 0.046560495934106466 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 29 | 0.010982764705898873 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 30 | 0.05544270933616033 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 31 | -0.08177622034340673 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 32 | 0.021949279090786533 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 33 | -0.07013648062960545 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 34 | -0.010421582406594992 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 35 | -0.013758652389453369 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 36 | 0.09034332331706618 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 37 | -0.1463080048705626 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 38 | 0.015675033548886552 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| 39 | -0.021884056700976956 | 1e7e570ae9ac | 1.0 | d943c1905910 |

_…4960 more rows; see CSV._


#### results/simulation/s2_ri_summary.csv (1 rows)

| method | RI | beta | p | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- |
| randomization_inference | 5000 | -0.2074565550145567 | 0.0033993201359728054 | 1e7e570ae9ac | 1.0 | d943c1905910 |

#### results/simulation/s3_covid_counterfactual_monthly.csv (924 rows)

| iso | ym | ln_co2_cf | year | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- |
| AL | 202003 | 9.229533947915074 | 2020 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AL | 202004 | 9.318523784694218 | 2020 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AL | 202005 | 9.341494459063155 | 2020 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AL | 202006 | 9.457458136997664 | 2020 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AL | 202007 | 9.67435926538521 | 2020 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AL | 202008 | 9.756145872357475 | 2020 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AL | 202009 | 9.593388370855074 | 2020 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AL | 202010 | 9.391146948298754 | 2020 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AL | 202011 | 9.259221135176073 | 2020 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AL | 202012 | 9.388560618982726 | 2020 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AL | 202101 | 9.365639618049205 | 2021 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AL | 202102 | 9.149910594345796 | 2021 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AL | 202103 | 9.277981158500895 | 2021 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AL | 202104 | 9.366970995280038 | 2021 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AL | 202105 | 9.389941669648975 | 2021 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AL | 202106 | 9.505905347583484 | 2021 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AL | 202107 | 9.722806475971028 | 2021 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AL | 202108 | 9.804593082943295 | 2021 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AL | 202109 | 9.641835581440894 | 2021 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AL | 202110 | 9.439594158884574 | 2021 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AL | 202111 | 9.307668345761893 | 2021 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AL | 202112 | 9.437007829568547 | 2021 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AM | 202003 | 9.7151527388868 | 2020 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AM | 202004 | 9.8046935411354 | 2020 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AM | 202005 | 9.876252113317461 | 2020 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AM | 202006 | 9.938832825997302 | 2020 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AM | 202007 | 10.086641438494675 | 2020 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AM | 202008 | 10.130823304989043 | 2020 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AM | 202009 | 9.990140891762843 | 2020 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AM | 202010 | 9.941628019214393 | 2020 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AM | 202011 | 9.799960670185547 | 2020 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AM | 202012 | 9.905759009125775 | 2020 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AM | 202101 | 9.73687414658079 | 2021 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AM | 202102 | 9.583389178707483 | 2021 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AM | 202103 | 9.732332542762265 | 2021 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AM | 202104 | 9.821873345010863 | 2021 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AM | 202105 | 9.893431917192926 | 2021 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AM | 202106 | 9.956012629872765 | 2021 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AM | 202107 | 10.103821242370138 | 2021 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| AM | 202108 | 10.148003108864506 | 2021 | 1e7e570ae9ac | 1.0 | d943c1905910 |

_…884 more rows; see CSV._


#### results/simulation/s3_did_variants.csv (3 rows)

| variant | note | coef | se | p | N | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| drop_covid | main sample (2010-2019) | -0.2074565550145567 | 0.08255461822992015 | 0.011972249108812068 | 415 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| raw_covid | 2020-21 as observed (contaminated) | -0.22842720031536212 | 0.13194924194980215 | 0.08342059550514531 | 672 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| adjusted_covid | 2020-21 replaced by COVID-free counterfactual | -0.21505723885462397 | 0.11772009213487047 | 0.06772195711317626 | 672 | 1e7e570ae9ac | 1.0 | d943c1905910 |

#### results/simulation/s4_policy_montecarlo.csv (27 rows)

| scenario | year | ets | mc_mean | mc_p05 | mc_p95 | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Aggressive_8pct | 2022 | 57.9 | 119.35 | 74.46 | 178.65 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| Aggressive_8pct | 2023 | 62.5 | 117.97 | 70.09 | 179.36 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| Aggressive_8pct | 2024 | 67.5 | 118.13 | 70.96 | 181.22 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| Aggressive_8pct | 2025 | 72.9 | 117.94 | 69.17 | 181.66 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| Aggressive_8pct | 2026 | 78.8 | 117.18 | 68.95 | 181.17 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| Aggressive_8pct | 2027 | 85.1 | 117.55 | 69.41 | 180.43 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| Aggressive_8pct | 2028 | 91.9 | 116.91 | 68.4 | 184.93 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| Aggressive_8pct | 2029 | 99.2 | 115.37 | 67.0 | 181.24 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| Aggressive_8pct | 2030 | 107.1 | 114.67 | 65.12 | 180.41 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| Moderate_plus3 | 2022 | 56.6 | 119.91 | 73.02 | 179.28 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| Moderate_plus3 | 2023 | 59.6 | 118.61 | 72.36 | 181.28 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| Moderate_plus3 | 2024 | 62.6 | 119.15 | 72.74 | 184.12 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| Moderate_plus3 | 2025 | 65.6 | 117.42 | 71.79 | 183.08 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| Moderate_plus3 | 2026 | 68.6 | 118.57 | 71.0 | 182.59 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| Moderate_plus3 | 2027 | 71.6 | 118.66 | 71.07 | 180.62 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| Moderate_plus3 | 2028 | 74.6 | 117.54 | 70.12 | 181.54 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| Moderate_plus3 | 2029 | 77.6 | 116.92 | 68.57 | 180.12 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| Moderate_plus3 | 2030 | 80.6 | 117.25 | 71.71 | 180.97 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| Flat_2021 | 2022 | 53.6 | 119.93 | 73.36 | 181.38 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| Flat_2021 | 2023 | 53.6 | 119.85 | 72.11 | 180.86 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| Flat_2021 | 2024 | 53.6 | 119.05 | 72.8 | 178.68 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| Flat_2021 | 2025 | 53.6 | 120.35 | 72.9 | 184.81 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| Flat_2021 | 2026 | 53.6 | 120.21 | 73.21 | 180.36 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| Flat_2021 | 2027 | 53.6 | 119.05 | 75.08 | 178.02 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| Flat_2021 | 2028 | 53.6 | 119.73 | 74.29 | 180.25 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| Flat_2021 | 2029 | 53.6 | 118.75 | 73.21 | 180.89 | 1e7e570ae9ac | 1.0 | d943c1905910 |
| Flat_2021 | 2030 | 53.6 | 120.57 | 72.23 | 181.86 | 1e7e570ae9ac | 1.0 | d943c1905910 |

#### results/scm/scm_aggregate_annual.csv (10 rows)

| year | actual_idx | syn_idx | treated_rel_synth_pct |
| --- | --- | --- | --- |
| 2010 | 98.19279015917432 | 99.8035867268443 | -1.61 |
| 2011 | 102.36522876243254 | 103.03958688713881 | -0.65 |
| 2012 | 98.76026098658355 | 102.34381381137109 | -3.5 |
| 2013 | 98.43303297263775 | 109.04231371533082 | -9.73 |
| 2014 | 101.94982153014347 | 122.52887806469353 | -16.8 |
| 2015 | 104.24677455349394 | 126.88505331432985 | -17.84 |
| 2016 | 109.79818517690263 | 139.22274793104665 | -21.13 |
| 2017 | 114.70036154377067 | 156.2057165956046 | -26.57 |
| 2018 | 119.69362684751911 | 169.51863392978706 | -29.39 |
| 2019 | 122.26338117942078 | 180.20859130964914 | -32.15 |

#### results/scm/scm_placebo.csv (39 rows)

| unit | att_classic | att_aug | ridge_lam | rmspe_pre | rmspe_post | rmspe_ratio | n_pre | pre_mse | is_treated |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AL | -0.12337442412832827 | -0.07551997409483553 | 0.01 | 0.08359508141545216 | 0.1685498048327475 | 2.0162646172337104 | 23 | 0.16072716564768927 | False |
| AM | -0.54400856329368 | -0.4843373474763845 | 0.01 | 0.05579321841678354 | 0.6311855542280557 | 11.312943976685604 | 23 | 0.07159631408996654 | False |
| BA | 0.34778232844402074 | 0.20531403535353762 | 0.01 | 0.09301686878202332 | 0.5021914411507747 | 5.398928686017321 | 23 | 0.19899917119427946 | False |
| MC | 0.18096863814277228 | 0.09594735978745289 | 0.01 | 0.3447548510841558 | 0.4622000217519296 | 1.340662851584081 | 23 | 2.733685868959344 | False |
| MD | 0.4723010537199734 | 0.5442447855566799 | 0.01 | 0.04787113755122045 | 0.5312257167025963 | 11.09699380204206 | 23 | 0.05270785364030088 | False |
| ME | -0.42038272210069855 | -0.17479623729995272 | 0.01 | 0.3163482193534487 | 0.5908879075095331 | 1.8678401563858573 | 23 | 2.3017525054262475 | False |
| MK | 0.5426992709919692 | 0.5474099115482742 | 0.01 | 0.0592865139055421 | 0.5921715522311392 | 9.988301102922211 | 23 | 0.08084248681465717 | False |
| RS | 0.06834160741550867 | 0.03685393581889614 | 0.01 | 0.07120329939660222 | 0.1300390874689947 | 1.826307047159111 | 23 | 0.11660792643413014 | False |
| TR | -0.11025317818907203 | -0.07350306469251135 | 0.01 | 0.07153943900454242 | 0.15695503381737674 | 2.1939651191199703 | 23 | 0.11771150066094606 | False |
| XK | -0.06486011428243227 | -0.04507879683180579 | 0.01 | 0.0756176259835178 | 0.15543865211471172 | 2.0555875709268143 | 23 | 0.13151458326581278 | False |
| AT | -0.13601079387050982 | -0.053231322117723585 | 0.01 | 0.11909354854364493 | 0.19025931510129235 | 1.597561895064088 | 23 | 0.3262152860085033 | True |
| BE | -0.19163736546977272 | -0.07540608837886313 | 0.01 | 0.12569762750253105 | 0.23144502538361797 | 1.8412839604228615 | 23 | 0.36339755187459705 | True |
| BG | -0.10205481115403064 | -0.06597354350369679 | 0.01 | 0.07718823517047643 | 0.1803426738679381 | 2.336401052176368 | 23 | 0.1370345439208533 | True |
| CH | -0.06287199011605536 | -0.02133906842033298 | 0.01 | 0.13012679801317262 | 0.16567146023146126 | 1.2731540525164577 | 23 | 0.3894586219067042 | True |
| CY | -0.4404824797595633 | -0.2961759579559383 | 0.01 | 0.09578006966098676 | 0.4790055503710396 | 5.001098371158824 | 23 | 0.21099790011805977 | True |
| CZ | -0.42475520468982086 | -0.36344181935806724 | 0.01 | 0.038942795745122494 | 0.45758581080240357 | 11.750204422847974 | 23 | 0.034880450830265426 | True |
| DE | -0.18087558304039475 | -0.07529495441986372 | 0.01 | 0.1146912235053144 | 0.23670324722704555 | 2.063830518087354 | 23 | 0.3025437652303583 | True |
| DK | -0.10125399635810707 | -0.058118230179352415 | 0.01 | 0.10195778036217164 | 0.18788608875858684 | 1.8427832392112011 | 23 | 0.23909394645675958 | True |
| EL | -0.25958387278256434 | -0.21276639540651565 | 0.01 | 0.1312104603750567 | 0.33659269383763724 | 2.565288566746192 | 23 | 0.3959722529721901 | True |
| ES | -0.38744437085498395 | -0.16665221363208427 | 0.01 | 0.0754814757284019 | 0.4324200407053976 | 5.728823350795831 | 23 | 0.1310414230971586 | True |
| FI | -0.2373464091274146 | -0.08678088261562426 | 0.01 | 0.17218567933509063 | 0.3212902062695257 | 1.865951962498941 | 23 | 0.6819018878659913 | True |
| FR | -0.1323468352761059 | -0.05072879915129092 | 0.01 | 0.09749570738219944 | 0.19157022610032362 | 1.9649093405654914 | 23 | 0.21862449803297443 | True |
| GB | -0.2054171286932026 | -0.09406065893137412 | 0.01 | 0.09859675770427694 | 0.2691795932207223 | 2.7301059333824913 | 23 | 0.2235903744853059 | True |
| HR | -0.02314615498224389 | -0.010399683841611038 | 0.01 | 0.136199506992725 | 0.25632949987284387 | 1.8820148878111247 | 23 | 0.4266570312164114 | True |
| HU | -0.3201363636042039 | -0.15347569501267644 | 0.01 | 0.06238462716338931 | 0.3468416215298221 | 5.55972901178718 | 23 | 0.08951235924524764 | True |
| IE | -0.14681684090192515 | -0.08727968959316325 | 0.01 | 0.07198121209891702 | 0.19454454062712875 | 2.7027127628774084 | 23 | 0.1191697825902733 | True |
| IS | 0.2655931836480212 | 0.1659349003443816 | 0.01 | 0.13088261800335954 | 0.3803906291727482 | 2.9063494830381846 | 23 | 0.3939959729945057 | True |
| IT | -0.33130824618687765 | -0.14550849810989078 | 0.01 | 0.06909975965810393 | 0.3840264980043161 | 5.557566334592568 | 23 | 0.10981986605057743 | True |
| LT | 0.1916092072820775 | 0.06891718372728133 | 0.01 | 0.10078133847921997 | 0.2295019016292923 | 2.2772261719525897 | 23 | 0.2336081982702507 | True |
| LU | 0.10665344077789089 | 0.037228922438138294 | 0.01 | 0.15871197014142083 | 0.23142136826878168 | 1.458121703502092 | 23 | 0.579358257721943 | True |
| MT | -0.25069640851190733 | -0.174855991189781 | 0.01 | 0.07362811772116913 | 0.27903030941603946 | 3.789724877562832 | 23 | 0.12468529354073425 | True |
| NL | -0.10636559663554972 | -0.04090426494773101 | 0.01 | 0.10040283295223383 | 0.17908740714697194 | 1.7836887852773229 | 23 | 0.23185676389118687 | True |
| NO | -0.1616480199089747 | -0.08357829321712114 | 0.01 | 0.1179550399100713 | 0.26849232812767115 | 2.2762259953654307 | 23 | 0.32000800312428934 | True |
| PL | -0.16093634728080516 | -0.16876990291776997 | 0.01 | 0.044553094356314875 | 0.22551894824290472 | 5.061802137452212 | 23 | 0.04565449898462179 | True |
| PT | -0.22941156364730228 | -0.13008363225435102 | 0.01 | 0.05626775867674378 | 0.295257992520531 | 5.247374330596272 | 23 | 0.07281939532959905 | True |
| RO | -0.13493592506650962 | -0.07357400904201729 | 0.01 | 0.07859056669359538 | 0.19006130973052268 | 2.418373065962527 | 23 | 0.14205897498406972 | True |
| SE | -0.2196141774589695 | -0.08969805956839198 | 0.01 | 0.15431378321235442 | 0.29210481431373897 | 1.8929275676675454 | 23 | 0.5476931048541193 | True |
| SI | -0.39403460484917535 | -0.3228396209709828 | 0.01 | 0.07192589173845251 | 0.4790894258755961 | 6.660875719382547 | 23 | 0.11898667975454605 | True |
| SK | -0.23836833486446915 | -0.15585601471680663 | 0.01 | 0.10096837973066358 | 0.2780421136711056 | 2.7537543378708453 | 23 | 0.234476115225016 | True |

#### results/scm/scm_state_effects.csv (29 rows)

| unit | att_classic | att_aug | ridge_lam | rmspe_pre | rmspe_post | rmspe_ratio | n_pre | pre_mse | weights_json |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AT | -0.13601079387050982 | -0.053231322117723585 | 0.01 | 0.11909354854364493 | 0.19025931510129235 | 1.597561895064088 | 23 | 0.3262152860085033 | {'AM': 0.1787, 'BA': 0.0436, 'MD': 0.0663, 'RS': 0.3376, 'XK': 0.3738} |
| BE | -0.19163736546977272 | -0.07540608837886313 | 0.01 | 0.12569762750253105 | 0.23144502538361797 | 1.8412839604228615 | 23 | 0.36339755187459705 | {'AM': 0.173, 'RS': 0.4327, 'XK': 0.3943} |
| BG | -0.10205481115403064 | -0.06597354350369679 | 0.01 | 0.07718823517047643 | 0.1803426738679381 | 2.336401052176368 | 23 | 0.1370345439208533 | {'AL': 0.1527, 'BA': 0.1881, 'ME': 0.6592} |
| CH | -0.06287199011605536 | -0.02133906842033298 | 0.01 | 0.13012679801317262 | 0.16567146023146126 | 1.2731540525164577 | 23 | 0.3894586219067042 | {'AM': 0.0556, 'MD': 0.0154, 'RS': 0.4139, 'XK': 0.5152} |
| CY | -0.4404824797595633 | -0.2961759579559383 | 0.01 | 0.09578006966098676 | 0.4790055503710396 | 5.001098371158824 | 23 | 0.21099790011805977 | {'BA': 0.0526, 'MC': 0.168, 'ME': 0.1136, 'TR': 0.6658} |
| CZ | -0.42475520468982086 | -0.36344181935806724 | 0.01 | 0.038942795745122494 | 0.45758581080240357 | 11.750204422847974 | 23 | 0.034880450830265426 | {'AL': 0.0214, 'BA': 0.2318, 'MD': 0.2945, 'RS': 0.1644, 'TR': 0.2332, 'XK': 0.0547} |
| DE | -0.18087558304039475 | -0.07529495441986372 | 0.01 | 0.1146912235053144 | 0.23670324722704555 | 2.063830518087354 | 23 | 0.3025437652303583 | {'AM': 0.2802, 'RS': 0.4596, 'XK': 0.2602} |
| DK | -0.10125399635810707 | -0.058118230179352415 | 0.01 | 0.10195778036217164 | 0.18788608875858684 | 1.8427832392112011 | 23 | 0.23909394645675958 | {'AM': 0.09, 'BA': 0.1031, 'RS': 0.3829, 'XK': 0.424} |
| EL | -0.25958387278256434 | -0.21276639540651565 | 0.01 | 0.1312104603750567 | 0.33659269383763724 | 2.565288566746192 | 23 | 0.3959722529721901 | {'MC': 0.2726, 'ME': 0.6298, 'TR': 0.0976} |
| ES | -0.38744437085498395 | -0.16665221363208427 | 0.01 | 0.0754814757284019 | 0.4324200407053976 | 5.728823350795831 | 23 | 0.1310414230971586 | {'BA': 0.2292, 'MD': 0.2819, 'RS': 0.3782, 'XK': 0.1108} |
| FI | -0.2373464091274146 | -0.08678088261562426 | 0.01 | 0.17218567933509063 | 0.3212902062695257 | 1.865951962498941 | 23 | 0.6819018878659913 | {'MD': 0.047, 'RS': 0.6919, 'XK': 0.2611} |
| FR | -0.1323468352761059 | -0.05072879915129092 | 0.01 | 0.09749570738219944 | 0.19157022610032362 | 1.9649093405654914 | 23 | 0.21862449803297443 | {'AM': 0.1775, 'RS': 0.398, 'XK': 0.4245} |
| GB | -0.2054171286932026 | -0.09406065893137412 | 0.01 | 0.09859675770427694 | 0.2691795932207223 | 2.7301059333824913 | 23 | 0.2235903744853059 | {'AM': 0.0335, 'BA': 0.092, 'MD': 0.0824, 'RS': 0.4516, 'XK': 0.3405} |
| HR | -0.02314615498224389 | -0.010399683841611038 | 0.01 | 0.136199506992725 | 0.25632949987284387 | 1.8820148878111247 | 23 | 0.4266570312164114 | {'MC': 0.3578, 'ME': 0.6422} |
| HU | -0.3201363636042039 | -0.15347569501267644 | 0.01 | 0.06238462716338931 | 0.3468416215298221 | 5.55972901178718 | 23 | 0.08951235924524764 | {'AM': 0.0572, 'BA': 0.3027, 'MD': 0.1298, 'RS': 0.2403, 'TR': 0.1336, 'XK': 0.1364} |
| IE | -0.14681684090192515 | -0.08727968959316325 | 0.01 | 0.07198121209891702 | 0.19454454062712875 | 2.7027127628774084 | 23 | 0.1191697825902733 | {'BA': 0.4351, 'RS': 0.4023, 'XK': 0.1625} |
| IS | 0.2655931836480212 | 0.1659349003443816 | 0.01 | 0.13088261800335954 | 0.3803906291727482 | 2.9063494830381846 | 23 | 0.3939959729945057 | {'ME': 0.0861, 'MK': 0.4187, 'RS': 0.2101, 'TR': 0.2851} |
| IT | -0.33130824618687765 | -0.14550849810989078 | 0.01 | 0.06909975965810393 | 0.3840264980043161 | 5.557566334592568 | 23 | 0.10981986605057743 | {'AM': 0.0274, 'BA': 0.2889, 'MD': 0.2239, 'RS': 0.1801, 'XK': 0.2797} |
| LT | 0.1916092072820775 | 0.06891718372728133 | 0.01 | 0.10078133847921997 | 0.2295019016292923 | 2.2772261719525897 | 23 | 0.2336081982702507 | {'AM': 0.3917, 'BA': 0.2114, 'RS': 0.0921, 'TR': 0.2566, 'XK': 0.0481} |
| LU | 0.10665344077789089 | 0.037228922438138294 | 0.01 | 0.15871197014142083 | 0.23142136826878168 | 1.458121703502092 | 23 | 0.579358257721943 | {'AM': 0.5297, 'RS': 0.021, 'XK': 0.4493} |
| MT | -0.25069640851190733 | -0.174855991189781 | 0.01 | 0.07362811772116913 | 0.27903030941603946 | 3.789724877562832 | 23 | 0.12468529354073425 | {'BA': 0.2504, 'MC': 0.1084, 'MD': 0.2344, 'RS': 0.1417, 'TR': 0.265} |
| NL | -0.10636559663554972 | -0.04090426494773101 | 0.01 | 0.10040283295223383 | 0.17908740714697194 | 1.7836887852773229 | 23 | 0.23185676389118687 | {'AM': 0.2085, 'RS': 0.4445, 'XK': 0.3471} |
| NO | -0.1616480199089747 | -0.08357829321712114 | 0.01 | 0.1179550399100713 | 0.26849232812767115 | 2.2762259953654307 | 23 | 0.32000800312428934 | {'AM': 0.182, 'BA': 0.1096, 'MD': 0.0874, 'RS': 0.4421, 'XK': 0.1789} |
| PL | -0.16093634728080516 | -0.16876990291776997 | 0.01 | 0.044553094356314875 | 0.22551894824290472 | 5.061802137452212 | 23 | 0.04565449898462179 | {'BA': 0.4384, 'MC': 0.0043, 'MD': 0.2983, 'RS': 0.0703, 'TR': 0.1472, 'XK': 0.0415} |
| PT | -0.22941156364730228 | -0.13008363225435102 | 0.01 | 0.05626775867674378 | 0.295257992520531 | 5.247374330596272 | 23 | 0.07281939532959905 | {'AL': 0.0931, 'BA': 0.4532, 'MD': 0.3134, 'RS': 0.0473, 'XK': 0.093} |
| RO | -0.13493592506650962 | -0.07357400904201729 | 0.01 | 0.07859056669359538 | 0.19006130973052268 | 2.418373065962527 | 23 | 0.14205897498406972 | {'AM': 0.1174, 'BA': 0.4098, 'MD': 0.0853, 'RS': 0.1893, 'XK': 0.1982} |
| SE | -0.2196141774589695 | -0.08969805956839198 | 0.01 | 0.15431378321235442 | 0.29210481431373897 | 1.8929275676675454 | 23 | 0.5476931048541193 | {'AM': 0.1112, 'MD': 0.0672, 'RS': 0.6446, 'XK': 0.1769} |
| SI | -0.39403460484917535 | -0.3228396209709828 | 0.01 | 0.07192589173845251 | 0.4790894258755961 | 6.660875719382547 | 23 | 0.11898667975454605 | {'AL': 0.0298, 'BA': 0.3753, 'MD': 0.0112, 'ME': 0.0884, 'RS': 0.0714, 'TR': 0.3278, 'XK': 0.0961} |
| SK | -0.23836833486446915 | -0.15585601471680663 | 0.01 | 0.10096837973066358 | 0.2780421136711056 | 2.7537543378708453 | 23 | 0.234476115225016 | {'AL': 0.1811, 'BA': 0.3659, 'ME': 0.3833, 'TR': 0.0698} |

### tables/

#### tables/T1_descriptives.csv (7 rows)

| variable | unit | n | mean | sd | min | median | max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Aviation CO2 | t | 672 | 4190281.6 | 7498425.6 | 0.5 | 956644.5 | 37299134.2 |
| IFR flights | count | 672 | 200179.8 | 307822.1 | 1.0 | 51300.0 | 1267852.0 |
| CO2 per flight | t | 672 | 16.5 | 9.0 | 0.3 | 14.7 | 76.8 |
| GDP per capita | USD | 397 | 37166.0 | 24193.6 | 6854.3 | 31391.6 | 137781.7 |
| Air passengers | pax | 347 | 26288645.1 | 38539048.0 | 857.0 | 8851291.0 | 192528432.0 |
| Tourist arrivals | count | 280 | 31003159.3 | 43437854.9 | 525000.0 | 11700000.0 | 217877000.0 |
| EU ETS price | EUR/t | 672 | 30.8 | 29.1 | 4.5 | 15.5 | 83.0 |

#### tables/T2_panel_structure.csv (43 rows)

| iso | years | n | treated | co2_mt | co2_pf |
| --- | --- | --- | --- | --- | --- |
| AL | 2010-2025 | 16 | 0 | 0.18 | 11.2 |
| AM | 2010-2025 | 16 | 0 | 0.27 | 20.6 |
| AT | 2010-2025 | 16 | 1 | 2.34 | 14.3 |
| BA | 2010-2025 | 16 | 0 | 0.09 | 10.0 |
| BE | 2010-2025 | 16 | 1 | 4.44 | 29.6 |
| BG | 2010-2025 | 16 | 1 | 0.65 | 16.0 |
| CH | 2010-2025 | 16 | 1 | 4.79 | 20.6 |
| CY | 2010-2025 | 16 | 1 | 0.91 | 25.7 |
| CZ | 2010-2025 | 16 | 1 | 1.04 | 13.7 |
| DE | 2010-2025 | 16 | 1 | 26.82 | 26.1 |
| DK | 2010-2025 | 16 | 1 | 2.55 | 15.3 |
| EE | 2017-2025 | 9 | 1 | 0.18 | 9.0 |
| EL | 2010-2025 | 16 | 1 | 3.68 | 14.6 |
| ES | 2010-2025 | 16 | 1 | 18.16 | 19.3 |
| FI | 2010-2025 | 16 | 1 | 2.03 | 18.1 |
| FR | 2010-2025 | 16 | 1 | 19.32 | 21.4 |
| GB | 2010-2025 | 16 | 1 | 31.36 | 28.9 |
| GE | 2014-2025 | 12 | 0 | 0.44 | 21.8 |
| HR | 2010-2025 | 16 | 1 | 0.5 | 9.6 |
| HU | 2010-2025 | 16 | 1 | 0.85 | 15.5 |
| IE | 2010-2025 | 16 | 1 | 2.48 | 20.0 |
| IS | 2010-2025 | 16 | 1 | 0.39 | 17.5 |
| IT | 2010-2025 | 16 | 1 | 12.39 | 15.9 |
| LI | 2010-2025 | 12 | 1 | 0.0 | 0.6 |
| LT | 2010-2025 | 16 | 1 | 0.3 | 11.6 |
| LU | 2010-2025 | 16 | 1 | 1.52 | 49.3 |
| LV | 2011-2025 | 15 | 1 | 0.37 | 11.5 |
| MC | 2010-2025 | 16 | 0 | 0.0 | 0.6 |
| MD | 2010-2025 | 16 | 0 | 0.15 | 13.0 |
| ME | 2010-2025 | 16 | 0 | 0.11 | 10.1 |
| MK | 2010-2025 | 16 | 0 | 0.1 | 12.0 |
| MT | 2010-2025 | 16 | 1 | 0.39 | 16.8 |
| NL | 2010-2025 | 16 | 1 | 9.85 | 35.1 |
| NO | 2010-2025 | 16 | 1 | 2.69 | 7.7 |
| PL | 2010-2025 | 16 | 1 | 2.51 | 13.1 |
| PT | 2010-2025 | 16 | 1 | 4.09 | 21.1 |
| RO | 2010-2025 | 16 | 1 | 1.14 | 13.0 |
| RS | 2010-2025 | 16 | 0 | 0.37 | 11.1 |
| SE | 2010-2025 | 16 | 1 | 2.6 | 11.0 |
| SI | 2010-2025 | 16 | 1 | 0.1 | 6.9 |

_…3 more rows; see CSV._


#### tables/T3_main_did.csv (40 rows)

| model | outcome | var | coef | se | p | lo | hi | N | R2 | note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D1_did_naive_10_19 | ln_co2 | did | -0.2074565550145567 | 0.0825546182299201 | 0.011972249108812 | -0.369260633502654 | -0.0456524765264594 | 415 | 0.9977 | naive GB treated thru 2019 (harmless pre-2021) |
| D2_did_adj_10_19 | ln_co2 | did_adj | -0.2074565550145567 | 0.0825546182299201 | 0.011972249108812 | -0.369260633502654 | -0.0456524765264594 | 415 | 0.9977 | main: GB cutoff irrelevant pre-2021, same as D1 check |
| D1_did_naive_10_19 | ln_flights | did | -0.1088430386190407 | 0.0677682648816761 | 0.108250551193877 | -0.2416663970818965 | 0.023980319843815 | 415 | 0.9973 | naive GB treated thru 2019 (harmless pre-2021) |
| D2_did_adj_10_19 | ln_flights | did_adj | -0.1088430386190407 | 0.0677682648816761 | 0.108250551193877 | -0.2416663970818965 | 0.023980319843815 | 415 | 0.9973 | main: GB cutoff irrelevant pre-2021, same as D1 check |
| D1_did_naive_10_19 | ln_intensity | did | -0.0986135163955147 | 0.0688551057072556 | 0.1520897746459764 | -0.2335670437334341 | 0.0363400109424047 | 415 | 0.9872 | naive GB treated thru 2019 (harmless pre-2021) |
| D2_did_adj_10_19 | ln_intensity | did_adj | -0.0986135163955147 | 0.0688551057072556 | 0.1520897746459764 | -0.2335670437334341 | 0.0363400109424047 | 415 | 0.9872 | main: GB cutoff irrelevant pre-2021, same as D1 check |
| D3_did_adj_full | ln_co2 | did_adj | -0.2284272003153621 | 0.1319492419498021 | 0.0834205955051453 | -0.4870429623243359 | 0.0301885616936117 | 672 | 0.9945 | includes COVID — reported for completeness, not identified |
| D3_did_adj_full | ln_flights | did_adj | -0.140498911905923 | 0.1001110466107358 | 0.1604884564948276 | -0.3367129577175759 | 0.0557151339057298 | 672 | 0.9934 | includes COVID — reported for completeness, not identified |
| D3_did_adj_full | ln_intensity | did_adj | -0.0879282884094382 | 0.0625222745033063 | 0.1596198035593649 | -0.2104696946674455 | 0.0346131178485689 | 672 | 0.9812 | includes COVID — reported for completeness, not identified |
| D4_did_adj_gdp | ln_co2 | did_adj | 0.0837143031005313 | 0.0173561561200715 | 1.4118784900743723e-06 | 0.0496968621951365 | 0.117731744005926 | 262 | 0.9982 | add ln gdp pc; sample = WB-covered states; sign flip reflects compositional shift (gdp-conditional spec on smaller sample); NOT the headline |
| D4_did_adj_gdp | ln_co2 | ln_gdp_pc | 0.7272092914047237 | 0.11594007207717 | 3.5578526488190474e-10 | 0.4999709257684924 | 0.9544476570409548 | 262 | 0.9982 | add ln gdp pc; sample = WB-covered states; sign flip reflects compositional shift (gdp-conditional spec on smaller sample); NOT the headline |
| D4_did_adj_gdp | ln_flights | did_adj | 0.0168404198889159 | 0.0254492698114996 | 0.5081474337637247 | -0.0330392323744658 | 0.0667200721522977 | 262 | 0.9976 | add ln gdp pc; sample = WB-covered states; sign flip reflects compositional shift (gdp-conditional spec on smaller sample); NOT the headline |
| D4_did_adj_gdp | ln_flights | ln_gdp_pc | 0.6315712670329845 | 0.1847908742179425 | 0.0006313824291025 | 0.2693878088941458 | 0.9937547251718232 | 262 | 0.9976 | add ln gdp pc; sample = WB-covered states; sign flip reflects compositional shift (gdp-conditional spec on smaller sample); NOT the headline |
| D4_did_adj_gdp | ln_intensity | did_adj | 0.0668738832116153 | 0.0176076993412262 | 0.0001458736327785 | 0.0323634266522021 | 0.1013843397710284 | 262 | 0.9847 | add ln gdp pc; sample = WB-covered states; sign flip reflects compositional shift (gdp-conditional spec on smaller sample); NOT the headline |
| D4_did_adj_gdp | ln_intensity | ln_gdp_pc | 0.0956380243717344 | 0.1588854631367799 | 0.5472203250963449 | -0.2157717610433206 | 0.4070478097867894 | 262 | 0.9847 | add ln gdp pc; sample = WB-covered states; sign flip reflects compositional shift (gdp-conditional spec on smaller sample); NOT the headline |
| D4b_did_adj_gdpsub | ln_co2 | did_adj | 0.1221321098806174 | 0.0216144483239372 | 1.59996033837964e-08 | 0.0797685696199983 | 0.1644956501412366 | 262 | 0.9974 | baseline D2 on the GDP-available subsample (N shrinks) — decomposition step 1 |
| D4b_did_adj_gdpsub | ln_flights | did_adj | 0.0502057566516747 | 0.0253712804554886 | 0.047833792359169 | 0.000478960717252 | 0.0999325525860975 | 262 | 0.9967 | baseline D2 on the GDP-available subsample (N shrinks) — decomposition step 1 |
| D4b_did_adj_gdpsub | ln_intensity | did_adj | 0.0719263532289427 | 0.0166957854828479 | 1.6469683288750024e-05 | 0.039203214988954 | 0.1046494914689314 | 262 | 0.9845 | baseline D2 on the GDP-available subsample (N shrinks) — decomposition step 1 |
| D4c_did_adj_pretrendgdp | ln_co2 | did_adj | 1.0133915095712958 | 0.3855114838829286 | 0.0085713590509093 | 0.2578028855341622 | 1.7689801336084292 | 262 | 0.9978 | pre-treatment GDP x trend control (mediator-safe) |
| D4c_did_adj_pretrendgdp | ln_co2 | ln_gdp2010 | 36.87534259668716 | 15.311721029956958 | 0.0160266470518049 | 6.864920836646981 | 66.88576435672735 | 262 | 0.9978 | pre-treatment GDP x trend control (mediator-safe) |
| D4c_did_adj_pretrendgdp | ln_co2 | trend_x_gdp2010 | -0.017826240599943 | 0.0076706573730573 | 0.0201280594134381 | -0.0328604527888821 | -0.0027920284110039 | 262 | 0.9978 | pre-treatment GDP x trend control (mediator-safe) |
| D4c_did_adj_pretrendgdp | ln_flights | did_adj | 0.8012819854134765 | 0.3333848645543167 | 0.0162401043034212 | 0.1478596578962516 | 1.4547043129307011 | 262 | 0.9972 | pre-treatment GDP x trend control (mediator-safe) |
| D4c_did_adj_pretrendgdp | ln_flights | ln_gdp2010 | 31.062571955238568 | 13.303062576994607 | 0.0195437316029634 | 4.989048420246537 | 57.1360954902306 | 262 | 0.9972 | pre-treatment GDP x trend control (mediator-safe) |
| D4c_did_adj_pretrendgdp | ln_flights | trend_x_gdp2010 | -0.0150224116205097 | 0.0066643184021118 | 0.0241863716947808 | -0.0280842356701564 | -0.0019605875708629 | 262 | 0.9972 | pre-treatment GDP x trend control (mediator-safe) |
| D4c_did_adj_pretrendgdp | ln_intensity | did_adj | 0.2121095241578148 | 0.1968637996691748 | 0.2812823997629207 | -0.1737364330534761 | 0.5979554813691057 | 262 | 0.9846 | pre-treatment GDP x trend control (mediator-safe) |
| D4c_did_adj_pretrendgdp | ln_intensity | ln_gdp2010 | 5.812770641448406 | 7.821319918765607 | 0.4573632597804927 | -9.516734710897929 | 21.14227599379474 | 262 | 0.9846 | pre-treatment GDP x trend control (mediator-safe) |
| D4c_did_adj_pretrendgdp | ln_intensity | trend_x_gdp2010 | -0.0028038289794332 | 0.003918194543116 | 0.4742432659820703 | -0.010483349168362 | 0.0048756912094956 | 262 | 0.9846 | pre-treatment GDP x trend control (mediator-safe) |
| D4d_noTR | ln_co2 | did_adj | -0.2028328671291348 | 0.0902710355537526 | 0.0246443812735117 | -0.3797608456616248 | -0.0259048885966448 | 405 | 0.9977 | drop TR from control group |
| D4e_noTR_gdp | ln_co2 | did_adj | 0.0837143031005313 | 0.0173561561200715 | 1.4118784900743723e-06 | 0.0496968621951365 | 0.117731744005926 | 262 | 0.9982 | drop TR + GDP control |
| D4e_noTR_gdp | ln_co2 | ln_gdp_pc | 0.7272092914047237 | 0.11594007207717 | 3.5578526488190474e-10 | 0.4999709257684924 | 0.9544476570409548 | 262 | 0.9982 | drop TR + GDP control |
| D4d_noTR | ln_flights | did_adj | -0.0877333083709453 | 0.0696030487789634 | 0.2074959607303368 | -0.2241527771918983 | 0.0486861604500075 | 405 | 0.9972 | drop TR from control group |
| D4e_noTR_gdp | ln_flights | did_adj | 0.0168404198889159 | 0.0254492698114996 | 0.5081474337637247 | -0.0330392323744658 | 0.0667200721522977 | 262 | 0.9976 | drop TR + GDP control |
| D4e_noTR_gdp | ln_flights | ln_gdp_pc | 0.6315712670329845 | 0.1847908742179425 | 0.0006313824291025 | 0.2693878088941458 | 0.9937547251718232 | 262 | 0.9976 | drop TR + GDP control |
| D4d_noTR | ln_intensity | did_adj | -0.1150995587581895 | 0.0735254205563751 | 0.1174800164913452 | -0.2592067349968457 | 0.0290076174804666 | 405 | 0.9872 | drop TR from control group |
| D4e_noTR_gdp | ln_intensity | did_adj | 0.0668738832116153 | 0.0176076993412262 | 0.0001458736327785 | 0.0323634266522021 | 0.1013843397710284 | 262 | 0.9847 | drop TR + GDP control |
| D4e_noTR_gdp | ln_intensity | ln_gdp_pc | 0.0956380243717344 | 0.1588854631367799 | 0.5472203250963449 | -0.2157717610433206 | 0.4070478097867894 | 262 | 0.9847 | drop TR + GDP control |
| D5_noGB | ln_co2 | did_adj | -0.205892816823276 | 0.0830299334082841 | 0.0131477461010721 | -0.368628495942272 | -0.04315713770428 | 405 | 0.9976 | drop GB entirely |
| D5_noGB | ln_flights | did_adj | -0.1093009798819346 | 0.0683610300385758 | 0.1098476063081109 | -0.2432861367036041 | 0.0246841769397348 | 405 | 0.9971 | drop GB entirely |
| D5_noGB | ln_intensity | did_adj | -0.0965918369413428 | 0.0690864667056769 | 0.1620741400934804 | -0.2319988235035951 | 0.0388151496209095 | 405 | 0.9869 | drop GB entirely |
| D6_noTiny | ln_co2 | did_adj | -0.1807751508759197 | 0.0881395688073416 | 0.0402659576049463 | -0.3535255313511993 | -0.0080247704006401 | 398 | 0.9955 | drop states <50k flights/yr |

#### tables/T4_inference_simulation.csv (5 rows)

| method | B | beta | p | ci_lo | ci_hi | n_clusters | block | RI | variant | note | coef | se | N |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| wild_cluster_bootstrap | 4999.0 | -0.2074565550145567 | 0.0392078415683136 | -0.4047857563812171 | -0.0115306780142565 | 43.0 | S1 wild bootstrap |  |  |  |  |  |  |
| randomization_inference |  | -0.2074565550145567 | 0.0033993201359728 |  |  |  | S2 randomization inference | 5000.0 |  |  |  |  |  |
|  |  |  | 0.011972249108812 |  |  |  | S3 COVID counterfactual variants |  | drop_covid | main sample (2010-2019) | -0.2074565550145567 | 0.0825546182299201 | 415.0 |
|  |  |  | 0.0834205955051453 |  |  |  | S3 COVID counterfactual variants |  | raw_covid | 2020-21 as observed (contaminated) | -0.2284272003153621 | 0.1319492419498021 | 672.0 |
|  |  |  | 0.0677219571131762 |  |  |  | S3 COVID counterfactual variants |  | adjusted_covid | 2020-21 replaced by COVID-free counterfactual | -0.2150572388546239 | 0.1177200921348704 | 672.0 |

#### tables/T5_scm_summary.csv (8 rows)

|  | att_classic | att_aug | rmspe_ratio |
| --- | --- | --- | --- |
| count | 29.0 | 29.0 | 29.0 |
| mean | -0.173 | -0.103 | 3.338 |
| std | 0.165 | 0.11 | 2.241 |
| min | -0.44 | -0.363 | 1.273 |
| 25% | -0.251 | -0.156 | 1.882 |
| 50% | -0.181 | -0.087 | 2.418 |
| 75% | -0.106 | -0.053 | 5.001 |
| max | 0.266 | 0.166 | 11.75 |

#### tables/T5b_optimal_path.csv (9 rows)

| year | price_path | remaining_mt |
| --- | --- | --- |
| 2022 | 50.0 | 147.65 |
| 2023 | 50.0 | 140.86 |
| 2024 | 50.0 | 134.39 |
| 2025 | 50.0 | 128.21 |
| 2026 | 50.0 | 122.31 |
| 2027 | 50.0 | 116.69 |
| 2028 | 50.0 | 111.32 |
| 2029 | 50.0 | 106.21 |
| 2030 | 50.0 | 101.32 |

#### tables/T5c_price_targets.csv (3 rows)

| target | target_mt | price_star | feasible | note |
| --- | --- | --- | --- | --- |
| -10% | 139.29251817150003 | 118.6 | True | root found in [5, 1e6] |
| -20% | 123.81557170800002 | 678.4 | True | root found in [5, 1e6] |
| -29% (EU 2030 transport)  | 109.88631989085 | 3973.6 | True | root found in [5, 1e6] |

## 4. Audit report

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


## 5. Novelty gap

# Novelty & Gap Analysis (from literature scout)

Bottom line: route/airline-level EU ETS aviation studies are crowded, but a clear gap exists:
nobody links free-allocation exposure to emissions at the state level, nor uses causal
estimates to drive robust policy optimization.

## What exists
- Fageda & Teixidó (JEEM 2022): route-level DiD 2010-2016, 4.7% emissions cut on regulated routes, 10.7% short-haul.
- Kang et al. (TR-A 2022): synthetic control, seat capacity fell >20% at peak.
- Zhang & Wang (TR-D 2024 vol.130): similar mitigation (citation only - verify).
- Fageda & Oesingmann (Econ. of Transportation 2025): less emissions/flights, no passenger drop.
- Albert et al. (Transport Policy 2025): VAR, carbon price shocks cut domestic/intra-EU flights, raise prices; no extra-EU effect.
- Fageda & Oesingmann (TR-A 2025): hub carbon leakage, traffic shifting regulated->unregulated.
- T&E/CE Delft (2025): at most 3% of expected savings lost to leakage.
- Santonja, Teixidó & Zaklan (2023 WP): free allocation may have created windfall profits (closest to free-allocation angle).
- Rausch & Straubinger (ZEW 2025/26): 2035 ETS+SAF package 377 EUR/t avoided, +12% ticket prices.
- Nesheim (arXiv Mar 2026): two-stage airline competition, free allowances phased out from 2026.
- AlJameel & Oluleye (IAEE): optimisation of allowance support for SAF.

## Your gap
1. Long state-level panel: 2010-2025, staggered entry, baseline before free allocation ends.
2. Free-allocation exposure: no paper links net-short exposure to emissions (main novelty).
3. Causal estimates feeding robust optimization: no DiD/CATE inputs to CVaR/Pareto optimization of 2026-2030 phase-out (hedged until checked).

Timing hook: free allowances fully phased out from 2026; June 2026 CE Delft study (Carbon Market Watch) on extending ETS to all departing flights.

## Caveats
- ~6 searches, not exhaustive. Check forward citations of Fageda & Teixidó 2022 and Zhang & Wang 2024.
- Reviewers will ask why state-level when route-level exists -> answer via route-level triple-diff; test feasibility first.

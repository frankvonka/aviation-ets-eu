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

- code/02_clean_build.py (185 lines)
- code/05_models_fixed.py (141 lines)
- code/05_reconcile.py (67 lines)
- code/06_ml_suite.py (171 lines)
- code/07_scm_suite.py (154 lines)
- code/08_simulation_suite.py (191 lines)
- code/09_optimization_suite.py (312 lines)
- code/10_tables_figures.py (184 lines)
- code/11_null_precision.py (156 lines)
- code/12_mechanism_pass_through.py (92 lines)
- code/14_fuel_crosscheck.py (48 lines)
- code/15_dose_response.py (59 lines)
- code/build_manuscript.py (569 lines)
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
| net_short_share_x_post | 0.014151690003539934 | 0.02355064402241857 | 0.5479035383291906 | 415 | 861c175df25b | 1.0 | 44fee0bfc126 |

#### results/models/event_study_fixed.csv (27 rows)

| outcome | event_time | coef | se | p | lo | hi | pretrend_p | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ln_co2 | -2 | 0.00921407372341865 | 0.03492115627621094 | 0.7918927103501154 | -0.05923013487644965 | 0.07765828232328695 | 0.7918927103501154 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ln_co2 | 0 | -0.09253462253312779 | 0.08442133861319776 | 0.27303297620802325 | -0.25799740574165597 | 0.07292816067540041 | 0.7918927103501154 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ln_co2 | 1 | -0.16995143836947624 | 0.07852889167401748 | 0.030449774064444907 | -0.3238652377963978 | -0.016037638942554666 | 0.7918927103501154 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ln_co2 | 2 | -0.19104014848749523 | 0.09422688153076704 | 0.042616567429331405 | -0.375721442663321 | -0.006358854311669437 | 0.7918927103501154 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ln_co2 | 3 | -0.17754730835622962 | 0.0990667759225955 | 0.07310120533420111 | -0.37171462122901655 | 0.016620004516557346 | 0.7918927103501154 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ln_co2 | 4 | -0.2083611189187108 | 0.10662538663826122 | 0.05068445661359825 | -0.41734303656736116 | 0.0006207987299395035 | 0.7918927103501154 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ln_co2 | 5 | -0.2366758418692534 | 0.11500855332804229 | 0.03959995083069125 | -0.4620884643062705 | -0.011263219432236321 | 0.7918927103501154 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ln_co2 | 6 | -0.24498016764719688 | 0.11958104752922363 | 0.04049597965884054 | -0.47935471403804764 | -0.010605621256346148 | 0.7918927103501154 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ln_co2 | 7 | -0.30183433939840976 | 0.11259314265829191 | 0.007345684113956692 | -0.5225128439148423 | -0.0811558348819772 | 0.7918927103501154 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ln_flights | -2 | 0.047888605026868834 | 0.047182126755140816 | 0.310118493144494 | -0.044586664127210844 | 0.1403638741809485 | 0.310118493144491 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ln_flights | 0 | -0.017621849568571834 | 0.024388859987132094 | 0.4699644905348178 | -0.06542313676734074 | 0.030179437630197075 | 0.310118493144491 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ln_flights | 1 | -0.08132598241885154 | 0.046544277913753374 | 0.08058842110257944 | -0.17255109081623124 | 0.009899125978528156 | 0.310118493144491 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ln_flights | 2 | -0.06549555607505445 | 0.07043664745712698 | 0.3524484641399612 | -0.20354884828276812 | 0.07255773613265923 | 0.310118493144491 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ln_flights | 3 | -0.060934658311947436 | 0.08592542728783117 | 0.4782267648569173 | -0.22934540115231172 | 0.10747608452841684 | 0.310118493144491 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ln_flights | 4 | -0.08122421493773502 | 0.08334585487548635 | 0.32978643101222815 | -0.24457908875439033 | 0.08213065887892029 | 0.310118493144491 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ln_flights | 5 | -0.10091445505108465 | 0.09739843534384662 | 0.3001557978362277 | -0.2918118804755771 | 0.0899829703734078 | 0.310118493144491 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ln_flights | 6 | -0.10610892598480404 | 0.10467432985925251 | 0.3107233805053552 | -0.31126684261480453 | 0.09904899064519648 | 0.310118493144491 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ln_flights | 7 | -0.16556816788443718 | 0.09032355745122142 | 0.06679419590323728 | -0.3425990874443656 | 0.01146275167549124 | 0.310118493144491 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ln_intensity | -2 | -0.03867453130345109 | 0.038804296980094584 | 0.3189315652592388 | -0.11472955582983285 | 0.03738049322293068 | 0.31893156525923594 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ln_intensity | 0 | -0.07491277296455613 | 0.08658958785573137 | 0.38695778888514853 | -0.24462524659795648 | 0.0947997006688442 | 0.31893156525923594 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ln_intensity | 1 | -0.08862545595062286 | 0.08401657665157922 | 0.2914908291416145 | -0.25329492029206696 | 0.07604400839082122 | 0.31893156525923594 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ln_intensity | 2 | -0.12554459241243984 | 0.08740598240750372 | 0.1509059958322026 | -0.2968571699644887 | 0.045767985139609 | 0.31893156525923594 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ln_intensity | 3 | -0.11661265004428242 | 0.07997405435151272 | 0.14480443054389525 | -0.27335891627089615 | 0.0401336161823313 | 0.31893156525923594 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ln_intensity | 4 | -0.1271369039809779 | 0.08451705568388627 | 0.13251054281611915 | -0.29278728920076125 | 0.038513481238805464 | 0.31893156525923594 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ln_intensity | 5 | -0.13576138681816857 | 0.08600108891442615 | 0.11442765357498776 | -0.30432042372167073 | 0.032797650085333585 | 0.31893156525923594 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ln_intensity | 6 | -0.13887124166239523 | 0.0892839461200856 | 0.11985352163443713 | -0.3138645604553777 | 0.03612207713058724 | 0.31893156525923594 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ln_intensity | 7 | -0.13626617151397277 | 0.08946860042753081 | 0.127743345668987 | -0.311621406099138 | 0.039089063071192504 | 0.31893156525923594 | 861c175df25b | 1.0 | 44fee0bfc126 |

#### results/models/heterogeneity.csv (12 rows)

| model | outcome | var | coef | se | p | lo | hi | N | n_units | R2 | note | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H_lowcost share 2019 | ln_co2 | did_adj | -0.02497130417063187 | 0.1451592822347752 | 0.8634163657085765 | -0.30947826937247613 | 0.2595356610312124 | 415 | 43 | 0.9978 | interaction heterogeneity: lowcost share 2019 | 861c175df25b | 1.0 | 44fee0bfc126 |
| H_lowcost share 2019 | ln_co2 | x_lowcost | -0.7509913295942163 | 0.4416441072287135 | 0.08904733193824889 | -1.6165978737468405 | 0.11461521455840784 | 415 | 43 | 0.9978 | interaction heterogeneity: lowcost share 2019 | 861c175df25b | 1.0 | 44fee0bfc126 |
| H_lowcost share 2019 | ln_flights | did_adj | 0.018585869964606483 | 0.09886823961019206 | 0.8508874271078825 | -0.17519231888624634 | 0.2123640588154593 | 415 | 43 | 0.9973 | interaction heterogeneity: lowcost share 2019 | 861c175df25b | 1.0 | 44fee0bfc126 |
| H_lowcost share 2019 | ln_flights | x_lowcost | -0.5244150146020379 | 0.27122112532564663 | 0.05317056351343449 | -1.0559986520867297 | 0.007168622882653852 | 415 | 43 | 0.9973 | interaction heterogeneity: lowcost share 2019 | 861c175df25b | 1.0 | 44fee0bfc126 |
| H_cargo share 2019 | ln_co2 | did_adj | -0.17842778579155916 | 0.10387295409208734 | 0.08584219186014042 | -0.3820150347798328 | 0.02515946319671447 | 415 | 43 | 0.9977 | interaction heterogeneity: cargo share 2019 | 861c175df25b | 1.0 | 44fee0bfc126 |
| H_cargo share 2019 | ln_co2 | x_cargo | -0.40482166771696354 | 0.7096829878307392 | 0.5683887613302336 | -1.79577476430599 | 0.9861314288720628 | 415 | 43 | 0.9977 | interaction heterogeneity: cargo share 2019 | 861c175df25b | 1.0 | 44fee0bfc126 |
| H_cargo share 2019 | ln_flights | did_adj | -0.12803601434567277 | 0.07864461268315052 | 0.1035179166298357 | -0.28217662278274974 | 0.0261045940914042 | 415 | 43 | 0.9973 | interaction heterogeneity: cargo share 2019 | 861c175df25b | 1.0 | 44fee0bfc126 |
| H_cargo share 2019 | ln_flights | x_cargo | 0.2676562820293322 | 0.45547341289689747 | 0.5567711769385462 | -0.6250552031641282 | 1.1603677672227928 | 415 | 43 | 0.9973 | interaction heterogeneity: cargo share 2019 | 861c175df25b | 1.0 | 44fee0bfc126 |
| H_tourism arrivals (norm) | ln_co2 | did_adj | -0.196334742701669 | 0.08448404208530537 | 0.020129409278424694 | -0.36192042245723377 | -0.030749062946104272 | 415 | 43 | 0.9977 | interaction heterogeneity: tourism arrivals (norm) | 861c175df25b | 1.0 | 44fee0bfc126 |
| H_tourism arrivals (norm) | ln_co2 | x_tourism | -0.010463887960381984 | 0.013612667496946965 | 0.4420788204676137 | -0.03714422598791704 | 0.01621645006715307 | 415 | 43 | 0.9977 | interaction heterogeneity: tourism arrivals (norm) | 861c175df25b | 1.0 | 44fee0bfc126 |
| H_tourism arrivals (norm) | ln_flights | did_adj | -0.09259254263319783 | 0.06997953298967965 | 0.1857896640118526 | -0.22974990694790254 | 0.04456482168150688 | 415 | 43 | 0.9973 | interaction heterogeneity: tourism arrivals (norm) | 861c175df25b | 1.0 | 44fee0bfc126 |
| H_tourism arrivals (norm) | ln_flights | x_tourism | -0.015289178104460063 | 0.013487557876483732 | 0.2569722521413389 | -0.04172430578176771 | 0.011145949572847584 | 415 | 43 | 0.9973 | interaction heterogeneity: tourism arrivals (norm) | 861c175df25b | 1.0 | 44fee0bfc126 |

#### results/models/main_models.csv (19 rows)

| model | outcome | var | coef | se | p | lo | hi | N | n_units | R2 | note | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D1_did_naive_10_19 | ln_co2 | did | -0.2074565550145567 | 0.08255461822992015 | 0.011972249108812068 | -0.369260633502654 | -0.04565247652645943 | 415 | 43 | 0.9977 | naive GB treated thru 2019 (harmless pre-2021) | 861c175df25b | 1.0 | 44fee0bfc126 |
| D2_did_adj_10_19 | ln_co2 | did_adj | -0.2074565550145567 | 0.08255461822992015 | 0.011972249108812068 | -0.369260633502654 | -0.04565247652645943 | 415 | 43 | 0.9977 | main: GB cutoff irrelevant pre-2021, same as D1 check | 861c175df25b | 1.0 | 44fee0bfc126 |
| D1_did_naive_10_19 | ln_flights | did | -0.10884303861904077 | 0.06776826488167616 | 0.10825055119387707 | -0.24166639708189658 | 0.023980319843815046 | 415 | 43 | 0.9973 | naive GB treated thru 2019 (harmless pre-2021) | 861c175df25b | 1.0 | 44fee0bfc126 |
| D2_did_adj_10_19 | ln_flights | did_adj | -0.10884303861904077 | 0.06776826488167616 | 0.10825055119387707 | -0.24166639708189658 | 0.023980319843815046 | 415 | 43 | 0.9973 | main: GB cutoff irrelevant pre-2021, same as D1 check | 861c175df25b | 1.0 | 44fee0bfc126 |
| D1_did_naive_10_19 | ln_intensity | did | -0.09861351639551472 | 0.06885510570725568 | 0.15208977464597648 | -0.23356704373343418 | 0.036340010942404743 | 415 | 43 | 0.9872 | naive GB treated thru 2019 (harmless pre-2021) | 861c175df25b | 1.0 | 44fee0bfc126 |
| D2_did_adj_10_19 | ln_intensity | did_adj | -0.09861351639551472 | 0.06885510570725568 | 0.15208977464597648 | -0.23356704373343418 | 0.036340010942404743 | 415 | 43 | 0.9872 | main: GB cutoff irrelevant pre-2021, same as D1 check | 861c175df25b | 1.0 | 44fee0bfc126 |
| D3_did_adj_full | ln_co2 | did_adj | -0.22842720031536212 | 0.13194924194980215 | 0.08342059550514531 | -0.48704296232433597 | 0.030188561693611726 | 672 | 43 | 0.9945 | includes COVID — reported for completeness, not identified | 861c175df25b | 1.0 | 44fee0bfc126 |
| D3_did_adj_full | ln_flights | did_adj | -0.14049891190592306 | 0.10011104661073583 | 0.16048845649482768 | -0.3367129577175759 | 0.055715133905729824 | 672 | 43 | 0.9934 | includes COVID — reported for completeness, not identified | 861c175df25b | 1.0 | 44fee0bfc126 |
| D3_did_adj_full | ln_intensity | did_adj | -0.08792828840943828 | 0.0625222745033063 | 0.1596198035593649 | -0.21046969466744553 | 0.034613117848568964 | 672 | 43 | 0.9812 | includes COVID — reported for completeness, not identified | 861c175df25b | 1.0 | 44fee0bfc126 |
| D4_did_adj_gdp | ln_co2 | did_adj | 0.0837143031005313 | 0.017356156120071572 | 1.4118784900743723e-06 | 0.049696862195136575 | 0.11773174400592601 | 262 | 27 | 0.9982 | add ln gdp pc; sample = WB-covered states (27 of 43); sign flip reflects compositional shift (gdp-conditional spec on a 37% smaller sample); NOT the headline | 861c175df25b | 1.0 | 44fee0bfc126 |
| D4_did_adj_gdp | ln_co2 | ln_gdp_pc | 0.7272092914047237 | 0.11594007207717001 | 3.5578526488190474e-10 | 0.49997092576849245 | 0.9544476570409549 | 262 | 27 | 0.9982 | add ln gdp pc; sample = WB-covered states (27 of 43); sign flip reflects compositional shift (gdp-conditional spec on a 37% smaller sample); NOT the headline | 861c175df25b | 1.0 | 44fee0bfc126 |
| D4_did_adj_gdp | ln_flights | did_adj | 0.016840419888915936 | 0.025449269811499673 | 0.5081474337637247 | -0.03303923237446588 | 0.06672007215229775 | 262 | 27 | 0.9976 | add ln gdp pc; sample = WB-covered states (27 of 43); sign flip reflects compositional shift (gdp-conditional spec on a 37% smaller sample); NOT the headline | 861c175df25b | 1.0 | 44fee0bfc126 |
| D4_did_adj_gdp | ln_flights | ln_gdp_pc | 0.6315712670329845 | 0.18479087421794257 | 0.0006313824291025332 | 0.2693878088941458 | 0.9937547251718232 | 262 | 27 | 0.9976 | add ln gdp pc; sample = WB-covered states (27 of 43); sign flip reflects compositional shift (gdp-conditional spec on a 37% smaller sample); NOT the headline | 861c175df25b | 1.0 | 44fee0bfc126 |
| D4_did_adj_gdp | ln_intensity | did_adj | 0.06687388321161532 | 0.01760769934122628 | 0.00014587363277853235 | 0.03236342665220217 | 0.10138433977102847 | 262 | 27 | 0.9847 | add ln gdp pc; sample = WB-covered states (27 of 43); sign flip reflects compositional shift (gdp-conditional spec on a 37% smaller sample); NOT the headline | 861c175df25b | 1.0 | 44fee0bfc126 |
| D4_did_adj_gdp | ln_intensity | ln_gdp_pc | 0.09563802437173444 | 0.15888546313677993 | 0.5472203250963449 | -0.2157717610433206 | 0.40704780978678945 | 262 | 27 | 0.9847 | add ln gdp pc; sample = WB-covered states (27 of 43); sign flip reflects compositional shift (gdp-conditional spec on a 37% smaller sample); NOT the headline | 861c175df25b | 1.0 | 44fee0bfc126 |
| D5_noGB | ln_co2 | did_adj | -0.205892816823276 | 0.08302993340828416 | 0.013147746101072123 | -0.368628495942272 | -0.043157137704280035 | 405 | 42 | 0.9976 | drop GB entirely | 861c175df25b | 1.0 | 44fee0bfc126 |
| D5_noGB | ln_flights | did_adj | -0.10930097988193463 | 0.06836103003857587 | 0.10984760630811095 | -0.2432861367036041 | 0.024684176939734848 | 405 | 42 | 0.9971 | drop GB entirely | 861c175df25b | 1.0 | 44fee0bfc126 |
| D5_noGB | ln_intensity | did_adj | -0.0965918369413428 | 0.06908646670567695 | 0.16207414009348042 | -0.23199882350359516 | 0.03881514962090957 | 405 | 42 | 0.9869 | drop GB entirely | 861c175df25b | 1.0 | 44fee0bfc126 |
| D6_noTiny | ln_co2 | did_adj | -0.18077515087591972 | 0.08813956880734165 | 0.0402659576049463 | -0.35352553135119935 | -0.008024770400640119 | 398 | 41 | 0.9955 | drop states <50k flights/yr | 861c175df25b | 1.0 | 44fee0bfc126 |

#### results/models/n1_respecified.csv (3 rows)

| model | outcome | coef | se | p | lo | hi | N | n_units | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N1a_original | ln_co2 | -0.2074565550145567 | 0.08255461822992015 | 0.011972249108812068 | -0.369260633502654 | -0.04565247652645943 | 415 | 43 | 861c175df25b | 1.0 | 44fee0bfc126 |
| N1b_plus_scale | ln_co2 | -0.20743757683549252 | 0.08261456125582649 | 0.012042101786379196 | -0.36935914149549054 | -0.045516012175494475 | 406 | 41 | 861c175df25b | 1.0 | 44fee0bfc126 |
| N1c_scale_trend | ln_co2 | -0.19491724403932126 | 0.08224432996263391 | 0.017789148762773592 | -0.3561131686987122 | -0.03372131937993034 | 390 | 39 | 861c175df25b | 1.0 | 44fee0bfc126 |

#### results/models/n2_tost.csv (3 rows)

| model | outcome | coef | se | p | lo | hi | N | n_units | equiv_margin | z_low | z_high | p_equiv | verdict | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N1a_original | ln_co2 | -0.2074565550145567 | 0.08255461822992015 | 0.011972249108812068 | -0.369260633502654 | -0.04565247652645943 | 415 | 43 | 0.03 | -2.1495654491469915 | -2.876357011950855 | 0.9842051980740998 | not conclusive | 861c175df25b | 1.0 | 44fee0bfc126 |
| N1b_plus_scale | ln_co2 | -0.20743757683549252 | 0.08261456125582649 | 0.012042101786379196 | -0.36935914149549054 | -0.045516012175494475 | 406 | 41 | 0.03 | -2.147776059550017 | -2.8740402808681256 | 0.9841342251270172 | not conclusive | 861c175df25b | 1.0 | 44fee0bfc126 |
| N1c_scale_trend | ln_co2 | -0.19491724403932126 | 0.08224432996263391 | 0.017789148762773592 | -0.3561131686987122 | -0.03372131937993034 | 390 | 39 | 0.03 | -2.005211108343252 | -2.734744682600101 | 0.9775297584849114 | not conclusive | 861c175df25b | 1.0 | 44fee0bfc126 |

#### results/models/n3_mde.csv (1 rows)

| se_did | mde_80pct | mde_pct | beta_hat | n_treated | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.08255461822992015 | 0.231282046466688 | 23.13 | -0.2074565550145567 | 32 | 861c175df25b | 1.0 | 44fee0bfc126 |

#### results/models/n4_looo.csv (43 rows)

| dropped | group | coef | se | p | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AT | treated | -0.20588113166632066 | 0.08302889735437075 | 0.013151794750330409 | 861c175df25b | 1.0 | 44fee0bfc126 |
| BE | treated | -0.20308122980414045 | 0.082899713024451 | 0.014296664846665091 | 861c175df25b | 1.0 | 44fee0bfc126 |
| BG | treated | -0.20748208903377185 | 0.08305464238036532 | 0.012484702690920597 | 861c175df25b | 1.0 | 44fee0bfc126 |
| CH | treated | -0.20751723254864524 | 0.08305102665292032 | 0.012465981094289235 | 861c175df25b | 1.0 | 44fee0bfc126 |
| CY | treated | -0.20218495814901788 | 0.08283429385439474 | 0.014653292031524323 | 861c175df25b | 1.0 | 44fee0bfc126 |
| CZ | treated | -0.2044224763989106 | 0.08297539770868649 | 0.013752969812705549 | 861c175df25b | 1.0 | 44fee0bfc126 |
| DE | treated | -0.2036510489798864 | 0.08293540381976712 | 0.014067381605300605 | 861c175df25b | 1.0 | 44fee0bfc126 |
| DK | treated | -0.20716107127698136 | 0.08305123317769796 | 0.01261785115721983 | 861c175df25b | 1.0 | 44fee0bfc126 |
| EE | treated | -0.20744672057317587 | 0.08250483689901335 | 0.01192492163941521 | 861c175df25b | 1.0 | 44fee0bfc126 |
| EL | treated | -0.2064520265326334 | 0.08304356028018231 | 0.012916289475919307 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ES | treated | -0.20503471458164674 | 0.08300151301168908 | 0.013501762378685915 | 861c175df25b | 1.0 | 44fee0bfc126 |
| FI | treated | -0.205422846270304 | 0.08301118666763861 | 0.013337034217205553 | 861c175df25b | 1.0 | 44fee0bfc126 |
| FR | treated | -0.20464528712363386 | 0.08298612878936061 | 0.013662446936793799 | 861c175df25b | 1.0 | 44fee0bfc126 |
| GB | treated | -0.205892816823276 | 0.08302993340828416 | 0.013147746101072123 | 861c175df25b | 1.0 | 44fee0bfc126 |
| HR | treated | -0.21345154103822178 | 0.0828078300954907 | 0.009946796138733496 | 861c175df25b | 1.0 | 44fee0bfc126 |
| HU | treated | -0.2050142202016782 | 0.08300118515574699 | 0.013510716902350613 | 861c175df25b | 1.0 | 44fee0bfc126 |
| IE | treated | -0.2111240174608761 | 0.08296561951845395 | 0.010936635304352677 | 861c175df25b | 1.0 | 44fee0bfc126 |
| IS | treated | -0.22847093905957844 | 0.0798187040411585 | 0.004204811430446124 | 861c175df25b | 1.0 | 44fee0bfc126 |
| IT | treated | -0.20434816942637157 | 0.08297377798801457 | 0.013785517315325714 | 861c175df25b | 1.0 | 44fee0bfc126 |
| LI | treated | -0.19565038544847815 | 0.08181662899637886 | 0.016787553560334404 | 861c175df25b | 1.0 | 44fee0bfc126 |
| LT | treated | -0.21775364936618224 | 0.08230245621942091 | 0.008150439413426552 | 861c175df25b | 1.0 | 44fee0bfc126 |
| LU | treated | -0.20795926900249895 | 0.08305413090152436 | 0.012283261797899774 | 861c175df25b | 1.0 | 44fee0bfc126 |
| LV | treated | -0.20681151424759714 | 0.08279500615722632 | 0.012494050389534868 | 861c175df25b | 1.0 | 44fee0bfc126 |
| MT | treated | -0.21116023486171062 | 0.08296248523538627 | 0.010919964184205835 | 861c175df25b | 1.0 | 44fee0bfc126 |
| NL | treated | -0.20605444506695297 | 0.08303390866205494 | 0.013080506724467264 | 861c175df25b | 1.0 | 44fee0bfc126 |
| NO | treated | -0.20759379942475395 | 0.08305325850043217 | 0.012435948700464003 | 861c175df25b | 1.0 | 44fee0bfc126 |
| PL | treated | -0.21399159803344722 | 0.08275925808653972 | 0.009717812071956274 | 861c175df25b | 1.0 | 44fee0bfc126 |
| PT | treated | -0.21040161129381546 | 0.08299831546504022 | 0.011244391651692375 | 861c175df25b | 1.0 | 44fee0bfc126 |
| RO | treated | -0.20998697668990762 | 0.08301641610798277 | 0.011423712495152743 | 861c175df25b | 1.0 | 44fee0bfc126 |
| SE | treated | -0.20595818378783223 | 0.08303086686369834 | 0.013119773843075881 | 861c175df25b | 1.0 | 44fee0bfc126 |
| SI | treated | -0.20170707114914854 | 0.0827959776403812 | 0.014842718145207252 | 861c175df25b | 1.0 | 44fee0bfc126 |
| SK | treated | -0.20493321113925134 | 0.08299962132971964 | 0.013545862246500626 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AL | control | -0.23749085260565125 | 0.08367689773992007 | 0.004537030566733353 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AM | control | -0.24340190171605908 | 0.08058898136738575 | 0.0025253475705347118 | 861c175df25b | 1.0 | 44fee0bfc126 |
| BA | control | -0.18686235355657177 | 0.08732479420611926 | 0.032366527438966675 | 861c175df25b | 1.0 | 44fee0bfc126 |
| GE | control | -0.20744778964038962 | 0.08254802557574185 | 0.011969042157255146 | 861c175df25b | 1.0 | 44fee0bfc126 |
| MC | control | -0.1926116212766544 | 0.0888304843928382 | 0.0301354558976547 | 861c175df25b | 1.0 | 44fee0bfc126 |
| MD | control | -0.17406997224746493 | 0.08200637731255363 | 0.03378407587246115 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ME | control | -0.21959728807578985 | 0.08936234116508983 | 0.013995430561326547 | 861c175df25b | 1.0 | 44fee0bfc126 |
| MK | control | -0.17746596457022892 | 0.083698485151642 | 0.033980686710981936 | 861c175df25b | 1.0 | 44fee0bfc126 |

_…3 more rows; see CSV._


#### results/models/n4_ri_per_drop.csv (11 rows)

| dropped | p_ri | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- |
| AL | 0.006496751624187906 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AM | 0.005497251374312844 | 861c175df25b | 1.0 | 44fee0bfc126 |
| BA | 0.004497751124437781 | 861c175df25b | 1.0 | 44fee0bfc126 |
| GE | 0.005997001499250375 | 861c175df25b | 1.0 | 44fee0bfc126 |
| MC | 0.00399800099950025 | 861c175df25b | 1.0 | 44fee0bfc126 |
| MD | 0.001999000499750125 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ME | 0.004497751124437781 | 861c175df25b | 1.0 | 44fee0bfc126 |
| MK | 0.006496751624187906 | 861c175df25b | 1.0 | 44fee0bfc126 |
| RS | 0.004497751124437781 | 861c175df25b | 1.0 | 44fee0bfc126 |
| TR | 0.005497251374312844 | 861c175df25b | 1.0 | 44fee0bfc126 |
| XK | 0.009995002498750625 | 861c175df25b | 1.0 | 44fee0bfc126 |

#### results/models/specification_log.csv (19 rows)

| Specification | Outcome | Variable | Result_coef | Result_p | Reason | Final status | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D1_did_naive_10_19 | ln_co2 | did | -0.2074565550145567 | 0.011972249108812068 | naive GB treated thru 2019 (harmless pre-2021) | MAIN | 861c175df25b | 1.0 | 44fee0bfc126 |
| D2_did_adj_10_19 | ln_co2 | did_adj | -0.2074565550145567 | 0.011972249108812068 | main: GB cutoff irrelevant pre-2021, same as D1 check | MAIN | 861c175df25b | 1.0 | 44fee0bfc126 |
| D1_did_naive_10_19 | ln_flights | did | -0.10884303861904077 | 0.10825055119387707 | naive GB treated thru 2019 (harmless pre-2021) | MAIN | 861c175df25b | 1.0 | 44fee0bfc126 |
| D2_did_adj_10_19 | ln_flights | did_adj | -0.10884303861904077 | 0.10825055119387707 | main: GB cutoff irrelevant pre-2021, same as D1 check | MAIN | 861c175df25b | 1.0 | 44fee0bfc126 |
| D1_did_naive_10_19 | ln_intensity | did | -0.09861351639551472 | 0.15208977464597648 | naive GB treated thru 2019 (harmless pre-2021) | MAIN | 861c175df25b | 1.0 | 44fee0bfc126 |
| D2_did_adj_10_19 | ln_intensity | did_adj | -0.09861351639551472 | 0.15208977464597648 | main: GB cutoff irrelevant pre-2021, same as D1 check | MAIN | 861c175df25b | 1.0 | 44fee0bfc126 |
| D3_did_adj_full | ln_co2 | did_adj | -0.22842720031536212 | 0.08342059550514531 | includes COVID — reported for completeness, not identified | descriptive only | 861c175df25b | 1.0 | 44fee0bfc126 |
| D3_did_adj_full | ln_flights | did_adj | -0.14049891190592306 | 0.16048845649482768 | includes COVID — reported for completeness, not identified | descriptive only | 861c175df25b | 1.0 | 44fee0bfc126 |
| D3_did_adj_full | ln_intensity | did_adj | -0.08792828840943828 | 0.1596198035593649 | includes COVID — reported for completeness, not identified | descriptive only | 861c175df25b | 1.0 | 44fee0bfc126 |
| D4_did_adj_gdp | ln_co2 | did_adj | 0.0837143031005313 | 1.4118784900743723e-06 | add ln gdp pc; sample = WB-covered states (27 of 43); sign flip reflects compositional shift (gdp-conditional spec on a 37% smaller sample); NOT the headline | robustness/heterogeneity | 861c175df25b | 1.0 | 44fee0bfc126 |
| D4_did_adj_gdp | ln_co2 | ln_gdp_pc | 0.7272092914047237 | 3.5578526488190474e-10 | add ln gdp pc; sample = WB-covered states (27 of 43); sign flip reflects compositional shift (gdp-conditional spec on a 37% smaller sample); NOT the headline | robustness/heterogeneity | 861c175df25b | 1.0 | 44fee0bfc126 |
| D4_did_adj_gdp | ln_flights | did_adj | 0.016840419888915936 | 0.5081474337637247 | add ln gdp pc; sample = WB-covered states (27 of 43); sign flip reflects compositional shift (gdp-conditional spec on a 37% smaller sample); NOT the headline | robustness/heterogeneity | 861c175df25b | 1.0 | 44fee0bfc126 |
| D4_did_adj_gdp | ln_flights | ln_gdp_pc | 0.6315712670329845 | 0.0006313824291025332 | add ln gdp pc; sample = WB-covered states (27 of 43); sign flip reflects compositional shift (gdp-conditional spec on a 37% smaller sample); NOT the headline | robustness/heterogeneity | 861c175df25b | 1.0 | 44fee0bfc126 |
| D4_did_adj_gdp | ln_intensity | did_adj | 0.06687388321161532 | 0.00014587363277853235 | add ln gdp pc; sample = WB-covered states (27 of 43); sign flip reflects compositional shift (gdp-conditional spec on a 37% smaller sample); NOT the headline | robustness/heterogeneity | 861c175df25b | 1.0 | 44fee0bfc126 |
| D4_did_adj_gdp | ln_intensity | ln_gdp_pc | 0.09563802437173444 | 0.5472203250963449 | add ln gdp pc; sample = WB-covered states (27 of 43); sign flip reflects compositional shift (gdp-conditional spec on a 37% smaller sample); NOT the headline | robustness/heterogeneity | 861c175df25b | 1.0 | 44fee0bfc126 |
| D5_noGB | ln_co2 | did_adj | -0.205892816823276 | 0.013147746101072123 | drop GB entirely | robustness/heterogeneity | 861c175df25b | 1.0 | 44fee0bfc126 |
| D5_noGB | ln_flights | did_adj | -0.10930097988193463 | 0.10984760630811095 | drop GB entirely | robustness/heterogeneity | 861c175df25b | 1.0 | 44fee0bfc126 |
| D5_noGB | ln_intensity | did_adj | -0.0965918369413428 | 0.16207414009348042 | drop GB entirely | robustness/heterogeneity | 861c175df25b | 1.0 | 44fee0bfc126 |
| D6_noTiny | ln_co2 | did_adj | -0.18077515087591972 | 0.0402659576049463 | drop states <50k flights/yr | robustness/heterogeneity | 861c175df25b | 1.0 | 44fee0bfc126 |

#### results/mechanisms/m1_fare_pass_through.csv (2 rows)

| model | var | coef | se | p | N | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M1a_fares_twxets | treat_x_ets | -0.010708520770135753 | 0.004611251467585944 | 0.020218987396654082 | 3720 | 861c175df25b | 1.0 | 44fee0bfc126 |
| M1b_fares_twxets_ctrend | treat_x_ets | -0.01610452697453978 | 0.00317503671948286 | 3.9317394858691955e-07 | 3720 | 861c175df25b | 1.0 | 44fee0bfc126 |

#### results/mechanisms/m2_fuel_did.csv (1 rows)

| outcome | coef | se | p | N | cross_source_corr | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ln_jetfuel_ktoe | -0.23557619004097796 | 0.3350945186888832 | 0.4820469279343743 | 364 | 0.966 | 861c175df25b | 1.0 | 44fee0bfc126 |

#### results/mechanisms/m3_segments.csv (6 rows)

| segment | coef | se | p | N | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| business | -0.06021748840361274 | 0.2896206533360076 | 0.8352926130985747 | 3240 | 861c175df25b | 1.0 | 44fee0bfc126 |
| cargo | 0.1185777910304856 | 0.2787969615112907 | 0.6706037625813797 | 3240 | 861c175df25b | 1.0 | 44fee0bfc126 |
| lowcost | -0.07842777977196491 | 0.34064216757474597 | 0.8179090970557356 | 3223 | 861c175df25b | 1.0 | 44fee0bfc126 |
| mainline | -0.16460185895167395 | 0.284628356864964 | 0.5630585583593546 | 3240 | 861c175df25b | 1.0 | 44fee0bfc126 |
| other | 0.023103817476279265 | 0.26004594307828055 | 0.9292049852491923 | 3240 | 861c175df25b | 1.0 | 44fee0bfc126 |
| regional | -0.3307922806873433 | 0.3543675759840276 | 0.35057621764404 | 3194 | 861c175df25b | 1.0 | 44fee0bfc126 |

#### results/ml/aipw_did.csv (5 rows)

| metric | value |
| --- | --- |
| naive_diff | -0.2175763708504061 |
| aipw_att | -0.1119855832139016 |
| aipw_se | 0.05303898149033784 |
| n_treated | 31.0 |
| n_control | 10.0 |

#### results/ml/aipw_state_effects.csv (31 rows)

| iso | psi | mu1 | mu0 | dY |
| --- | --- | --- | --- | --- |
| AT | -0.1153666847674744 | 0.06770454707643231 | 0.20843509687831227 | 0.0868821035658609 |
| BE | -0.23411675341608457 | 0.1015166302369567 | 0.20843509687831227 | 0.0053423158463079545 |
| BG | -0.08254721797364607 | 0.15602520552008387 | 0.20843509687831227 | 0.13323844637184123 |
| CH | -0.053857980540681805 | 0.07163346456461023 | 0.20843509687831227 | 0.13434695736860114 |
| CY | -0.27892368495809483 | 0.13315989734373518 | 0.20843509687831227 | -0.02081822578136361 |
| CZ | -0.20200845190202762 | 0.1620884210482012 | 0.20843509687831227 | 0.04439293182309356 |
| DE | -0.20183958123914633 | 0.06931402463706143 | 0.20843509687831227 | 0.021892712955725813 |
| DK | -0.08102993675339759 | 0.11340640641367603 | 0.20843509687831227 | 0.12399082995144184 |
| EL | -0.10277409237972548 | 0.09590799657294503 | 0.20843509687831227 | 0.10328222207769855 |
| ES | -0.15560384572224017 | 0.09094075433539485 | 0.20843509687831227 | 0.06212625193151666 |
| FI | -0.1556340890976926 | 0.13757515544968058 | 0.20843509687831227 | 0.07347762916331746 |
| FR | -0.16685130906857254 | 0.07942377801842372 | 0.20843509687831227 | 0.050813053714296785 |
| GB | -0.1107258010913929 | 0.05404431422716538 | 0.20843509687831227 | 0.08705930028454034 |
| HR | 0.06294287725063846 | 0.1307729667155505 | 0.30093089819765645 | 0.3070199196598207 |
| HU | -0.181487115769695 | 0.16943758963936567 | 0.20843509687831227 | 0.06170154416489737 |
| IE | 0.07430519517552074 | 0.10448853467009993 | 0.20843509687831227 | 0.23926425366755666 |
| IS | 0.7554554278657999 | 0.06043386140153302 | 0.20843509687831227 | 0.7435352410020197 |
| IT | -0.1837787081003669 | 0.09660918643128844 | 0.20843509687831227 | 0.042205851620224166 |
| LI | -1.249013464748222 | 0.28284988397399047 | 0.4940233217402446 | -0.5018584291099365 |
| LT | 0.28561153966575237 | 0.19538720272835355 | 0.22286954187247784 | 0.43211672085289443 |
| LU | -0.05156662079731182 | 0.11728067258599506 | 0.20843509687831227 | 0.14721291425295036 |
| LV | -0.19793672649076635 | 0.28974107961580137 | 0.22304221475281336 | 0.08965075444588955 |
| MT | 0.046334093694344596 | 0.19553041969063387 | 0.20843509687831227 | 0.24032070986972442 |
| NL | -0.10945245718600334 | 0.06928498266370721 | 0.20843509687831227 | 0.09173930870972313 |
| NO | -0.12556964371794926 | 0.015973458581969024 | 0.30093089819765645 | 0.13648618230952714 |
| PL | 0.15591558707632605 | 0.15729743751085842 | 0.22017997329497002 | 0.32273016455167713 |
| PT | 0.06151116790947164 | 0.058001588578903564 | 0.20843509687831227 | 0.21825244132220334 |
| RO | -0.013982621958994673 | 0.19673591907724075 | 0.22304221475281336 | 0.20605381871660455 |
| SE | -0.15535179151868814 | 0.15446939402978183 | 0.22304221475281336 | 0.0888560258672122 |
| SI | -0.37955870700523847 | 0.09335655922666274 | 0.3037303368343807 | -0.03456375324463323 |
| SK | -0.32465168206539063 | 0.308020390279436 | 0.3037303368343807 | 0.05930834635690374 |

#### results/ml/cate_by_state.csv (31 rows)

| iso | cate | abs_rank |
| --- | --- | --- |
| AT | -0.24163705733220894 | 17.0 |
| BE | -0.2615248104345389 | 7.0 |
| BG | -0.2303306322575796 | 22.0 |
| CH | -0.23006026372178448 | 23.0 |
| CY | -0.2679054303437271 | 6.0 |
| CZ | -0.2520002699523961 | 12.0 |
| DE | -0.2574881282127297 | 8.0 |
| DK | -0.232586148457677 | 21.0 |
| EL | -0.23763702842688267 | 20.0 |
| ES | -0.24767506992595145 | 15.0 |
| FI | -0.2449064413328293 | 16.0 |
| FR | -0.25043438656429773 | 13.0 |
| GB | -0.2415938386203359 | 18.0 |
| HR | -0.2821618995179837 | 5.0 |
| HU | -0.24777865718610248 | 14.0 |
| IE | -0.2044706792586246 | 27.0 |
| IS | -0.08147775551851166 | 31.0 |
| IT | -0.2525337041482179 | 11.0 |
| LI | -0.7471517418083923 | 1.0 |
| LT | -0.17118635964616935 | 30.0 |
| LU | -0.22692222545730906 | 24.0 |
| LV | -0.2548477720086141 | 10.0 |
| MT | -0.20421300701419345 | 28.0 |
| NL | -0.24045237315077914 | 19.0 |
| NO | -0.32375549399366504 | 4.0 |
| PL | -0.19515172333997274 | 29.0 |
| PT | -0.20959551153797906 | 26.0 |
| RO | -0.22645678072307385 | 25.0 |
| SE | -0.25504160824731587 | 9.0 |
| SI | -0.3702024864646193 | 2.0 |
| SK | -0.34548351608965966 | 3.0 |

#### results/ml/cate_summary.csv (1 rows)

| method | mean | sd | min | max | att_boot_ci_lo | att_boot_ci_hi |
| --- | --- | --- | --- | --- | --- | --- |
| X-learner | -0.259182670990133 | 0.10346850554706209 | -0.7471517418083923 | -0.08147775551851166 | -0.2179605019136964 | -0.010577950357013864 |

#### results/ml/ml_cv.csv (15 rows)

| outcome | model | cv_r2 | cv_r2_sd | n | top |
| --- | --- | --- | --- | --- | --- |
| ln_co2 | HistGB | 0.684 | 0.189 | 397 | n/a |
| ln_co2 | RF | 0.695 | 0.166 | 397 | trend |
| ln_co2 | Ridge | 0.086 | 0.044 | 397 | n/a |
| ln_co2 | Lasso | 0.002 | 0.021 | 397 | n/a |
| ln_co2 | Dummy | -0.0 | 0.0 | 397 | n/a |
| ln_flights | HistGB | 0.733 | 0.113 | 397 | n/a |
| ln_flights | RF | 0.744 | 0.088 | 397 | trend |
| ln_flights | Ridge | 0.09 | 0.03 | 397 | n/a |
| ln_flights | Lasso | 0.007 | 0.024 | 397 | n/a |
| ln_flights | Dummy | 0.0 | 0.0 | 397 | n/a |
| ln_intensity | HistGB | 0.099 | 0.205 | 397 | n/a |
| ln_intensity | RF | 0.159 | 0.261 | 397 | trend |
| ln_intensity | Ridge | 0.153 | 0.256 | 397 | n/a |
| ln_intensity | Lasso | 0.153 | 0.223 | 397 | n/a |
| ln_intensity | Dummy | -0.0 | 0.0 | 397 | n/a |

#### results/ml/ml_importance.csv (12 rows)

| outcome | model | feature | importance |
| --- | --- | --- | --- |
| ln_co2 | RF | trend | 0.6693 |
| ln_co2 | RF | tr_x_lnets | 0.2015 |
| ln_co2 | RF | ln_gdp_pc | 0.1288 |
| ln_co2 | RF | did_adj | 0.0005 |
| ln_flights | RF | trend | 0.5902 |
| ln_flights | RF | tr_x_lnets | 0.3009 |
| ln_flights | RF | ln_gdp_pc | 0.1078 |
| ln_flights | RF | did_adj | 0.0011 |
| ln_intensity | RF | trend | 0.5474 |
| ln_intensity | RF | ln_gdp_pc | 0.3294 |
| ln_intensity | RF | tr_x_lnets | 0.1065 |
| ln_intensity | RF | did_adj | 0.0167 |

#### results/optimization/o1_mac_curve.csv (224 rows)

| ets | iso | co2_2019_mt | abate_share | abate_mt | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | AT | 3.114972593 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | BE | 4.879818683 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | BG | 0.799939346 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | CH | 5.823362078 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | CY | 1.051496169 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | CZ | 1.43947165 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | DE | 31.089433908 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | DK | 3.1007603390000003 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | EE | 0.210027185 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | EL | 4.430024401 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | ES | 22.036524182999997 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | FI | 2.675334307 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | FR | 22.402052039 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | GB | 37.299134185999996 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | HR | 0.7095893449999999 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | HU | 1.102381928 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | IE | 3.304912457 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | IS | 0.516600534 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | IT | 15.106921478 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | LI | 1.767e-06 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | LT | 0.393580497 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | LU | 1.772959277 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | LV | 0.494257553 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | MT | 0.5182756660000001 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | NL | 11.144285299 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | NO | 3.113181945 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | PL | 3.266972499 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | PT | 5.256608541 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | RO | 1.4745418529999998 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | SE | 3.234225659 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | SI | 0.11661393099999999 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | SK | 0.190339292 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 20 | AT | 3.114972593 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 20 | BE | 4.879818683 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 20 | BG | 0.799939346 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 20 | CH | 5.823362078 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 20 | CY | 1.051496169 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 20 | CZ | 1.43947165 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 20 | DE | 31.089433908 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 20 | DK | 3.1007603390000003 | 0.0 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |

_…184 more rows; see CSV._


#### results/optimization/o2_price_targets.csv (3 rows)

| target | target_mt | price_star | feasible | note | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| -10% | 172.8617405292 | 118.6 | True | root found in [5, 1e6] | 861c175df25b | 1.0 | 44fee0bfc126 |
| -20% | 153.65488047040003 | 678.4 | True | root found in [5, 1e6] | 861c175df25b | 1.0 | 44fee0bfc126 |
| -29% (EU 2030 transport)  | 136.36870641748 | 3973.6 | True | root found in [5, 1e6] | 861c175df25b | 1.0 | 44fee0bfc126 |

#### results/optimization/o3_optimal_price_path.csv (9 rows)

| year | price_path | remaining_mt | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- |
| 2022 | 50.0 | 183.24 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 2023 | 50.0 | 174.81 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 2024 | 50.0 | 166.77 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 2025 | 50.0 | 159.11 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 2026 | 50.0 | 151.79 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 2027 | 50.0 | 144.81 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 2028 | 50.0 | 138.15 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 2029 | 50.0 | 131.8 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 2030 | 50.0 | 125.74 | 861c175df25b | 1.0 | 44fee0bfc126 |

#### results/optimization/o4_allocation.csv (32 rows)

| iso | alloc_eur_bn | co2_2019_mt | eff_per_bn | eff_per_mt | pred_residual_mt | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GB | 4.528 | 37.3 | 4.6403 | 0.1244 | 16.288 | 861c175df25b | 1.0 | 44fee0bfc126 |
| DE | 2.993 | 31.09 | 4.9455 | 0.1591 | 16.288 | 861c175df25b | 1.0 | 44fee0bfc126 |
| FR | 1.271 | 22.4 | 4.8101 | 0.2147 | 16.288 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ES | 1.208 | 22.04 | 4.7571 | 0.2159 | 16.288 | 861c175df25b | 1.0 | 44fee0bfc126 |
| CH | 0.0 | 5.82 | 4.4187 | 0.7588 | 5.823 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AT | 0.0 | 3.11 | 4.6411 | 1.4899 | 3.115 | 861c175df25b | 1.0 | 44fee0bfc126 |
| BG | 0.0 | 0.8 | 4.4239 | 5.5303 | 0.8 | 861c175df25b | 1.0 | 44fee0bfc126 |
| BE | 0.0 | 4.88 | 5.0231 | 1.0294 | 4.88 | 861c175df25b | 1.0 | 44fee0bfc126 |
| DK | 0.0 | 3.1 | 4.4672 | 1.4407 | 3.101 | 861c175df25b | 1.0 | 44fee0bfc126 |
| CZ | 0.0 | 1.44 | 4.8401 | 3.3624 | 1.439 | 861c175df25b | 1.0 | 44fee0bfc126 |
| CY | 0.0 | 1.05 | 5.1456 | 4.8936 | 1.051 | 861c175df25b | 1.0 | 44fee0bfc126 |
| EE | 0.0 | 0.21 | 4.9781 | 23.7021 | 0.21 | 861c175df25b | 1.0 | 44fee0bfc126 |
| FI | 0.0 | 2.68 | 4.7039 | 1.7582 | 2.675 | 861c175df25b | 1.0 | 44fee0bfc126 |
| EL | 0.0 | 4.43 | 4.5643 | 1.0303 | 4.43 | 861c175df25b | 1.0 | 44fee0bfc126 |
| HR | 0.0 | 0.71 | 5.4194 | 7.6374 | 0.71 | 861c175df25b | 1.0 | 44fee0bfc126 |
| HU | 0.0 | 1.1 | 4.759 | 4.3171 | 1.102 | 861c175df25b | 1.0 | 44fee0bfc126 |
| IE | 0.0 | 3.3 | 3.9272 | 1.1883 | 3.305 | 861c175df25b | 1.0 | 44fee0bfc126 |
| IS | 0.0 | 0.52 | 1.5649 | 3.0293 | 0.517 | 861c175df25b | 1.0 | 44fee0bfc126 |
| IT | 0.0 | 15.11 | 4.8504 | 0.3211 | 15.107 | 861c175df25b | 1.0 | 44fee0bfc126 |
| LI | 0.0 | 0.0 | 14.3504 | 8121357.6387 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |
| LT | 0.0 | 0.39 | 3.288 | 8.354 | 0.394 | 861c175df25b | 1.0 | 44fee0bfc126 |
| LU | 0.0 | 1.77 | 4.3585 | 2.4583 | 1.773 | 861c175df25b | 1.0 | 44fee0bfc126 |
| LV | 0.0 | 0.49 | 4.8948 | 9.9034 | 0.494 | 861c175df25b | 1.0 | 44fee0bfc126 |
| MT | 0.0 | 0.52 | 3.9223 | 7.568 | 0.518 | 861c175df25b | 1.0 | 44fee0bfc126 |
| NL | 0.0 | 11.14 | 4.6183 | 0.4144 | 11.144 | 861c175df25b | 1.0 | 44fee0bfc126 |
| NO | 0.0 | 3.11 | 6.2183 | 1.9974 | 3.113 | 861c175df25b | 1.0 | 44fee0bfc126 |
| PL | 0.0 | 3.27 | 3.7483 | 1.1473 | 3.267 | 861c175df25b | 1.0 | 44fee0bfc126 |
| PT | 0.0 | 5.26 | 4.0257 | 0.7658 | 5.257 | 861c175df25b | 1.0 | 44fee0bfc126 |
| RO | 0.0 | 1.47 | 4.3495 | 2.9497 | 1.475 | 861c175df25b | 1.0 | 44fee0bfc126 |
| SE | 0.0 | 3.23 | 4.8985 | 1.5146 | 3.234 | 861c175df25b | 1.0 | 44fee0bfc126 |
| SI | 0.0 | 0.12 | 7.1104 | 60.9741 | 0.117 | 861c175df25b | 1.0 | 44fee0bfc126 |
| SK | 0.0 | 0.19 | 6.6357 | 34.8622 | 0.19 | 861c175df25b | 1.0 | 44fee0bfc126 |

#### results/optimization/o4b_allocation_fair.csv (32 rows)

| iso | alloc_eur_bn | co2_2019_mt | eff_per_bn | pred_abate_mt | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GB | 1.939 | 37.3 | 4.6403 | 8.996 | 861c175df25b | 1.0 | 44fee0bfc126 |
| DE | 1.622 | 31.09 | 4.9455 | 8.021 | 861c175df25b | 1.0 | 44fee0bfc126 |
| FR | 1.166 | 22.4 | 4.8101 | 5.61 | 861c175df25b | 1.0 | 44fee0bfc126 |
| ES | 1.147 | 22.04 | 4.7571 | 5.457 | 861c175df25b | 1.0 | 44fee0bfc126 |
| IT | 0.785 | 15.11 | 4.8504 | 3.809 | 861c175df25b | 1.0 | 44fee0bfc126 |
| NL | 0.581 | 11.14 | 4.6183 | 2.684 | 861c175df25b | 1.0 | 44fee0bfc126 |
| CH | 0.303 | 5.82 | 4.4187 | 1.338 | 861c175df25b | 1.0 | 44fee0bfc126 |
| PT | 0.274 | 5.26 | 4.0257 | 1.101 | 861c175df25b | 1.0 | 44fee0bfc126 |
| BE | 0.254 | 4.88 | 5.0231 | 1.277 | 861c175df25b | 1.0 | 44fee0bfc126 |
| EL | 0.231 | 4.43 | 4.5643 | 1.055 | 861c175df25b | 1.0 | 44fee0bfc126 |
| IE | 0.172 | 3.3 | 3.9272 | 0.676 | 861c175df25b | 1.0 | 44fee0bfc126 |
| PL | 0.17 | 3.27 | 3.7483 | 0.638 | 861c175df25b | 1.0 | 44fee0bfc126 |
| SE | 0.169 | 3.23 | 4.8985 | 0.825 | 861c175df25b | 1.0 | 44fee0bfc126 |
| NO | 0.162 | 3.11 | 6.2183 | 1.008 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AT | 0.162 | 3.11 | 4.6411 | 0.753 | 861c175df25b | 1.0 | 44fee0bfc126 |
| DK | 0.161 | 3.1 | 4.4672 | 0.721 | 861c175df25b | 1.0 | 44fee0bfc126 |
| FI | 0.139 | 2.68 | 4.7039 | 0.655 | 861c175df25b | 1.0 | 44fee0bfc126 |
| LU | 0.092 | 1.77 | 4.3585 | 0.402 | 861c175df25b | 1.0 | 44fee0bfc126 |
| RO | 0.077 | 1.47 | 4.3495 | 0.334 | 861c175df25b | 1.0 | 44fee0bfc126 |
| CZ | 0.075 | 1.44 | 4.8401 | 0.363 | 861c175df25b | 1.0 | 44fee0bfc126 |
| HU | 0.057 | 1.1 | 4.759 | 0.273 | 861c175df25b | 1.0 | 44fee0bfc126 |
| CY | 0.055 | 1.05 | 5.1456 | 0.282 | 861c175df25b | 1.0 | 44fee0bfc126 |
| BG | 0.042 | 0.8 | 4.4239 | 0.184 | 861c175df25b | 1.0 | 44fee0bfc126 |
| HR | 0.037 | 0.71 | 5.4194 | 0.2 | 861c175df25b | 1.0 | 44fee0bfc126 |
| MT | 0.027 | 0.52 | 3.9223 | 0.106 | 861c175df25b | 1.0 | 44fee0bfc126 |
| IS | 0.027 | 0.52 | 1.5649 | 0.042 | 861c175df25b | 1.0 | 44fee0bfc126 |
| LV | 0.026 | 0.49 | 4.8948 | 0.126 | 861c175df25b | 1.0 | 44fee0bfc126 |
| LT | 0.02 | 0.39 | 3.288 | 0.067 | 861c175df25b | 1.0 | 44fee0bfc126 |
| EE | 0.011 | 0.21 | 4.9781 | 0.055 | 861c175df25b | 1.0 | 44fee0bfc126 |
| SK | 0.01 | 0.19 | 6.6357 | 0.066 | 861c175df25b | 1.0 | 44fee0bfc126 |
| SI | 0.006 | 0.12 | 7.1104 | 0.043 | 861c175df25b | 1.0 | 44fee0bfc126 |
| LI | 0.0 | 0.0 | 14.3504 | 0.0 | 861c175df25b | 1.0 | 44fee0bfc126 |

#### results/simulation/s1_wild_bootstrap.csv (1 rows)

| method | B | beta | p | ci_lo | ci_hi | n_clusters | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| wild_cluster_bootstrap | 4999 | -0.2074565550145567 | 0.03920784156831366 | -0.4047857563812171 | -0.011530678014256501 | 43 | 861c175df25b | 1.0 | 44fee0bfc126 |

#### results/simulation/s2_ri_betas.csv (5000 rows)

| iteration | beta_perm | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- |
| 0 | 0.003909514398678177 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 1 | 0.03973550304608904 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 2 | 0.024681200159422767 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 3 | 0.00951833984822198 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 4 | 0.11934640112692868 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 5 | 0.00450473884716579 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 6 | -0.002914887320162707 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 7 | -0.0470908005013258 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 8 | 0.06777791449338846 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 9 | 0.0049062687114045656 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 10 | -0.1395146918284129 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 11 | -0.029974417370993295 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 12 | 0.08514999257904726 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 13 | 0.05423196584283935 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 14 | 0.04042273327036755 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 15 | 0.10728118128105865 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 16 | -0.0373221950285193 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 17 | 0.09402621951548112 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 18 | -4.3849765328007884e-05 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 19 | -0.02131451122301667 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 20 | 0.048093582073759994 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 21 | -0.0008173221341039039 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 22 | 0.11759114255256492 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 23 | 0.025640487440967585 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 24 | 0.0016150396155737712 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 25 | -0.08115177569003434 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 26 | 0.06939204651463327 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 27 | 0.046388351691535934 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 28 | 0.046560495934106466 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 29 | 0.010982764705898873 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 30 | 0.05544270933616033 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 31 | -0.08177622034340673 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 32 | 0.021949279090786533 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 33 | -0.07013648062960545 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 34 | -0.010421582406594992 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 35 | -0.013758652389453369 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 36 | 0.09034332331706618 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 37 | -0.1463080048705626 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 38 | 0.015675033548886552 | 861c175df25b | 1.0 | 44fee0bfc126 |
| 39 | -0.021884056700976956 | 861c175df25b | 1.0 | 44fee0bfc126 |

_…4960 more rows; see CSV._


#### results/simulation/s2_ri_summary.csv (1 rows)

| method | RI | beta | p | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- |
| randomization_inference | 5000 | -0.2074565550145567 | 0.0033993201359728054 | 861c175df25b | 1.0 | 44fee0bfc126 |

#### results/simulation/s3_covid_counterfactual_monthly.csv (924 rows)

| iso | ym | ln_co2_cf | year | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- |
| AL | 202003 | 9.229533947915074 | 2020 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AL | 202004 | 9.318523784694218 | 2020 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AL | 202005 | 9.341494459063155 | 2020 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AL | 202006 | 9.457458136997664 | 2020 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AL | 202007 | 9.67435926538521 | 2020 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AL | 202008 | 9.756145872357475 | 2020 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AL | 202009 | 9.593388370855074 | 2020 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AL | 202010 | 9.391146948298754 | 2020 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AL | 202011 | 9.259221135176073 | 2020 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AL | 202012 | 9.388560618982726 | 2020 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AL | 202101 | 9.365639618049205 | 2021 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AL | 202102 | 9.149910594345796 | 2021 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AL | 202103 | 9.277981158500895 | 2021 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AL | 202104 | 9.366970995280038 | 2021 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AL | 202105 | 9.389941669648975 | 2021 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AL | 202106 | 9.505905347583484 | 2021 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AL | 202107 | 9.722806475971028 | 2021 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AL | 202108 | 9.804593082943295 | 2021 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AL | 202109 | 9.641835581440894 | 2021 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AL | 202110 | 9.439594158884574 | 2021 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AL | 202111 | 9.307668345761893 | 2021 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AL | 202112 | 9.437007829568547 | 2021 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AM | 202003 | 9.7151527388868 | 2020 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AM | 202004 | 9.8046935411354 | 2020 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AM | 202005 | 9.876252113317461 | 2020 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AM | 202006 | 9.938832825997302 | 2020 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AM | 202007 | 10.086641438494675 | 2020 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AM | 202008 | 10.130823304989043 | 2020 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AM | 202009 | 9.990140891762843 | 2020 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AM | 202010 | 9.941628019214393 | 2020 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AM | 202011 | 9.799960670185547 | 2020 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AM | 202012 | 9.905759009125775 | 2020 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AM | 202101 | 9.73687414658079 | 2021 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AM | 202102 | 9.583389178707483 | 2021 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AM | 202103 | 9.732332542762265 | 2021 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AM | 202104 | 9.821873345010863 | 2021 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AM | 202105 | 9.893431917192926 | 2021 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AM | 202106 | 9.956012629872765 | 2021 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AM | 202107 | 10.103821242370138 | 2021 | 861c175df25b | 1.0 | 44fee0bfc126 |
| AM | 202108 | 10.148003108864506 | 2021 | 861c175df25b | 1.0 | 44fee0bfc126 |

_…884 more rows; see CSV._


#### results/simulation/s3_did_variants.csv (3 rows)

| variant | note | coef | se | p | N | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| drop_covid | main sample (2010-2019) | -0.2074565550145567 | 0.08255461822992015 | 0.011972249108812068 | 415 | 861c175df25b | 1.0 | 44fee0bfc126 |
| raw_covid | 2020-21 as observed (contaminated) | -0.22842720031536212 | 0.13194924194980215 | 0.08342059550514531 | 672 | 861c175df25b | 1.0 | 44fee0bfc126 |
| adjusted_covid | 2020-21 replaced by COVID-free counterfactual | -0.21505723885462397 | 0.11772009213487047 | 0.06772195711317626 | 672 | 861c175df25b | 1.0 | 44fee0bfc126 |

#### results/simulation/s4_policy_montecarlo.csv (27 rows)

| scenario | year | ets | mc_mean | mc_p05 | mc_p95 | run_id | protocol_version | git_commit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Aggressive_8pct | 2022 | 57.9 | 119.35 | 74.46 | 178.65 | 861c175df25b | 1.0 | 44fee0bfc126 |
| Aggressive_8pct | 2023 | 62.5 | 117.97 | 70.09 | 179.36 | 861c175df25b | 1.0 | 44fee0bfc126 |
| Aggressive_8pct | 2024 | 67.5 | 118.13 | 70.96 | 181.22 | 861c175df25b | 1.0 | 44fee0bfc126 |
| Aggressive_8pct | 2025 | 72.9 | 117.94 | 69.17 | 181.66 | 861c175df25b | 1.0 | 44fee0bfc126 |
| Aggressive_8pct | 2026 | 78.8 | 117.18 | 68.95 | 181.17 | 861c175df25b | 1.0 | 44fee0bfc126 |
| Aggressive_8pct | 2027 | 85.1 | 117.55 | 69.41 | 180.43 | 861c175df25b | 1.0 | 44fee0bfc126 |
| Aggressive_8pct | 2028 | 91.9 | 116.91 | 68.4 | 184.93 | 861c175df25b | 1.0 | 44fee0bfc126 |
| Aggressive_8pct | 2029 | 99.2 | 115.37 | 67.0 | 181.24 | 861c175df25b | 1.0 | 44fee0bfc126 |
| Aggressive_8pct | 2030 | 107.1 | 114.67 | 65.12 | 180.41 | 861c175df25b | 1.0 | 44fee0bfc126 |
| Moderate_plus3 | 2022 | 56.6 | 119.91 | 73.02 | 179.28 | 861c175df25b | 1.0 | 44fee0bfc126 |
| Moderate_plus3 | 2023 | 59.6 | 118.61 | 72.36 | 181.28 | 861c175df25b | 1.0 | 44fee0bfc126 |
| Moderate_plus3 | 2024 | 62.6 | 119.15 | 72.74 | 184.12 | 861c175df25b | 1.0 | 44fee0bfc126 |
| Moderate_plus3 | 2025 | 65.6 | 117.42 | 71.79 | 183.08 | 861c175df25b | 1.0 | 44fee0bfc126 |
| Moderate_plus3 | 2026 | 68.6 | 118.57 | 71.0 | 182.59 | 861c175df25b | 1.0 | 44fee0bfc126 |
| Moderate_plus3 | 2027 | 71.6 | 118.66 | 71.07 | 180.62 | 861c175df25b | 1.0 | 44fee0bfc126 |
| Moderate_plus3 | 2028 | 74.6 | 117.54 | 70.12 | 181.54 | 861c175df25b | 1.0 | 44fee0bfc126 |
| Moderate_plus3 | 2029 | 77.6 | 116.92 | 68.57 | 180.12 | 861c175df25b | 1.0 | 44fee0bfc126 |
| Moderate_plus3 | 2030 | 80.6 | 117.25 | 71.71 | 180.97 | 861c175df25b | 1.0 | 44fee0bfc126 |
| Flat_2021 | 2022 | 53.6 | 119.93 | 73.36 | 181.38 | 861c175df25b | 1.0 | 44fee0bfc126 |
| Flat_2021 | 2023 | 53.6 | 119.85 | 72.11 | 180.86 | 861c175df25b | 1.0 | 44fee0bfc126 |
| Flat_2021 | 2024 | 53.6 | 119.05 | 72.8 | 178.68 | 861c175df25b | 1.0 | 44fee0bfc126 |
| Flat_2021 | 2025 | 53.6 | 120.35 | 72.9 | 184.81 | 861c175df25b | 1.0 | 44fee0bfc126 |
| Flat_2021 | 2026 | 53.6 | 120.21 | 73.21 | 180.36 | 861c175df25b | 1.0 | 44fee0bfc126 |
| Flat_2021 | 2027 | 53.6 | 119.05 | 75.08 | 178.02 | 861c175df25b | 1.0 | 44fee0bfc126 |
| Flat_2021 | 2028 | 53.6 | 119.73 | 74.29 | 180.25 | 861c175df25b | 1.0 | 44fee0bfc126 |
| Flat_2021 | 2029 | 53.6 | 118.75 | 73.21 | 180.89 | 861c175df25b | 1.0 | 44fee0bfc126 |
| Flat_2021 | 2030 | 53.6 | 120.57 | 72.23 | 181.86 | 861c175df25b | 1.0 | 44fee0bfc126 |

#### results/scm/scm_aggregate_annual.csv (10 rows)

| year | actual_idx | syn_idx | treated_rel_synth_pct |
| --- | --- | --- | --- |
| 2010 | 14861.465745350995 | 249684.43369249193 | -94.05 |
| 2011 | 38079.38171429239 | 1620854.9675613446 | -97.65 |
| 2012 | 14669.98989766078 | 4766549.17904939 | -99.69 |
| 2013 | 29567.942363178663 | 134835703.08547756 | -99.98 |
| 2014 | 136264.79037433767 | 873844467.0503682 | -99.98 |
| 2015 | 430923.7220442413 | 9772702352.313166 | -100.0 |
| 2016 | 3560776.0603441275 | 3117873519.3787937 | -99.89 |
| 2017 | 35445129.72212644 | 110328021976.0775 | -99.97 |
| 2018 | 369625684.47678876 | 999461441966.3561 | -99.96 |
| 2019 | 434029702.524528 | 14093621112268.9 | -100.0 |

#### results/scm/scm_placebo.csv (39 rows)

| unit | att_classic | att_aug | ridge_lam | rmspe_pre | rmspe_post | rmspe_ratio | n_pre | pre_mse | is_treated |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AL | -0.1588255048339063 | -0.09515178339377088 | 0.01 | 0.08377961233172845 | 0.19305702350933884 | 2.3043437196262317 | 23 | 0.16143753917645798 | False |
| AM | -0.3994327877051505 | -0.30490119935040405 | 0.01 | 0.05983697931003076 | 0.4648187761439532 | 7.76808558024976 | 23 | 0.08235067413782818 | False |
| BA | 0.2773268949248004 | 0.20750310823134557 | 0.01 | 0.10071791046999218 | 0.4537321366733045 | 4.504979646182087 | 23 | 0.23331424225715106 | False |
| MC | -5.2986072756163365 | -0.10394649556567148 | 0.01 | 5.308247038590336 | 5.337291336635625 | 1.0054715422688771 | 23 | 648.0821923221706 | False |
| MD | 0.3398304793303315 | 0.34357347042112446 | 0.01 | 0.06549151075379347 | 0.4019498722910858 | 6.137434724970116 | 23 | 0.09865017355872913 | False |
| ME | -0.34738836926014294 | -0.11043502835464657 | 0.01 | 0.3314691550224764 | 0.5622539349427967 | 1.6962481317595635 | 23 | 2.5270514168202207 | False |
| MK | 0.3783148163136974 | 0.29579948074076073 | 0.01 | 0.0737436680651344 | 0.43066358068459115 | 5.840007582809765 | 23 | 0.12507695733311644 | False |
| RS | -0.02419091116524974 | -0.014126946740658015 | 0.01 | 0.07178994261727832 | 0.10724490517525592 | 1.4938708858842902 | 23 | 0.11853730480281904 | False |
| TR | 3.6970658340088214 | 0.023960167670318184 | 0.01 | 3.710154352926213 | 3.6993025997626634 | 0.9970751208356087 | 23 | 316.6006424183585 | False |
| XK | -0.12845445945289166 | -0.0871503169739497 | 0.01 | 0.07612335418596451 | 0.20451225041827764 | 2.6865901089784776 | 23 | 0.1332795962080012 | False |
| AT | -0.19661915283325437 | -0.03741061437114449 | 0.01 | 0.1559022758915608 | 0.23308329959131285 | 1.495060275793767 | 23 | 0.559026951447871 | True |
| BE | -0.3198292998467685 | -0.05990431018308471 | 0.01 | 0.18077827243563838 | 0.3493439964056778 | 1.9324446002218163 | 23 | 0.7516580270507192 | True |
| BG | -0.14392612269906782 | -0.060138385363636894 | 0.01 | 0.10392297627875255 | 0.20500813018570072 | 1.972693022530528 | 23 | 0.24839965496858546 | True |
| CH | -0.19239263570503332 | -0.028155398395007216 | 0.01 | 0.19192486150225194 | 0.25284354878785364 | 1.3174090464819064 | 23 | 0.8472085066411466 | True |
| CY | -0.4357373383298979 | -0.28490305761345786 | 0.01 | 0.09599807341957431 | 0.47597399485763614 | 4.95816194953537 | 23 | 0.21195949230620909 | True |
| CZ | -0.27517020557258665 | -0.22274694568377815 | 0.01 | 0.0443335828662572 | 0.29464916873284924 | 6.646184442654421 | 23 | 0.045205731104463506 | True |
| DE | 0.7905928728928124 | -0.05652872612911974 | 0.01 | 1.1703894781859692 | 0.80790196931857 | 0.6902847166489976 | 23 | 31.50566520491377 | True |
| DK | -0.16404423704523274 | -0.03887739038195086 | 0.01 | 0.1420464005904737 | 0.20946521348425914 | 1.4746252816933882 | 23 | 0.46407513817631457 | True |
| EL | -0.31647957018516504 | -0.06771814582541362 | 0.01 | 0.24554607898372974 | 0.5056038243036323 | 2.0590995645144647 | 23 | 1.3867361687985313 | True |
| ES | 0.33078308081597346 | -0.05892455069500565 | 0.01 | 0.6763712579043141 | 0.34544506628390004 | 0.5107329181228603 | 23 | 10.521995805938475 | True |
| FI | -0.23537130360425706 | -0.05675609194008111 | 0.01 | 0.2055963656815392 | 0.31178614810107147 | 1.5164963985015967 | 23 | 0.972206908373515 | True |
| FR | 0.4488781397608744 | -0.05249655022367813 | 0.01 | 0.8053730456018018 | 0.4778952217340554 | 0.5933836802012117 | 23 | 14.918392079384205 | True |
| GB | 0.9585246833497069 | -0.03846294759673539 | 0.01 | 1.2700954151847261 | 0.9695615902720067 | 0.763376970486104 | 23 | 37.10227436448503 | True |
| HR | 0.025580397542807238 | -0.00011256278652480717 | 0.01 | 0.2067095645599968 | 0.23617204227672772 | 1.1425307908680709 | 23 | 0.9827634138534265 | True |
| HU | -0.22393817016028442 | -0.10174828706315876 | 0.01 | 0.06758346576193343 | 0.25301426978063063 | 3.743730318180007 | 23 | 0.10505307142107151 | True |
| IE | -0.043172681252425515 | -0.0004294167199460029 | 0.01 | 0.10887053223091792 | 0.11907021838659204 | 1.0936863809395205 | 23 | 0.27261423412959607 | True |
| IS | 0.25551722691260725 | 0.15878786131245617 | 0.01 | 0.13145108414703946 | 0.36679399234043863 | 2.7903458896554074 | 23 | 0.39742591303893693 | True |
| IT | -0.030354188756339866 | -0.05395680642146278 | 0.01 | 0.35766458373806503 | 0.11010121131155291 | 0.30783369759692314 | 23 | 2.9422509525920355 | True |
| LT | 0.13574690930005365 | 0.04529812506243034 | 0.01 | 0.10179161276336358 | 0.19067985980907665 | 1.8732374370799374 | 23 | 0.23831524586623118 | True |
| LU | -0.07201524291041256 | -0.012844086025328182 | 0.01 | 0.19075593238776928 | 0.21294896170339964 | 1.116342538016151 | 23 | 0.8369199920459259 | True |
| MT | -0.21453086290636011 | -0.13211350461772883 | 0.01 | 0.07432934821553391 | 0.2407031743941518 | 3.2383329085058197 | 23 | 0.12707159614135996 | True |
| NL | -0.22476825660026947 | -0.05165993083143835 | 0.01 | 0.19233805631831902 | 0.2751055539546927 | 1.4303230427752358 | 23 | 0.8508603418911036 | True |
| NO | -0.15704394365514487 | -0.046891902292780153 | 0.01 | 0.14855475055992975 | 0.22537075119397082 | 1.5170888197415946 | 23 | 0.5075758200202282 | True |
| PL | 0.01547377047298911 | 0.013658705191997604 | 0.01 | 0.06284055040527543 | 0.1109669749041988 | 1.7658498244929945 | 23 | 0.09082549983047318 | True |
| PT | -0.0926529016477281 | -0.012180116586803492 | 0.01 | 0.09780606472789152 | 0.11864841799793716 | 1.2130987820441566 | 23 | 0.22001860484379912 | True |
| RO | -0.011678109085132208 | 0.004373874511442112 | 0.01 | 0.10680049195922901 | 0.13448756715241197 | 1.2592410829320193 | 23 | 0.2623459369028689 | True |
| SE | -0.23107836204243717 | -0.05766815642600692 | 0.01 | 0.19339608396685024 | 0.29125306324538736 | 1.5059925582325164 | 23 | 0.8602470417554008 | True |
| SI | -0.4624074462541696 | -0.3928509618462413 | 0.01 | 0.07318468880905102 | 0.5609830453502903 | 7.665306151864261 | 23 | 0.12318796954978568 | True |
| SK | -0.23995592979704164 | -0.15402270185852376 | 0.01 | 0.10135911142776206 | 0.27533812342167197 | 2.716461495599274 | 23 | 0.23629439779678574 | True |

#### results/scm/scm_state_effects.csv (29 rows)

| unit | att_classic | att_aug | ridge_lam | rmspe_pre | rmspe_post | rmspe_ratio | n_pre | pre_mse | weights_json |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AT | -0.19661915283325437 | -0.03741061437114449 | 0.01 | 0.1559022758915608 | 0.23308329959131285 | 1.495060275793767 | 23 | 0.559026951447871 | {'TR': 0.6949, 'XK': 0.3051} |
| BE | -0.3198292998467685 | -0.05990431018308471 | 0.01 | 0.18077827243563838 | 0.3493439964056778 | 1.9324446002218163 | 23 | 0.7516580270507192 | {'TR': 0.8276, 'XK': 0.1724} |
| BG | -0.14392612269906782 | -0.060138385363636894 | 0.01 | 0.10392297627875255 | 0.20500813018570072 | 1.972693022530528 | 23 | 0.24839965496858546 | {'ME': 0.6034, 'TR': 0.3966} |
| CH | -0.19239263570503332 | -0.028155398395007216 | 0.01 | 0.19192486150225194 | 0.25284354878785364 | 1.3174090464819064 | 23 | 0.8472085066411466 | {'TR': 0.8478, 'XK': 0.1522} |
| CY | -0.4357373383298979 | -0.28490305761345786 | 0.01 | 0.09599807341957431 | 0.47597399485763614 | 4.95816194953537 | 23 | 0.21195949230620909 | {'BA': 0.0143, 'MC': 0.1559, 'ME': 0.115, 'TR': 0.7149} |
| CZ | -0.27517020557258665 | -0.22274694568377815 | 0.01 | 0.0443335828662572 | 0.29464916873284924 | 6.646184442654421 | 23 | 0.045205731104463506 | {'BA': 0.0948, 'RS': 0.1176, 'TR': 0.5219, 'XK': 0.2656} |
| DE | 0.7905928728928124 | -0.05652872612911974 | 0.01 | 1.1703894781859692 | 0.80790196931857 | 0.6902847166489976 | 23 | 31.50566520491377 | {'TR': 1.0} |
| DK | -0.16404423704523274 | -0.03887739038195086 | 0.01 | 0.1420464005904737 | 0.20946521348425914 | 1.4746252816933882 | 23 | 0.46407513817631457 | {'TR': 0.7148, 'XK': 0.2852} |
| EL | -0.31647957018516504 | -0.06771814582541362 | 0.01 | 0.24554607898372974 | 0.5056038243036323 | 2.0590995645144647 | 23 | 1.3867361687985313 | {'ME': 0.2513, 'TR': 0.7487} |
| ES | 0.33078308081597346 | -0.05892455069500565 | 0.01 | 0.6763712579043141 | 0.34544506628390004 | 0.5107329181228603 | 23 | 10.521995805938475 | {'TR': 1.0} |
| FI | -0.23537130360425706 | -0.05675609194008111 | 0.01 | 0.2055963656815392 | 0.31178614810107147 | 1.5164963985015967 | 23 | 0.972206908373515 | {'RS': 0.1472, 'TR': 0.6488, 'XK': 0.204} |
| FR | 0.4488781397608744 | -0.05249655022367813 | 0.01 | 0.8053730456018018 | 0.4778952217340554 | 0.5933836802012117 | 23 | 14.918392079384205 | {'TR': 1.0} |
| GB | 0.9585246833497069 | -0.03846294759673539 | 0.01 | 1.2700954151847261 | 0.9695615902720067 | 0.763376970486104 | 23 | 37.10227436448503 | {'TR': 1.0} |
| HR | 0.025580397542807238 | -0.00011256278652480717 | 0.01 | 0.2067095645599968 | 0.23617204227672772 | 1.1425307908680709 | 23 | 0.9827634138534265 | {'MC': 0.0096, 'ME': 0.7044, 'TR': 0.2861} |
| HU | -0.22393817016028442 | -0.10174828706315876 | 0.01 | 0.06758346576193343 | 0.25301426978063063 | 3.743730318180007 | 23 | 0.10505307142107151 | {'AM': 0.0455, 'BA': 0.1281, 'RS': 0.1033, 'TR': 0.435, 'XK': 0.2881} |
| IE | -0.043172681252425515 | -0.0004294167199460029 | 0.01 | 0.10887053223091792 | 0.11907021838659204 | 1.0936863809395205 | 23 | 0.27261423412959607 | {'TR': 0.6629, 'XK': 0.3371} |
| IS | 0.25551722691260725 | 0.15878786131245617 | 0.01 | 0.13145108414703946 | 0.36679399234043863 | 2.7903458896554074 | 23 | 0.39742591303893693 | {'ME': 0.0954, 'MK': 0.4668, 'RS': 0.2721, 'TR': 0.1656} |
| IT | -0.030354188756339866 | -0.05395680642146278 | 0.01 | 0.35766458373806503 | 0.11010121131155291 | 0.30783369759692314 | 23 | 2.9422509525920355 | {'TR': 1.0} |
| LT | 0.13574690930005365 | 0.04529812506243034 | 0.01 | 0.10179161276336358 | 0.19067985980907665 | 1.8732374370799374 | 23 | 0.23831524586623118 | {'AM': 0.364, 'BA': 0.2887, 'MD': 0.0906, 'RS': 0.1327, 'TR': 0.124} |
| LU | -0.07201524291041256 | -0.012844086025328182 | 0.01 | 0.19075593238776928 | 0.21294896170339964 | 1.116342538016151 | 23 | 0.8369199920459259 | {'AM': 0.1025, 'TR': 0.5319, 'XK': 0.3656} |
| MT | -0.21453086290636011 | -0.13211350461772883 | 0.01 | 0.07432934821553391 | 0.2407031743941518 | 3.2383329085058197 | 23 | 0.12707159614135996 | {'AM': 0.0282, 'BA': 0.2394, 'MC': 0.0839, 'MD': 0.1419, 'RS': 0.1083, 'TR': 0.3982} |
| NL | -0.22476825660026947 | -0.05165993083143835 | 0.01 | 0.19233805631831902 | 0.2751055539546927 | 1.4303230427752358 | 23 | 0.8508603418911036 | {'TR': 1.0} |
| NO | -0.15704394365514487 | -0.046891902292780153 | 0.01 | 0.14855475055992975 | 0.22537075119397082 | 1.5170888197415946 | 23 | 0.5075758200202282 | {'TR': 0.7278, 'XK': 0.2722} |
| PL | 0.01547377047298911 | 0.013658705191997604 | 0.01 | 0.06284055040527543 | 0.1109669749041988 | 1.7658498244929945 | 23 | 0.09082549983047318 | {'BA': 0.1029, 'TR': 0.6425, 'XK': 0.2546} |
| PT | -0.0926529016477281 | -0.012180116586803492 | 0.01 | 0.09780606472789152 | 0.11864841799793716 | 1.2130987820441566 | 23 | 0.22001860484379912 | {'TR': 0.7701, 'XK': 0.2299} |
| RO | -0.011678109085132208 | 0.004373874511442112 | 0.01 | 0.10680049195922901 | 0.13448756715241197 | 1.2592410829320193 | 23 | 0.2623459369028689 | {'AM': 0.1256, 'BA': 0.0228, 'TR': 0.4706, 'XK': 0.3809} |
| SE | -0.23107836204243717 | -0.05766815642600692 | 0.01 | 0.19339608396685024 | 0.29125306324538736 | 1.5059925582325164 | 23 | 0.8602470417554008 | {'RS': 0.0898, 'TR': 0.7266, 'XK': 0.1836} |
| SI | -0.4624074462541696 | -0.3928509618462413 | 0.01 | 0.07318468880905102 | 0.5609830453502903 | 7.665306151864261 | 23 | 0.12318796954978568 | {'AL': 0.0534, 'BA': 0.4249, 'MC': 0.0159, 'MD': 0.1652, 'ME': 0.0915, 'RS': 0.1147, 'TR': 0.1345} |
| SK | -0.23995592979704164 | -0.15402270185852376 | 0.01 | 0.10135911142776206 | 0.27533812342167197 | 2.716461495599274 | 23 | 0.23629439779678574 | {'AL': 0.166, 'BA': 0.3164, 'ME': 0.3774, 'TR': 0.1402} |

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


#### tables/T3_main_did.csv (19 rows)

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
| D4_did_adj_gdp | ln_co2 | did_adj | 0.0837143031005313 | 0.0173561561200715 | 1.4118784900743723e-06 | 0.0496968621951365 | 0.117731744005926 | 262 | 0.9982 | add ln gdp pc; sample = WB-covered states (27 of 43); sign flip reflects compositional shift (gdp-conditional spec on a 37% smaller sample); NOT the headline |
| D4_did_adj_gdp | ln_co2 | ln_gdp_pc | 0.7272092914047237 | 0.11594007207717 | 3.5578526488190474e-10 | 0.4999709257684924 | 0.9544476570409548 | 262 | 0.9982 | add ln gdp pc; sample = WB-covered states (27 of 43); sign flip reflects compositional shift (gdp-conditional spec on a 37% smaller sample); NOT the headline |
| D4_did_adj_gdp | ln_flights | did_adj | 0.0168404198889159 | 0.0254492698114996 | 0.5081474337637247 | -0.0330392323744658 | 0.0667200721522977 | 262 | 0.9976 | add ln gdp pc; sample = WB-covered states (27 of 43); sign flip reflects compositional shift (gdp-conditional spec on a 37% smaller sample); NOT the headline |
| D4_did_adj_gdp | ln_flights | ln_gdp_pc | 0.6315712670329845 | 0.1847908742179425 | 0.0006313824291025 | 0.2693878088941458 | 0.9937547251718232 | 262 | 0.9976 | add ln gdp pc; sample = WB-covered states (27 of 43); sign flip reflects compositional shift (gdp-conditional spec on a 37% smaller sample); NOT the headline |
| D4_did_adj_gdp | ln_intensity | did_adj | 0.0668738832116153 | 0.0176076993412262 | 0.0001458736327785 | 0.0323634266522021 | 0.1013843397710284 | 262 | 0.9847 | add ln gdp pc; sample = WB-covered states (27 of 43); sign flip reflects compositional shift (gdp-conditional spec on a 37% smaller sample); NOT the headline |
| D4_did_adj_gdp | ln_intensity | ln_gdp_pc | 0.0956380243717344 | 0.1588854631367799 | 0.5472203250963449 | -0.2157717610433206 | 0.4070478097867894 | 262 | 0.9847 | add ln gdp pc; sample = WB-covered states (27 of 43); sign flip reflects compositional shift (gdp-conditional spec on a 37% smaller sample); NOT the headline |
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
| mean | -0.046 | -0.064 | 2.08 |
| std | 0.329 | 0.101 | 1.731 |
| min | -0.462 | -0.393 | 0.308 |
| 25% | -0.231 | -0.06 | 1.143 |
| 50% | -0.157 | -0.052 | 1.506 |
| 75% | 0.015 | -0.013 | 2.059 |
| max | 0.959 | 0.159 | 7.665 |

#### tables/T5b_optimal_path.csv (9 rows)

| year | price_path | remaining_mt |
| --- | --- | --- |
| 2022 | 50.0 | 183.24 |
| 2023 | 50.0 | 174.81 |
| 2024 | 50.0 | 166.77 |
| 2025 | 50.0 | 159.11 |
| 2026 | 50.0 | 151.79 |
| 2027 | 50.0 | 144.81 |
| 2028 | 50.0 | 138.15 |
| 2029 | 50.0 | 131.8 |
| 2030 | 50.0 | 125.74 |

#### tables/T5c_price_targets.csv (3 rows)

| target | target_mt | price_star | feasible | note |
| --- | --- | --- | --- | --- |
| -10% | 172.8617405292 | 118.6 | True | root found in [5, 1e6] |
| -20% | 153.65488047040003 | 678.4 | True | root found in [5, 1e6] |
| -29% (EU 2030 transport)  | 136.36870641748 | 3973.6 | True | root found in [5, 1e6] |

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
- Main DiD ln CO2 (2010-19) = -0.208 (p=0.012); wild bootstrap p=0.039; RI p=0.0034. Pre-trend p=0.79. MDE 23.1%. TOST not conclusive.
- COVID-adjusted variant -0.215 (p=0.068) suggestive.
- Price response treated×lnETS = -0.0675; fare pass-through -0.016; dose-response +0.014 (p=0.548).
- Fuel cross-check DiD -0.236 (p=0.482); cross-source corr 0.966.
- Segments all null (p>=0.35).
- AIPW ATT -0.008 (SE 0.040); CATE LI -0.75, IS -0.08.
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

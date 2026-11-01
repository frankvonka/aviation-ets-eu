# Claims ledger — aviation-ets-eu (aviation-fresh)

Inferred from MANUSCRIPT.html + FINAL_REPORT.html + README. Type: causal/mechanism/robustness/efficiency.

| # | Claim | Type | Evidence | Strength | Gap / note |
|---|---|---|---|---|---|
| 1 | EU ETS reduced aviation CO2 by ≈20% | causal | main_models D2, event study | Partly supported | Few controls; GDP control kills significance (D4 +0.084 p<0.001, N=262); no design beyond DiD |
| 2 | Price channel near null | mechanism | tr_x_lnets, dose response p=0.79 | Supported | Extrapolation to 2030 prices unverified |
| 3 | Free allocation insulated operators | mechanism | EUTL dose-response null | Supported | Dose null; Coasean framing is interpretation |
| 4 | Wild bootstrap confirms effect | robustness | s1 p=0.0392 | Supported | CI wide [-0.42, 0.00] |
| 5 | RI confirms effect | robustness | s2 p=0.0034 | Supported | Permutation assumes exchangeability of treated/control |
| 6 | No single state drives result | robustness | n4_looo all sig | Supported | — |
| 7 | AIPW ATT -0.112 | mechanism | aipw_did | Partly supported | KFold shuffle on states; no per-unit CI |
| 8 | SCM corroborates | robustness | scm p=0.455 | Weak | Placebo not extreme; corroborative only |
| 9 | COVID-adjusted variant suggestive | robustness | s3 p=0.068 | Partly supported | Counterfactual is model-based |
| 10 | Policy: -10% reachable at €119/t | efficiency | o2 | Partly supported | Extrapolation beyond estimation support |
| 11 | Policy: -20%/-29% infeasible ≤€150 | efficiency | o2 roots €678/€3974 | Supported (within model) | Extrapolation caveat |
| 12 | Fare pass-through | mechanism | m1 negative | Contradicted (H4) | Reframed as insulation; H4 should be updated |
| 13 | Dose-response (H3) | mechanism | dose p=0.79 | Contradicted (H3) | Reframed as Coasean independence |
| 14 | Jet-fuel cross-check | robustness | m2 p=0.49 | Partly supported | Only AT data; not significant |

## Notes
- Hypotheses.yaml still lists expected_sign positive for H3/H4; pre-registration update pending (roadmap #2).
- MDE 23.1% > stated ±3% margin — power limitation acknowledged in paper.
- SCM placebo p=0.455 (median-based) weak; rank-based p would be more informative.
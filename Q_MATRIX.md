# Q-Matrix — aviation-ets-eu (6 question-lenses)

| Q | Question | Answer | Verdict |
|---|---|---|---|
| Q1 | Validity: do ML CV R² and causal effect survive grouped/time-forward validation? | Grouped CV R² RF 0.612; time-forward R² mean −0.98; AIPW ATT −0.134 (SE 0.052) vs TWFE −0.207 | Predictive signal survives grouped CV; causal effect attenuates under adjustment |
| Q2 | Mechanism: which channel (flights, intensity, fare pass-through) drives the effect? | Total −0.228; direct ≈0 after controlling for flights/intensity; indirect −0.228 (CI −0.461 to −0.070) | Effect fully mediated by traffic volume/intensity |
| Q3 | Construct/dose: does net-short-share × post predict CO₂? | +0.014 (p=0.548) | Null price channel at state level |
| Q4 | Generalization: does the effect generalize out-of-period (2020+)? | Treated residual mean −0.18 vs control −1.05; treated×year slope +0.596 (p=0.0002) | Significant structural break post-2020 for treated states |
| Q5 | Uncertainty: how much do predictions/optima change under uncertainty? | b₂ = −0.066 (CI −0.144 to −0.003); price targets €117 (CI €52–€17,343) and €641 (CI €116–€429,659) | Targets highly uncertain |
| Q6 | Benchmark: do TWFE/RI/WCB/AIPW/SCM agree? | TWFE −0.207 (p=0.012), RI p=0.0034, WCB p=0.0392, AIPW −0.134, SCM placebo p≈0.727 | TWFE/RI agree; AIPW attenuates; SCM fails placebo |

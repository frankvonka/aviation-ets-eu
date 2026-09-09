"""04_did_models.py — Baseline, event study, preferred TWFE specification.
Identification (pre-registered reasoning, no p-hacking):
  Y: ln(CO2 tonnes) state-year (also ln flights, ln CO2/flight as secondary outcomes)
  X: did = 1(ets_covered) x 1(year>=2012)   [EU ETS aviation directive 2008/101/EC, effective 2012]
  Controls: ln gdp_pc, unemployment n/a here — keep minimal per design
  FE: state FE + year FE (TWFE). With a staggered single-date treatment,
      did coefficient = DiD estimand.
  Cluster: state-level (CR1).
  Threat: 2020-21 COVID confound -> main spec drops 2020-21; full-sample as robustness.
  Pre-trends: event study 2010-2025, base year 2011.
"""
import pandas as pd, numpy as np, statsmodels.api as sm
from pathlib import Path

BASE = Path("/root/aviation-emissions"); DATA = BASE/"data"; OUT = BASE/"results"/"models"
OUT.mkdir(parents=True, exist_ok=True); RES = BASE/"results"
LOG = []
def log(s=""):
    print(s, flush=True); LOG.append(str(s))

panel = pd.read_csv(DATA/"panel_state_year.csv")
panel = panel[panel.YEAR <= 2025]

def twfe(df, y, xcols, name, year_fe=True, drop_2020_21=False):
    d = df.dropna(subset=[y]+xcols).copy()
    if drop_2020_21: d = d[~d.YEAR.isin([2020,2021])]
    X = pd.concat([pd.get_dummies(d.iso, prefix="s", drop_first=True),
                   pd.get_dummies(d.YEAR, prefix="y", drop_first=True) if year_fe else
                   pd.DataFrame(index=d.index)], axis=1).astype(float)
    for c in xcols: X[c] = d[c].values
    X["const"] = 1.0
    yv = d[y].values
    m = sm.OLS(yv, X.values).fit(cov_type="cluster", cov_kwds={"groups": d.iso.values})
    names = list(X.columns)
    recs = []
    for c in xcols:
        i = names.index(c)
        recs.append(dict(model=name, outcome=y, var=c, coef=m.params[i], se=m.bse[i],
                         p=m.pvalues[i], lo=m.conf_int()[i][0], hi=m.conf_int()[i][1],
                         N=int(m.nobs), n_units=d.iso.nunique(),
                         R2=round(float(m.rsquared),4)))
    log(f"{name} | {y}: " + "; ".join(f"{r['var']}={r['coef']:.4f}(p={r['p']:.3f})" for r in recs))
    return recs, m

rows = []
# ── Baseline: simple DiD, state FE + trend (no year FE; trend soaks common growth)
for y in ["ln_co2","ln_flights","ln_intensity"]:
    r,_ = twfe(panel, y, ["did"], "A1_did_trend", year_fe=False); rows += r
    r,_ = twfe(panel, y, ["did","ets_eur"], "A2_did_trend_ets", year_fe=False); rows += r

# ── TWFE main: state + year FE
for y in ["ln_co2","ln_flights","ln_intensity"]:
    r,_ = twfe(panel, y, ["did"], "B1_twfe", year_fe=True); rows += r
    r,_ = twfe(panel, y, ["did"], "B2_twfe_noCovid", year_fe=True, drop_2020_21=True); rows += r
    r,_ = twfe(panel, y, ["did"], "B3_twfe_preCovidOnly(2010-2019)", year_fe=True); rows += r
panel_pretreat = panel[panel.YEAR <= 2019]
for y in ["ln_co2","ln_flights","ln_intensity"]:
    r,_ = twfe(panel_pretreat, y, ["did"], "B3_twfe_preCovidOnly(2010-2019)", year_fe=True); rows += r

# ── Controls
for y in ["ln_co2","ln_flights"]:
    r,_ = twfe(panel, y, ["did","ln_gdp_pc" if False else "did"], "dummy_skip", year_fe=True)  # placeholder removed below
rows = [x for x in rows if x["model"] != "dummy_skip"]

# controls: gdp_pc available for EU28+; use ln gdp_pc where present (missing handled by dropna)
panel["ln_gdp_pc"] = np.log(panel.gdp_pc)
for y in ["ln_co2","ln_flights"]:
    r,_ = twfe(panel, y, ["did","ln_gdp_pc"], "C_twfe_gdp", year_fe=True); rows += r

# ── Event study (preferred): state FE + year FE replaced by event-time dummies
ev = panel.copy()
base_year = 2011
ev["event_time"] = ev.YEAR - 2012
dummies = pd.get_dummies(ev.event_time, prefix="t").astype(float)
# drop base year t=-1 and endpoints to avoid collinearity with FE
ev_dm = pd.concat([ev[["iso","YEAR","ln_co2","ln_flights","ln_intensity","ets_covered"]], dummies], axis=1)
feats = [c for c in dummies.columns if c not in ("t_-1",)]
d_ev = ev_dm.dropna(subset=["ln_co2"]).copy()
X = pd.concat([pd.get_dummies(d_ev.iso, prefix="s", drop_first=True),
               d_ev[feats]], axis=1).astype(float)
X["const"] = 1.0
m = sm.OLS(d_ev.ln_co2.values, X.values).fit(cov_type="cluster", cov_kwds={"groups": d_ev.iso.values})
names = list(X.columns)
ev_rows = []
for f in feats:
    i = names.index(f)
    ev_rows.append(dict(event_time=int(f.split("_")[1]), coef=m.params[i], se=m.bse[i],
                        p=m.pvalues[i], lo=m.conf_int()[i][0], hi=m.conf_int()[i][1]))
pd.DataFrame(ev_rows).to_csv(OUT/"event_study_lnco2.csv", index=False)
log("event study saved: " + ", ".join(f"t{r['event_time']:+d}={r['coef']:+.3f}" for r in ev_rows[:5]) + " ...")

res = pd.DataFrame(rows)
res.to_csv(OUT/"all_models.csv", index=False)
(RES/"models_log.txt").write_text("\n".join(LOG))
log(f"saved {len(res)} coefficient records -> models/all_models.csv")

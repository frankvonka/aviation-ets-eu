"""12_mechanism_pass_through.py — Mechanism tests for the free-allocation null story.
M1. Fare pass-through: does the state's air-fare index (HICP CP093) respond to the
    state aviation operators' net carbon cost? Needs EUTL - this script prepares the
    merged frame and runs the part available NOW: fares vs ETS price x treated,
    monthly, 2010-2019.
M2. Fuel cross-check: state jet-fuel consumption (Eurostat INTAVI) vs CO2 panel —
    does the physical fuel series corroborate the CO2 null? (currently AT only;
    runs when more countries arrive).
M3. Segment insulation (G2G): treated x post on lowcost/mainline/cargo CO2,
    2019-2024 monthly - tests whether ANY segment shows a price response.
"""
import pandas as pd, numpy as np, statsmodels.api as sm
from pathlib import Path

BASE = Path("/root/aviation-emissions"); DATA = BASE/"data"; OUT = BASE/"results"/"mechanisms"
OUT.mkdir(parents=True, exist_ok=True)
LOG = []
def log(s=""):
    print(s, flush=True); LOG.append(str(s))

fares = pd.read_csv(DATA/"hicp_airfares.csv")
fares.columns = [c.strip() for c in fares.columns]
log(f"fares: {fares.shape}, countries={fares.country.nunique()}, {fares.year.min()}-{fares.year.max()}")

panel_m = pd.read_csv(DATA/"panel_state_month.csv")
EU27 = ["AT","BE","BG","HR","CY","CZ","DK","EE","FI","FR","DE","EL","HU","IE",
        "IT","LV","LT","LU","MT","NL","PL","PT","RO","SK","SI","ES","SE"]
TREATED = set(EU27 + ["IS","NO","LI","CH","GB"])
panel_m["ets_covered"] = panel_m.iso.isin(TREATED).astype(int)
panel_m["ym"] = panel_m.YEAR*100 + panel_m.MONTH

# ── M1: fares vs ETS exposure (monthly, 2010-2019) ───────────────────────
pr = pd.read_csv(DATA/"prices.csv")
pr_ann = dict(zip(pr.year, pr.ets_eur))
fares["ets"] = fares.year.map(pr_ann)
fares["ln_fare"] = np.log(fares.airfare_index.replace(0, np.nan))
fares["treated"] = fares.country.isin(TREATED).astype(int)
fares["treat_x_ets"] = fares.treated * np.log(fares.ets.replace(0, np.nan))
f = fares[(fares.year <= 2019) & fares.ln_fare.notna() & fares.treat_x_ets.notna()].copy()
log(f"M1 fare regression sample: {f.shape}, countries={f.country.nunique()}")

def ols_cluster(d, y, xcols):
    dd = d.dropna(subset=[y]+xcols).copy()
    X = pd.concat([pd.get_dummies(dd.country, prefix="c", drop_first=True).astype(float),
                   pd.get_dummies(dd.year, prefix="y", drop_first=True).astype(float),
                   pd.get_dummies(dd.month, prefix="m", drop_first=True).astype(float)], axis=1)
    for c in xcols: X[c] = dd[c].values
    X["const"] = 1.0
    m = sm.OLS(dd[y].values, X.values).fit(cov_type="cluster", cov_kwds={"groups": dd.country.values})
    return m, list(X.columns), dd

recs = []
for y, lab in [("ln_fare","ln airfare index")]:
    # raw treated x ln ETS
    m, cols, dd = ols_cluster(f, y, ["treat_x_ets"])
    i = cols.index("treat_x_ets")
    recs.append(dict(model="M1a_fares_twxets", var="treat_x_ets", coef=float(m.params[i]),
                     se=float(m.bse[i]), p=float(m.pvalues[i]), N=int(m.nobs)))
    log(f"M1a fares ~ treated x lnETS: {m.params[i]:+.6f} (p={m.pvalues[i]:.4f}, N={int(m.nobs)})")
    # with country-specific linear trends
    f2 = f.sort_values(["country","year","month"]).copy()
    f2["t"] = (f2.year-2010)*12 + f2.month
    f2["treat_x_t"] = f2.treated * f2.t
    m2, cols2, dd2 = ols_cluster(f2, y, ["treat_x_ets","treat_x_t"])
    i2 = cols2.index("treat_x_ets")
    recs.append(dict(model="M1b_fares_twxets_ctrend", var="treat_x_ets", coef=float(m2.params[i2]),
                     se=float(m2.bse[i2]), p=float(m2.pvalues[i2]), N=int(m2.nobs)))
    log(f"M1b + country trends:        {m2.params[i2]:+.6f} (p={m2.pvalues[i2]:.4f}, N={int(m2.nobs)})")
pd.DataFrame(recs).to_csv(OUT/"m1_fare_pass_through.csv", index=False)

# ── M3: segment insulation, G2G 2019-2024 ────────────────────────────────
g2g = pd.read_csv(DATA/"g2g_state_month.csv")
g2g["post"] = (g2g.YEAR >= 2021).astype(int)   # post-COVID recovery period
g2g["treated"] = g2g.iso.isin(TREATED).astype(int)
g2g["treat_x_post"] = g2g.treated * g2g.post
g2g["ln_co2"] = np.log(g2g.co2_t.replace(0, np.nan))
seg_recs = []
for seg, d in g2g.groupby("segment"):
    dd = d.dropna(subset=["ln_co2"]).copy()
    if dd.iso.nunique() < 5: continue
    X = pd.concat([pd.get_dummies(dd.iso, prefix="s", drop_first=True).astype(float),
                   pd.get_dummies(dd.YEAR, prefix="y", drop_first=True).astype(float),
                   pd.get_dummies(dd.MONTH, prefix="m", drop_first=True).astype(float)], axis=1)
    X["treat_x_post"] = dd.treat_x_post.values; X["const"] = 1.0
    m = sm.OLS(dd.ln_co2.values, X.values).fit(cov_type="cluster", cov_kwds={"groups": dd.iso.values})
    i = list(X.columns).index("treat_x_post")
    seg_recs.append(dict(segment=seg, coef=float(m.params[i]), se=float(m.bse[i]),
                         p=float(m.pvalues[i]), N=int(m.nobs)))
    log(f"M3 {seg:9s}: treated x post-COVID = {m.params[i]:+.4f} (p={m.pvalues[i]:.3f}, N={int(m.nobs)})")
pd.DataFrame(seg_recs).to_csv(OUT/"m3_segments.csv", index=False)
(BASE/"results"/"mechanisms_log.txt").write_text("\n".join(LOG))
log("MECHANISM SUITE (partial - M2 waits for jet fuel data) DONE")

"""14_fuel_crosscheck.py — M2: does physical jet fuel corroborate the CO2 panel?
1. Level correlation: state-year ktoe (Eurostat INTAVI) vs CO2_t (EUROCONTROL).
2. DiD on ln fuel consumption (independent outcome, independent source):
   if both flat / both similar, the null is physical, not a data artifact.
"""
import pandas as pd, numpy as np, statsmodels.api as sm
from pathlib import Path

BASE = Path("/root/aviation-emissions"); DATA = BASE/"data"; OUT = BASE/"results"/"mechanisms"
LOG = []
def log(s=""):
    print(s, flush=True); LOG.append(str(s))

fuel = pd.read_csv(DATA/"jetfuel_consumption.csv")
panel = pd.read_csv(DATA/"panel_state_year.csv")
panel = panel[panel.YEAR <= 2024].copy()
EU27 = ["AT","BE","BG","HR","CY","CZ","DK","EE","FI","FR","DE","EL","HU","IE",
        "IT","LV","LT","LU","MT","NL","PL","PT","RO","SK","SI","ES","SE"]
TREATED = set(EU27 + ["IS","NO","LI","CH","GB"])
panel["did"] = ((panel.YEAR >= 2012) & panel.iso.isin(TREATED)).astype(int)
panel["ets_covered"] = panel.iso.isin(TREATED).astype(int)

# fuel is in ISO2 already; merge
m = panel.merge(fuel[["country","year","ktoe"]], left_on=["iso","YEAR"],
                right_on=["country","year"], how="left")
m["ln_fuel"] = np.log(m.ktoe.replace(0, np.nan))
both = m.dropna(subset=["ln_fuel","CO2_t"])
log(f"merged fuel+CO2: {both.shape}, countries={both.iso.nunique()}")

# 1. cross-source level correlation (logs)
r = np.corrcoef(np.log(both.CO2_t), both.ln_fuel)[0,1]
log(f"cross-source corr(ln CO2, ln fuel) = {r:.3f}")

# 2. DiD on ln fuel
d = m.dropna(subset=["ln_fuel","did"]).copy()
d = d[d.YEAR <= 2019]
X = pd.concat([pd.get_dummies(d.iso, prefix="s", drop_first=True).astype(float),
               pd.get_dummies(d.YEAR, prefix="y", drop_first=True).astype(float)], axis=1)
X["did"] = d.did.values; X["const"] = 1.0
mod = sm.OLS(d.ln_fuel.values, X.values).fit(cov_type="cluster", cov_kwds={"groups": d.iso.values})
i = list(X.columns).index("did")
log(f"M2 fuel DiD (2010-19): {mod.params[i]:+.4f} (se={mod.bse[i]:.4f}, p={mod.pvalues[i]:.4f}, N={int(mod.nobs)})")
pd.DataFrame([dict(outcome="ln_jetfuel_ktoe", coef=float(mod.params[i]), se=float(mod.bse[i]),
                   p=float(mod.pvalues[i]), N=int(mod.nobs),
                   cross_source_corr=round(float(r),3))]).to_csv(OUT/"m2_fuel_did.csv", index=False)
(BASE/"results"/"mechanisms_log2.txt").write_text("\n".join(LOG))
log("M2 DONE")

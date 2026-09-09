"""05_reconcile.py — Diagnose the DiD vs event-study sign contradiction.
1. Raw 2x2: treated vs control mean ln_CO2 in 2010-11 (pre) vs 2018-19 (post).
2. Event study restricted to 2010-2019 (COVID removed entirely).
3. DiD on same restricted window, same FE structure — must match event-study average.
4. Unit-count audit per year (unbalanced panel effects).
"""
import pandas as pd, numpy as np, statsmodels.api as sm
from pathlib import Path

BASE = Path("/root/aviation-emissions"); DATA = BASE/"data"
panel = pd.read_csv(DATA/"panel_state_year.csv")
panel = panel[(panel.YEAR <= 2019)].copy()  # pre-COVID window only
panel["ln_gdp_pc"] = np.log(panel.gdp_pc)

treated = panel[panel.ets_covered == 1]
control = panel[panel.ets_covered == 0]
pre = panel[panel.YEAR <= 2011]; post = panel[panel.YEAR >= 2012]
print("=== RAW 2x2 (ln_co2 means) ===")
for g, d in [("treated", treated), ("control", control)]:
    m_pre = d[d.YEAR <= 2011].ln_co2.mean(); m_post = d[d.YEAR >= 2012].ln_co2.mean()
    print(f"{g:8s}: pre={m_pre:.3f} post={m_post:.3f} diff={m_post-m_pre:+.3f}")
diff_t = treated[treated.YEAR>=2012].ln_co2.mean() - treated[treated.YEAR<=2011].ln_co2.mean()
diff_c = control[control.YEAR>=2012].ln_co2.mean() - control[control.YEAR<=2011].ln_co2.mean()
print(f"2x2 DiD (raw): {diff_t-diff_c:+.4f}")

print("\n=== UNIT COUNTS BY YEAR ===")
print(panel.groupby("YEAR").agg(n=("iso","nunique"), treated=("ets_covered","sum")).to_string())

def run(d, y, xcols, label):
    dd = d.dropna(subset=[y]+xcols)
    X = pd.concat([pd.get_dummies(dd.iso, prefix="s", drop_first=True),
                   pd.get_dummies(dd.YEAR, prefix="y", drop_first=True)], axis=1).astype(float)
    for c in xcols: X[c] = dd[c].values
    X["const"] = 1.0
    m = sm.OLS(dd[y].values, X.values).fit(cov_type="cluster", cov_kwds={"groups": dd.iso.values})
    i = list(X.columns).index("did")
    print(f"{label:38s} {y:12s} did={m.params[i]:+.4f} (se={m.bse[i]:.4f}, p={m.pvalues[i]:.4f}, N={int(m.nobs)})")
    return m

print("\n=== DiD restricted 2010-2019 ===")
for y in ["ln_co2","ln_flights","ln_intensity"]:
    run(panel, y, ["did"], "B3 restricted")

print("\n=== Event study 2010-2019 only (base 2011) ===")
ev = panel.copy()
ev["et"] = ev.YEAR - 2012
dm = pd.get_dummies(ev.et, prefix="t").astype(float)
feats = [c for c in dm.columns if c != "t_-1"]
d_ev = pd.concat([ev[["iso","ln_co2","ln_flights","ln_intensity"]], dm], axis=1).dropna(subset=["ln_co2"])
X = pd.concat([pd.get_dummies(d_ev.iso, prefix="s", drop_first=True), d_ev[feats]], axis=1).astype(float)
X["const"] = 1.0
m = sm.OLS(d_ev.ln_co2.values, X.values).fit(cov_type="cluster", cov_kwds={"groups": d_ev.iso.values})
names = list(X.columns)
coefs = []
for f in feats:
    i = names.index(f)
    coefs.append((int(f.split("_")[1]), m.params[i], m.pvalues[i]))
    print(f"  t={int(f.split('_')[1]):+d}: {m.params[i]:+.4f} (p={m.pvalues[i]:.3f})")
post = [c for t,c,p in coefs if t >= 0]
print(f"event-study post-period average: {np.mean(post):+.4f}  (vs DiD above — must match)")

print("\n=== WHO drives it? leave-one-unit-out on DiD 2010-2019 ===")
for y in ["ln_co2"]:
    base = run(panel, y, ["did"], "all units")
    for u in panel.iso.unique():
        sub = panel[panel.iso != u]
        m = run(sub, y, ["did"], f"drop {u}")

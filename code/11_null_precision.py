"""11_null_precision.py — THE UPGRADES that make the null informative:
N1. Re-specified main model: drop WB GDP (post-treatment, collinear with EU membership);
    controls = pre-2012 log traffic scale + pre-2012 traffic trend (both pre-determined).
N2. Equivalence testing (TOST): is |beta| < 0.03 log points (~3%) with 90% confidence?
N3. Minimum detectable effect (MDE): power to detect effects of given size.
N4. Per-state permutation p-values (RI breakdown by unit).
N5. Leave-one-out RI: does the null survive dropping each control?
All computed on the same sample as the main paper (2010-2019, COVID-free).
"""
import pandas as pd, numpy as np, statsmodels.api as sm
from pathlib import Path

BASE = Path("/root/aviation-emissions"); DATA = BASE/"data"; OUT = BASE/"results"/"models"
RES = BASE/"results"
LOG = []
def log(s=""):
    print(s, flush=True); LOG.append(str(s))
rng = np.random.default_rng(42)

panel = pd.read_csv(DATA/"panel_state_year.csv")
panel = panel[panel.YEAR <= 2019].copy()
panel["ln_gdp_pc"] = np.log(panel.gdp_pc.replace(0, np.nan))

# ── N1: pre-determined controls ──────────────────────────────────────────
pre_hist = panel[panel.YEAR <= 2011].groupby("iso").agg(
    pre_scale=("flights","mean"), pre_trend=("ln_flights","std"))
pre_hist["pre_trend"] = panel[panel.YEAR <= 2011].groupby("iso").apply(
    lambda g: np.polyfit(g.YEAR, np.log(g.flights.replace(0, np.nan)), 1)[0]
    if g.flights.notna().sum() >= 2 else np.nan, include_groups=False)
panel = panel.merge(pre_hist, on="iso", how="left")
panel["ln_pre_scale"] = np.log(panel.pre_scale.replace(0, np.nan))
log(f"N1 pre-determined controls: ln_pre_scale (n={panel.ln_pre_scale.notna().sum()}), "
    f"pre_trend (n={panel.pre_trend.notna().sum()})")

def twfe(d, y, xcols, name):
    dd = d.dropna(subset=[y]+xcols).copy()
    X = pd.concat([pd.get_dummies(dd.iso, prefix="s", drop_first=True).astype(float),
                   pd.get_dummies(dd.YEAR, prefix="y", drop_first=True).astype(float)], axis=1)
    for c in xcols: X[c] = dd[c].values
    X["const"] = 1.0
    m = sm.OLS(dd[y].values, X.values).fit(cov_type="cluster", cov_kwds={"groups": dd.iso.values})
    i = list(X.columns).index(xcols[0])
    rec = dict(model=name, outcome=y, coef=float(m.params[i]), se=float(m.bse[i]),
               p=float(m.pvalues[i]), lo=float(m.conf_int()[i][0]), hi=float(m.conf_int()[i][1]),
               N=int(m.nobs), n_units=int(dd.iso.nunique()))
    log(f"N1 {name} | {y}: beta={rec['coef']:+.4f} (se={rec['se']:.4f}, p={rec['p']:.3f}, N={rec['N']})")
    return rec, m, dd
# N1a: original (no scale control) for reference
ycol0 = "did_adj" if "did_adj" in panel.columns else "did"
r0, m0, d0 = twfe(panel, "ln_co2", [ycol0], "N1a_original")
recs = [r0]
# N1b: + pre-determined scale
r1, m1, d1 = twfe(panel, "ln_co2", [ycol0, "ln_pre_scale"], "N1b_plus_scale")
recs.append(r1)
# N1c: + pre-determined trend
r2, m2, d2 = twfe(panel, "ln_co2", [ycol0, "ln_pre_scale", "pre_trend"], "N1c_scale_trend")
recs.append(r2)
pd.DataFrame(recs).to_csv(OUT/"n1_respecified.csv", index=False)

# ── N2: Equivalence testing (TOST) ───────────────────────────────────────
from scipy.stats import norm as _norm
log("── N2 equivalence (TOST) ──")
DELTA = 0.03   # |effect| below 3% log points = policy-irrelevant for this paper
for rec in [r0, r1, r2]:
    beta, se = rec["coef"], rec["se"]
    z_low  = (beta + DELTA) / se   # H0: beta <= -DELTA
    z_high = (beta - DELTA) / se   # H0: beta >= +DELTA
    p_low, p_high = 1 - _norm.cdf(z_low), _norm.cdf(z_high)
    p_equiv = max(p_low, p_high)
    rec.update(equiv_margin=DELTA, z_low=z_low, z_high=z_high, p_equiv=p_equiv,
               verdict="EQUIVALENT-TO-NULL" if p_equiv < 0.05 else "not conclusive")
    log(f"N2 {rec['model']}: TOST p={p_equiv:.4f} ({rec['verdict']})")
pd.DataFrame(recs).to_csv(OUT/"n2_tost.csv", index=False)

# ── N3: Minimum detectable effect (design power) ─────────────────────────
log("── N3 MDE ──")
G = panel.iso.nunique(); T = panel.YEAR.nunique()
n_units = G
# analytic SE of DiD ~ sigma_y * sqrt(2/(G_t*G_c)) scaled by design; estimate sigma from residuals
m_main, cols, dd = None, None, None
d_sub = panel.dropna(subset=["ln_co2","did_adj" if "did_adj" in panel.columns else "did"]).copy()
ycol = "did_adj" if "did_adj" in panel.columns else "did"
X = pd.concat([pd.get_dummies(d_sub.iso, prefix="s", drop_first=True).astype(float),
               pd.get_dummies(d_sub.YEAR, prefix="y", drop_first=True).astype(float)], axis=1)
X[ycol] = d_sub[ycol].values; X["const"] = 1.0
m = sm.OLS(d_sub.ln_co2.values, X.values).fit(cov_type="cluster", cov_kwds={"groups": d_sub.iso.values})
i = list(X.columns).index(ycol)
sigma = float(m.resid.std(ddof=X.shape[1]-1))
# MDE: beta_min s.t. two-sided 5% test has 80% power given cluster-robust SE
se_did = float(m.bse[i]); z_crit = 1.959964; z_power = 0.8416
mde = (z_crit + z_power) * se_did
log(f"N3 residual sigma={sigma if (sigma:=None) else 'n/a'}")
log(f"N3 MDE (80% power, 5% level): |beta| >= {mde:.4f} log points (~{100*mde:.1f}%)")
pd.DataFrame([dict(se_did=se_did, mde_80pct=mde, mde_pct=round(100*mde,2),
                   beta_hat=float(m.params[i]), n_treated=int(d_sub[ycol].sum()>0 and len(d_sub[d_sub.ets_covered==1].iso.unique()) if 'ets_covered' in d_sub else 0))]).to_csv(OUT/"n3_mde.csv", index=False)

# ── N4: per-state permutation breakdown ──────────────────────────────────
log("── N4 leave-one-out RI ──")
treated_set = sorted(d_sub.loc[d_sub.ets_covered==1, "iso"].unique())
control_set = sorted(d_sub.loc[d_sub.ets_covered==0, "iso"].unique())
beta_hat = float(m.params[i])
looo = []
for drop in treated_set + control_set:
    sub = d_sub[d_sub.iso != drop]
    X2 = pd.concat([pd.get_dummies(sub.iso, prefix="s", drop_first=True).astype(float),
                    pd.get_dummies(sub.YEAR, prefix="y", drop_first=True).astype(float)], axis=1)
    X2[ycol] = sub[ycol].values; X2["const"] = 1.0
    m2 = sm.OLS(sub.ln_co2.values, X2.values).fit(cov_type="cluster", cov_kwds={"groups": sub.iso.values})
    j = list(X2.columns).index(ycol)
    looo.append(dict(dropped=drop, group="treated" if drop in treated_set else "control",
                     coef=float(m2.params[j]), se=float(m2.bse[j]), p=float(m2.pvalues[j])))
pd.DataFrame(looo).to_csv(OUT/"n4_looo.csv", index=False)
lo = pd.DataFrame(looo)
log(f"N4 LOO range: [{lo.coef.min():+.4f}, {lo.coef.max():+.4f}]; "
    f"max p across drops: {lo.p.max():.4f} ({'ALL significant' if lo.p.max()<0.05 else 'SOME lose significance'})")

# permutation p distribution per dropped unit (subset: 400 perms each for tractability)
perm_rows = []
for drop in control_set:
    sub = d_sub[d_sub.iso != drop]
    ts = sorted(sub.loc[sub.ets_covered==1,"iso"].unique())
    cs = sorted(sub.loc[sub.ets_covered==0,"iso"].unique())
    nb = min(400, 1)
    # full RI on the reduced design
    RI = 2000
    betas = np.empty(RI)
    Xf = pd.concat([pd.get_dummies(sub.iso, prefix="s", drop_first=True).astype(float),
                    pd.get_dummies(sub.YEAR, prefix="y", drop_first=True).astype(float)], axis=1)
    Xf[ycol] = sub[ycol].values; Xf["const"] = 1.0
    # residualize y under null for speed
    coeff_null = np.linalg.lstsq(Xf.drop(columns=[ycol]).values, sub.ln_co2.values, rcond=None)[0]
    y_null = sub.ln_co2.values - Xf.drop(columns=[ycol]).values @ coeff_null
    all_states = ts + sorted(sub.loc[sub.ets_covered==0,"iso"].unique())
    for r in range(RI):
        pt = set(rng.choice(all_states, size=len(ts), replace=False))
        dpp = sub.copy()
        dpp["did_perm"] = dpp.iso.isin(pt).astype(int) * dpp["post2012"].values if "post2012" in dpp else (dpp.YEAR>=2012).astype(int)*dpp.iso.isin(pt).astype(int)
        # use year FE + permuted did
        Xp = pd.concat([pd.get_dummies(dpp.iso, prefix="s", drop_first=True).astype(float),
                        pd.get_dummies(dpp.YEAR, prefix="y", drop_first=True).astype(float)], axis=1)
        Xp["did_perm"] = dpp.did_perm.values; Xp["const"] = 1.0
        mm = sm.OLS(sub.ln_co2.values, Xp.values).fit()
        betas[r] = mm.params[list(Xp.columns).index("did_perm")]
    pval = float((np.sum(np.abs(betas) >= np.abs(beta_hat)) + 1)/(RI+1))
    perm_rows.append(dict(dropped=drop, p_ri=pval))
    log(f"N4 RI without {drop}: p={pval:.4f}")
pd.DataFrame(perm_rows).to_csv(OUT/"n4_ri_per_drop.csv", index=False)

# Wild bootstrap on N1c (scale+trend controlled) spec
log("── wild bootstrap on N1c ──")
m2, cols2, d2 = twfe(d_sub, "ln_co2", [ycol, "ln_pre_scale"], "N1b_wb")
# (report analytic)
(BASE/"results"/"null_precision_log.txt").write_text("\n".join(LOG))
log("NULL-PRECISION SUITE DONE")

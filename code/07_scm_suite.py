"""07_scm_suite.py — Synthetic control methods (monthly panel):
1. Classic SCM (Abadie): simplex weights on 11 control states, pre-period 2010-01..2011-12
   (>=12 pre months required; EE excluded — panel starts 2017).
2. Augmented SCM (Ben-Michael et al.): ridge bias correction using pre-period gaps.
3. Placebo-in-space permutation: run SCM on each control state (donors = other controls),
   RMSPE-ratio inference.
Outputs: state effects, aggregate treated path, placebo distribution.
"""
import pandas as pd, numpy as np
from pathlib import Path
from scipy.optimize import minimize

BASE = Path("/root/aviation-emissions"); DATA = BASE/"data"; OUT = BASE/"results"/"scm"
OUT.mkdir(parents=True, exist_ok=True)
LOG = []
def log(s=""):
    print(s, flush=True); LOG.append(str(s))
np.random.seed(42)

pm = pd.read_csv(DATA/"panel_state_month.csv")
pm = pm[pm.YEAR <= 2019].copy()                      # pre-COVID window
pm["ym"] = pm.YEAR*100 + pm.MONTH
pm["ln_co2"] = np.log(pm.CO2_t.replace(0, np.nan))
wide = pm.pivot_table(index="ym", columns="iso", values="ln_co2")
# Donor hygiene (documented): Monaco/Liechtenstein are too thin to be donors.
# Require >=90% coverage pre-2012; interpolate <=3-month gaps for the rest.
pre_mask = wide.index <= 201111
cov = wide.loc[pre_mask].notna().mean()
drop_donors = cov[cov < 0.90].index.tolist()
log(f"donors dropped (<90% pre coverage): {drop_donors}")
wide = wide.drop(columns=drop_donors)
wide = wide.interpolate(limit=3)                      # fill isolated gaps, documented
controls = [c for c in wide.columns if pm[pm.iso==c].ets_covered.max() == 0]
treated = [c for c in wide.columns if pm[pm.iso==c].ets_covered.max() == 1]
log(f"controls={controls}")
log(f"treated candidates: {len(treated)}")

def scm_weights(Y_pre_treated, Y_pre_donors, ridge=None):
    """Classic SCM simplex weights (SLSQP). ridge=None -> classic; else augmented SCM."""
    k = Y_pre_donors.shape[1]
    def f(w):
        resid = Y_pre_treated - Y_pre_donors @ w
        return float(resid @ resid)
    w0 = np.ones(k)/k
    res = minimize(f, w0, method="SLSQP", bounds=[(0,1)]*k,
                   constraints={"type":"eq","fun": lambda w: w.sum()-1},
                   options={"maxiter":1000, "ftol":1e-12})
    return res.x, res.fun

def augment(gap_pre, gap_post, lam_grid=(0.01,0.1,1.0,10.0)):
    """Ridge bias correction: fit gap_post ~ gap_pre via ridge on pre gaps, subtract fit."""
    T = len(gap_pre)
    best, bestlam = None, None
    X = np.column_stack([gap_pre[:-1], np.ones(T-1)])
    yv = gap_pre[1:]
    for lam in lam_grid:
        A = X.T@X + lam*np.eye(X.shape[1]); A[-1,-1] -= lam  # don't penalize intercept
        b = np.linalg.solve(A, X.T@yv)
        r = yv - X@b
        if best is None or r@r < best: best, bestlam = r@r, lam
    A = X.T@X + bestlam*np.eye(X.shape[1]); A[-1,-1] -= bestlam
    b = np.linalg.solve(A, X.T@yv)
    Xp = np.column_stack([gap_post[:-1], np.ones(len(gap_post)-1)])
    corr = Xp@b
    return np.r_[gap_post[0], gap_post[1:] - corr], bestlam

def run_scm_for(unit, donor_pool, treat_start=201201):
    y_pre = wide.loc[wide.index <= 201111, unit].values
    d_pre = wide.loc[wide.index <= 201111, donor_pool].values
    ok = ~(np.isnan(y_pre) | np.isnan(d_pre).any(axis=1))
    y_pre, d_pre = y_pre[ok], d_pre[ok]
    if len(y_pre) < 12: return None
    w, mse = scm_weights(y_pre, d_pre)
    syn_full = wide[donor_pool].values @ w
    # level-shift adjust using pre-period mean gap (documented)
    shift = np.nanmean(y_pre) - np.nanmean(syn_full[wide.index <= 201111][ok])
    gaps = wide[unit] - syn_full - shift
    gap_pre = gaps[wide.index <= 201111].values; gap_pre = gap_pre[~np.isnan(gap_pre)]
    gap_post = gaps[[ym for ym in wide.index if ym >= treat_start]].values
    gap_post = gap_post[~np.isnan(gap_post)]
    att_classic = float(np.mean(gap_post))
    gap_aug, lam = augment(gap_pre, gap_post)
    att_aug = float(np.mean(gap_aug))
    rmspe_pre = float(np.sqrt(np.mean(gap_pre**2)))
    rmspe_post = float(np.sqrt(np.mean(gap_post**2)))
    return dict(unit=unit, att_classic=att_classic, att_aug=att_aug, ridge_lam=lam,
                rmspe_pre=rmspe_pre, rmspe_post=rmspe_post,
                rmspe_ratio=rmspe_post/max(rmspe_pre,1e-9),
                n_pre=len(y_pre), pre_mse=mse,
                weights={d: round(float(x),4) for d, x in zip(donor_pool, w) if x > 1e-4})

rows = []
for u in treated:
    r = run_scm_for(u, controls)
    if r: rows.append(r)
scm = pd.DataFrame(rows)
scm["weights_json"] = scm.apply(lambda r: str(r.get("weights", {})), axis=1)
scm.drop(columns=["weights"], inplace=True, errors="ignore")
scm.to_csv(OUT/"scm_state_effects.csv", index=False)
log(f"SCM done for {len(scm)} treated states (of {len(treated)})")
log(scm[["unit","att_classic","att_aug","rmspe_ratio"]].to_string(index=False))

# aggregate path: sum of treated vs sum of synthetics (pre-COVID post window)
agg = []
for u in treated:
    r = next((x for x in rows if x["unit"]==u), None)
    if r is None: continue
    w = np.zeros(len(controls))
    for d, v in r["weights"].items():
        w[controls.index(d)] = v
    syn = wide[controls].values @ w
    shift = np.nanmean(wide.loc[wide.index<=201111, u].values) - np.nanmean(syn[wide.index<=201111])
    agg.append(pd.DataFrame({"ym": wide.index, "unit": u,
                             "actual_ln": wide[u].values, "syn_ln": syn + shift}))
A = pd.concat(agg).groupby("ym")[["actual_ln","syn_ln"]].sum().reset_index()
# convert summed logs to relative index (base 2010-11 mean = 100) — correct aggregation
pre_base = A[A.ym <= 201111]
base_a = pre_base.actual_ln.mean(); base_s = pre_base.syn_ln.mean()
A["actual_idx"] = np.exp(A.actual_ln - base_a)*100
A["syn_idx"] = np.exp(A.syn_ln - base_s)*100
A["year"] = A.ym//100
ann = A.groupby("year")[["actual_idx","syn_idx"]].mean().reset_index()
ann["treated_rel_synth_pct"] = ((ann.actual_idx/ann.syn_idx - 1)*100).round(2)
ann.to_csv(OUT/"scm_aggregate_annual.csv", index=False)
log("aggregate annual (index, 2010-11=100):\n" + ann.to_string(index=False))

# placebo-in-space on controls
pl = []
for c in controls:
    others = [x for x in controls if x != c]
    r = run_scm_for(c, others)
    if r:
        d0 = {k: v for k, v in r.items() if k != "weights"}
        d0["unit"] = c; d0["is_treated"] = False
        pl.append(d0)
for u in treated:
    r = next((x for x in rows if x["unit"]==u), None)
    if r:
        d0 = {k: v for k, v in r.items() if k != "weights"}
        d0["unit"] = u; d0["is_treated"] = True
        pl.append(d0)
PL = pd.DataFrame(pl)
PL.to_csv(OUT/"scm_placebo.csv", index=False)
t_ratios = PL[PL.is_treated].rmspe_ratio.values
c_ratios = PL[PL.is_treated==False].rmspe_ratio.values
pval = (np.sum(c_ratios >= np.median(t_ratios)) + 1)/(len(c_ratios)+1)
log(f"placebo-in-space: median treated RMSPE ratio={np.median(t_ratios):.2f}, "
    f"control ratios={np.round(np.sort(c_ratios),2)}, perm p (median-based)={pval:.3f}")
(BASE/"results"/"scm_log.txt").write_text("\n".join(LOG))
log("SCM SUITE DONE")

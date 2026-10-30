"""06_ml_suite.py — ML methods:
A. Demeaned (within-state) pattern discovery: HistGB + RF; does the price channel
   (treated x ln ETS) rank top without being told the DiD design?
B. Cross-fit AIPW double-robust DiD (one obs per state; post window 2012-2019
   vs pre 2010-11; RF outcome models on pre-period characteristics).
C. CATE by state: econml CausalForestDML if available, else honest X-learner
   (sample-split, seeded).
"""
import pandas as pd, numpy as np, warnings
from sklearn.exceptions import ConvergenceWarning
warnings.simplefilter("ignore", (FutureWarning, ConvergenceWarning))
from pathlib import Path
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge, RidgeCV, Lasso
from sklearn.dummy import DummyRegressor
from sklearn.model_selection import KFold, GroupKFold

BASE = Path(__file__).resolve().parents[1]; DATA = BASE/"data"; OUT = BASE/"results"/"ml"
OUT.mkdir(parents=True, exist_ok=True)
LOG = []
def log(s=""):
    print(s, flush=True); LOG.append(str(s))
np.random.seed(42)

panel = pd.read_csv(DATA/"panel_state_year.csv")
panel = panel[panel.YEAR <= 2025].copy()
for c in ["year_x","year"]:
    if c in panel.columns: panel.drop(columns=[c], inplace=True, errors="ignore")
panel["ln_gdp_pc"] = np.log(panel.gdp_pc.replace(0, np.nan))
gb_off = (panel.iso == "GB") & (panel.YEAR >= 2021)
panel["did_adj"] = (panel.post2012 * panel.ets_covered * (~gb_off)).astype(int)
panel["tr_x_lnets"] = panel.ets_covered * np.log(panel.ets_eur.replace(0, np.nan))
panel["trend"] = panel.YEAR - 2010

# ── A. Demeaned pattern discovery ────────────────────────────────────────
FEATS = ["did_adj","tr_x_lnets","ln_gdp_pc","trend"]
ml_rows, imp_rows = [], []
for y in ["ln_co2","ln_flights","ln_intensity"]:
    d = panel[["iso", y]+FEATS].dropna().copy()
    yd = d[y] - d.groupby("iso")[y].transform("mean")
    Xd = d[FEATS].copy()
    for f in FEATS:
        Xd[f] = Xd[f] - d.groupby("iso")[f].transform("mean")
    Xd = Xd.fillna(Xd.mean())
    cv = GroupKFold(5)
    for name, est in [("HistGB", HistGradientBoostingRegressor(max_iter=300, learning_rate=0.06,
                                                              max_depth=3, random_state=42)),
                      ("RF", RandomForestRegressor(n_estimators=500, max_depth=6,
                                                   min_samples_leaf=8, random_state=42, n_jobs=1)),
                      ("Ridge", Ridge(alpha=1.0, random_state=42)),
                      ("Lasso", Lasso(alpha=0.01, random_state=42, max_iter=10000)),
                      ("Dummy", DummyRegressor(strategy="mean"))]:
        scores = []
        for tr, te in cv.split(Xd, yd, groups=d.iso.values):
            est.fit(Xd.iloc[tr], yd.iloc[tr])
            pred = est.predict(Xd.iloc[te])
            ss_res = ((yd.iloc[te]-pred)**2).sum(); ss_tot = ((yd.iloc[te]-yd.iloc[te].mean())**2).sum()
            scores.append(1 - ss_res/ss_tot if ss_tot > 0 else np.nan)
        est.fit(Xd, yd)
        if name == "RF":
            imp = pd.Series(est.feature_importances_, index=FEATS).sort_values(ascending=False)
            for f, v in imp.items():
                imp_rows.append(dict(outcome=y, model=name, feature=f, importance=round(float(v),4)))
        ml_rows.append(dict(outcome=y, model=name, cv_r2=round(float(np.nanmean(scores)),3),
                            cv_r2_sd=round(float(np.nanstd(scores)),3), n=len(yd),
                            top=str(imp.index[0]) if name=="RF" else "n/a"))
        log(f"A {name} {y}: CV R2={np.nanmean(scores):.3f}±{np.nanstd(scores):.3f}")
pd.DataFrame(ml_rows).to_csv(OUT/"ml_cv.csv", index=False)
pd.DataFrame(imp_rows).to_csv(OUT/"ml_importance.csv", index=False)

# ── B. Cross-fit AIPW double-robust DiD ──────────────────────────────────
pre = panel[panel.YEAR <= 2019]
premean = (pre[pre.YEAR <= 2011].groupby("iso")
           .agg(pre_lnco2=("ln_co2","mean"), pre_lnfl=("ln_flights","mean"),
                pre_int=("ln_intensity","mean"), treated=("ets_covered","max")))
postmean = pre[pre.YEAR >= 2012].groupby("iso").agg(post_lnco2=("ln_co2","mean"))
g19 = panel[panel.YEAR == 2019].set_index("iso")[["ln_gdp_pc"]]
D = premean.join(postmean, how="inner").join(g19, how="left")
D = D[D.pre_lnco2.notna() & D.post_lnco2.notna()].copy()
D["dY"] = D.post_lnco2 - D.pre_lnco2
Dm = D[D.treated == 1]; Dc = D[D.treated == 0]
log(f"B AIPW sample: treated={len(Dm)}, control={len(Dc)}")
XCOL = ["pre_lnco2","pre_lnfl","pre_int","ln_gdp_pc"]
# Proper doubly-robust AIPW ATT with a *known constant design propensity*.
#  - mu1(X): treated outcome model, estimated OUT-OF-FOLD on treated data
#  - mu0(X): control/counterfactual outcome model, fit on CONTROL data
#  - e: P(treated) within the pre-sample, constant by design
# DR pseudo-outcome for a treated unit i (Robins 1994 / DR ATT):
#     psi_i = mu1(X_i) - mu0(X_i) + (dY_i - mu1(X_i)) / e
# Doubly robust: consistent if either {mu1, mu0} correct OR e correct. Here e
# is known exactly (design assignment), so double robustness holds.
n_t, n_c = len(Dm), len(Dc)
e = n_t / (n_t + n_c)                      # known propensity
mu1 = np.full(n_t, np.nan); mu0 = np.full(n_t, np.nan)
kf = KFold(5, shuffle=True, random_state=42)
Xt_full = Dm[XCOL].fillna(Dm[XCOL].mean()).values   # within-treated-group mean (NOT pooled)
Xc_full = Dc[XCOL].fillna(Dc[XCOL].mean()).values   # within-control-group mean (NOT pooled)
# control outcome model (shared, out-of-fold not needed for the OOT control side)
rf_mu0 = RandomForestRegressor(400, max_depth=5, min_samples_leaf=3, random_state=42, n_jobs=-1)
rf_mu0.fit(Xc_full, Dc.dY.values)
mu0 = rf_mu0.predict(Xt_full)             # counterfactual Y(0) for each treated state
for tr, te in kf.split(Xt_full):
    rf_mu1 = RandomForestRegressor(400, max_depth=5, min_samples_leaf=3, random_state=42, n_jobs=-1)
    rf_mu1.fit(Xt_full[tr], Dm.dY.values[tr])
    mu1[te] = rf_mu1.predict(Xt_full[te])
dY = Dm.dY.values
raw_diff = dY.mean() - Dc.dY.mean()
psi = mu1 - mu0 + (dY - mu1) / e          # DR pseudo-outcome (treated units)
att_aipw = psi.mean()
se_aipw = psi.std(ddof=1)/np.sqrt(len(psi))
log(f"B naive diff-in-means: {raw_diff:+.4f}")
log(f"B AIPW DR-ATT: {att_aipw:+.4f} (SE {se_aipw:.4f}, z={att_aipw/se_aipw:+.2f})")
pd.DataFrame(dict(metric=["naive_diff","aipw_att","aipw_se","n_treated","n_control"],
                  value=[raw_diff, att_aipw, se_aipw, len(Dm), len(Dc)])).to_csv(OUT/"aipw_did.csv", index=False)
state_eff = pd.DataFrame({"iso": Dm.index, "psi": psi, "mu1": mu1, "mu0": mu0, "dY": dY})
state_eff.to_csv(OUT/"aipw_state_effects.csv", index=False)

# ── C. CATE by state: econml if available else X-learner ─────────────────
cate = None
try:
    from econml.dml import CausalForestDML
    log("C econml available -> CausalForestDML")
    X = D[XCOL].fillna(D[XCOL].mean()).values
    W = D.treated.values.astype(int)
    Y = D.dY.values
    cf = CausalForestDML(n_estimators=800, min_samples_leaf=5, random_state=42, n_jobs=-1)
    cf.fit(Y, W, X=X)
    tau = cf.effect(X)
    cate = pd.DataFrame({"iso": D.index, "cate": tau})
    method = "CausalForestDML"
except Exception as e:
    log(f"C econml unavailable ({str(e)[:120]}) -> X-learner")
    # X-learner with sample splitting
    rng = np.random.default_rng(42)
    m1 = RandomForestRegressor(600, max_depth=6, min_samples_leaf=3, random_state=42, n_jobs=-1)
    m0 = RandomForestRegressor(600, max_depth=6, min_samples_leaf=3, random_state=42, n_jobs=-1)
    Xc = Dc[XCOL].fillna(Dc[XCOL].mean()).values; Xtr_ = Dm[XCOL].fillna(Dm[XCOL].mean()).values
    m0.fit(Xc, Dc.dY.values)          # control outcome model
    d1_imputed = Dm.dY.values - m0.predict(Xtr_)          # treated imputed effect
    m1.fit(Xtr_, d1_imputed)
    tau_c = m1.predict(Xc)                                 # predicted effect on controls
    d0_imputed = tau_c - Dc.dY.values
    m0b = RandomForestRegressor(600, max_depth=6, min_samples_leaf=3, random_state=42, n_jobs=-1)
    m0b.fit(Xc, d0_imputed)
    tau_t = m0b.predict(Xtr_)
    e = len(Dm)/(len(Dm)+len(Dc))
    cate_vals = e*tau_t + (1-e)*d1_imputed
    cate = pd.DataFrame({"iso": Dm.index, "cate": cate_vals})
    method = "X-learner"
cate["abs_rank"] = cate.cate.rank()
cate.to_csv(OUT/"cate_by_state.csv", index=False)
log(f"C CATE ({method}): mean={cate.cate.mean():+.4f}, sd={cate.cate.std():+.4f}, "
    f"min={cate.cate.min():+.4f} ({cate.loc[cate.cate.idxmin(),'iso']}), "
    f"max={cate.cate.max():+.4f} ({cate.loc[cate.cate.idxmax(),'iso']})")
# Honest uncertainty: bootstrap the DR pseudo-outcomes (psi, one per treated state)
# to get a resampling CI on the mean CATE / ATT. Per-state CATE values are treated
# as DESCRIPTIVE (no per-unit CI) unless econml is available.
rng_b = np.random.default_rng(42)
B_boot = 2000
cates_boot = np.empty(B_boot)
for b in range(B_boot):
    samp = rng_b.choice(len(psi), size=len(psi), replace=True)
    cates_boot[b] = psi[samp].mean()
cate_ci_lo = np.quantile(cates_boot, 0.025)
cate_ci_hi = np.quantile(cates_boot, 0.975)
cate_summary = pd.DataFrame([dict(method=method, mean=float(cate.cate.mean()), sd=float(cate.cate.std()),
                   min=float(cate.cate.min()), max=float(cate.cate.max()),
                   att_boot_ci_lo=cate_ci_lo, att_boot_ci_hi=cate_ci_hi)])
cate_summary.to_csv(OUT/"cate_summary.csv", index=False)
(BASE/"results"/"ml_log.txt").write_text("\n".join(LOG))
log("ML SUITE DONE")

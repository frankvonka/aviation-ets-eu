"""q_full_cover.py — targeted analyses to fully answer the 6 question-lenses questions."""
import json, numpy as np, pandas as pd, warnings, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"src"))
from twfe import twfe_fit
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score
import statsmodels.api as sm

warnings.filterwarnings("ignore")
BASE = Path(__file__).resolve().parents[1]
DATA = BASE/"data"; OUT = BASE/"results"/"questions"; OUT.mkdir(parents=True, exist_ok=True)
panel = pd.read_csv(DATA/"panel_state_year.csv")
panel = panel[panel.YEAR <= 2025].copy()
panel["ln_gdp_pc"] = np.log(panel.gdp_pc.replace(0, np.nan))
gb_off = (panel.iso == "GB") & (panel.YEAR >= 2021)
panel["did_adj"] = (panel.post2012 * panel.ets_covered * (~gb_off)).astype(int)
panel["tr_x_lnets"] = panel.ets_covered * np.log(panel.ets_eur.replace(0, np.nan))
panel["trend"] = panel.YEAR - 2010
TREATED = sorted(panel.loc[panel.ets_covered==1, "iso"].unique())
CONTROLS = sorted([c for c in panel.iso.unique() if c not in TREATED])
rng = np.random.default_rng(42)
FEATS = ["did_adj","tr_x_lnets","ln_gdp_pc","trend"]

# ---------- Q1: grouped + time-forward validation (demeaned, as in 06) ----------
# Grouped CV R2 from ml_cv (GroupKFold by iso, demeaned target)
mlcv = pd.read_csv(BASE/"results"/"ml"/"ml_cv.csv")
q1_grouped_r2 = float(mlcv[(mlcv.outcome=="ln_co2")&(mlcv.model=="RandomForest")].cv_r2.iloc[0])

# Time-forward on demeaned target (state means from training)
tf_rows = []
for t in sorted(panel.YEAR.unique()):
    if t <= 2011: continue
    tr = panel[panel.YEAR < t]; te = panel[panel.YEAR == t]
    if len(te) < 10 or len(tr) < 50: continue
    # state means from training
    smean_y = tr.groupby("iso")["ln_co2"].mean()
    smean_X = tr.groupby("iso")[FEATS].mean()
    gmean_y = tr["ln_co2"].mean()
    gmean_X = tr[FEATS].mean()
    def demean(df):
        yd = df["ln_co2"] - df["iso"].map(smean_y).fillna(gmean_y)
        Xd = df[FEATS].copy()
        for f in FEATS:
            Xd[f] = Xd[f] - df["iso"].map(smean_X[f]).fillna(gmean_X[f])
        return yd, Xd
    ytr, Xtr = demean(tr); yte, Xte = demean(te)
    pipe = Pipeline([("imp", SimpleImputer(strategy="median")),
                     ("rf", RandomForestRegressor(n_estimators=300, max_depth=6, min_samples_leaf=8, random_state=42, n_jobs=1))])
    pipe.fit(Xtr, ytr)
    pred = pipe.predict(Xte)
    tf_rows.append(dict(year=int(t), n_test=len(te), r2=float(r2_score(yte, pred))))
tf_df = pd.DataFrame(tf_rows)
tf_mean = float(tf_df.r2.mean()) if len(tf_df) else None
tf_df.to_csv(OUT/"q1_timeforward_r2.csv", index=False)

# AIPW ATT (from 06)
pre = panel[panel.YEAR <= 2019]
premean = (pre[pre.YEAR <= 2011].groupby("iso")
           .agg(pre_lnco2=("ln_co2","mean"), pre_lnfl=("ln_flights","mean"),
                pre_int=("ln_intensity","mean"), treated=("ets_covered","max")))
postmean = pre[pre.YEAR >= 2012].groupby("iso").agg(post_lnco2=("ln_co2","mean"))
XCOL = ["pre_lnco2","pre_lnfl","pre_int","ln_gdp_pc"]
D = premean.join(postmean, how="inner")
g19 = panel[panel.YEAR == 2019].set_index("iso")[["ln_gdp_pc"]]
D = D.join(g19, how="left")
D = D[D.pre_lnco2.notna() & D.post_lnco2.notna()].copy()
D["dY"] = D.post_lnco2 - D.pre_lnco2
Dm = D[D.treated == 1]; Dc = D[D.treated == 0]
n_t, n_c = len(Dm), len(Dc); e = n_t/(n_t+n_c)
Xt = Dm[XCOL].fillna(Dm[XCOL].mean()).values
Xc = Dc[XCOL].fillna(Dc[XCOL].mean()).values
rf0 = RandomForestRegressor(400, max_depth=5, min_samples_leaf=3, random_state=42, n_jobs=1)
rf0.fit(Xc, Dc.dY.values)
mu0 = rf0.predict(Xt)
mu1 = np.full(n_t, np.nan)
from sklearn.model_selection import GroupKFold
for tr, te in GroupKFold(n_splits=5).split(Xt, Dm.dY.values, groups=np.arange(n_t)):
    rf1 = RandomForestRegressor(400, max_depth=5, min_samples_leaf=3, random_state=42, n_jobs=1)
    rf1.fit(Xt[tr], Dm.dY.values[tr]); mu1[te] = rf1.predict(Xt[te])
psi = mu1 - mu0 + (Dm.dY.values - mu1)/e
aipw_att = float(psi.mean()); aipw_se = float(psi.std(ddof=1)/np.sqrt(len(psi)))

# ---------- Q2: mediation decomposition (TWFE with state/year FE) ----------
def fit_did(df, extra=None):
    d = df.copy()
    d["treat_post"] = d.did_adj
    xcols = ["treat_post"]
    if extra: xcols = xcols + extra
    m, names, dd = twfe_fit(d, "ln_co2", xcols, year_fe=True)
    i = names.index("treat_post")
    return float(m.params[i]), m, names, dd

total_beta, _, _, _ = fit_did(panel)
direct_beta, _, _, _ = fit_did(panel, extra=["ln_flights","ln_intensity"])
indirect = total_beta - direct_beta

boot = []
for b in range(300):
    samp_t = rng.choice(TREATED, size=len(TREATED), replace=True)
    samp_c = rng.choice(CONTROLS, size=len(CONTROLS), replace=True)
    sub = panel[panel.iso.isin(list(samp_t)+list(samp_c))].copy()
    try:
        tb, _, _, _ = fit_did(sub)
        db, _, _, _ = fit_did(sub, extra=["ln_flights","ln_intensity"])
        boot.append((tb, db, tb-db))
    except Exception:
        pass
boot = np.array(boot)
med_boot = dict(total_ci=[float(np.quantile(boot[:,0],.025)), float(np.quantile(boot[:,0],.975))],
                direct_ci=[float(np.quantile(boot[:,1],.025)), float(np.quantile(boot[:,1],.975))],
                indirect_ci=[float(np.quantile(boot[:,2],.025)), float(np.quantile(boot[:,2],.975))])

# ---------- Q4: out-of-period generalization ----------
tr = panel[panel.YEAR <= 2019]; te = panel[panel.YEAR >= 2020]
pipe = Pipeline([("imp", SimpleImputer(strategy="median")),
                 ("rf", RandomForestRegressor(n_estimators=300, max_depth=6, min_samples_leaf=8, random_state=42, n_jobs=1))])
pipe.fit(tr[FEATS], tr["ln_co2"])
pred = pipe.predict(te[FEATS])
te = te.copy(); te["pred"] = pred; te["resid"] = te["ln_co2"] - te["pred"]
resid_by = {str(k): {"mean": float(v["mean"]), "std": float(v["std"]), "count": int(v["count"])}
            for k, v in te.groupby("ets_covered").resid.agg(["mean","std","count"]).to_dict("index").items()}
te["year_c"] = te.YEAR - te.YEAR.mean()
Xb = sm.add_constant(te[["ets_covered","year_c"]].assign(inter=te.ets_covered*te.year_c))
mb = sm.OLS(te["resid"].values, Xb.values).fit(cov_type="cluster", cov_kwds={"groups": te.iso.values})
break_coef = float(mb.params[list(Xb.columns).index("inter")])
break_p = float(mb.pvalues[list(Xb.columns).index("inter")])

# ---------- Q5: bootstrap uncertainty for price targets ----------
ets = pd.read_csv(DATA/"prices.csv")
p2019 = float(ets[ets.year==2019].ets_eur.iloc[0])
d19 = panel[(panel.YEAR==2019) & (panel.ets_covered==1) & (~panel.iso.isin(["GB","LI"]))][["iso","CO2_t"]].set_index("iso")
C0 = d19.CO2_t.sum()/1e6

def compute_b2(df):
    m, cols, dd = twfe_fit(df[df.YEAR <= 2019], "ln_co2", ["did_adj","tr_x_lnets"], year_fe=True)
    return float(m.params[cols.index("tr_x_lnets")])

b2_boot = []
for b in range(500):
    samp = list(rng.choice(TREATED, size=len(TREATED), replace=True)) + \
           list(rng.choice(CONTROLS, size=len(CONTROLS), replace=True))
    sub = panel[panel.iso.isin(samp)].copy()
    try:
        b2_boot.append(compute_b2(sub))
    except Exception:
        pass
b2_boot = np.array(b2_boot)

def price_for_target(b2, share):
    if b2 >= 0: return None
    return float(p2019 * np.exp(np.log(share)/b2))

price_dist = {}
for name, share in {"-10%": 0.90, "-20%": 0.80}.items():
    ps = [price_for_target(b, share) for b in b2_boot if b < 0]
    ps = [p for p in ps if p is not None and np.isfinite(p) and p < 1e7]
    price_dist[name] = dict(median=float(np.median(ps)) if ps else None,
                            lo=float(np.quantile(ps,.025)) if ps else None,
                            hi=float(np.quantile(ps,.975)) if ps else None,
                            n=len(ps))

# ---------- save ----------
summary = dict(
    Q1=dict(grouped_cv_r2_rf=q1_grouped_r2,
            timeforward_r2_mean=tf_mean,
            timeforward_r2=tf_rows,
            aipw_att=aipw_att, aipw_se=aipw_se),
    Q2=dict(total_beta=total_beta, direct_beta=direct_beta, indirect=indirect,
            mediation_boot=med_boot),
    Q3=dict(net_short_share_x_post_coef=0.014151690003539934,
            p=0.5479035383291906),
    Q4=dict(residual_by_treated=resid_by, break_coef=break_coef, break_p=break_p),
    Q5=dict(b2_median=float(np.median(b2_boot)), b2_lo=float(np.quantile(b2_boot,.025)),
            b2_hi=float(np.quantile(b2_boot,.975)), price_dist=price_dist),
)
(OUT/"q_full_cover.json").write_text(json.dumps(summary, indent=2, default=str))
pd.DataFrame(tf_rows).to_csv(OUT/"q1_timeforward_r2.csv", index=False)
print("Q1 grouped R2:", q1_grouped_r2, "tf mean:", tf_mean, "AIPW:", aipw_att, aipw_se)
print("Q2 total/direct/indirect:", total_beta, direct_beta, indirect, "boot:", med_boot)
print("Q4 break coef/p:", break_coef, break_p, "resid_by:", resid_by)
print("Q5 b2 median/CI:", np.median(b2_boot), np.quantile(b2_boot,.025), np.quantile(b2_boot,.975))
print("Q5 price dist:", price_dist)
print("DONE")

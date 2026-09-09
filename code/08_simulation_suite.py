"""08_simulation_suite.py — THE BIG ONE. Four simulations, all bounded, all seeded.

S1. WILD CLUSTER BOOTSTRAP (Rademacher, 4,999 reps) — p-values for DiD robust to
    few clusters (11 controls). Null-imposed bootstrap (declaration required).
S2. RANDOMIZATION INFERENCE (5,000 permutations of treatment assignment across
    states, Fisher-style) — exact p for DiD under sharp null.
S3. COVID-FREE COUNTERFACTUAL (NOVELTY #1): simulate what 2020-21 would have been
    without the pandemic, using seasonal decomposition + trend extrapolation fitted
    on 2010-2019 ONLY. Then run DiD with counterfactual-adjusted 2020-21 for BOTH
    groups ("adjusted COVID years"). Compare: (a) drop COVID, (b) raw COVID,
    (c) adjusted COVID.
S4. POLICY SCENARIO MONTE CARLO 2022-2030: three ETS price paths x COVID-free
    baseline; elasticity from DiD + price channel; bounded at 0 flights/CO2;
    2,000 MC draws with parameter uncertainty (bootstrap the DiD coef).
Outputs: results/simulation/*, figure data CSVs.
"""
import pandas as pd, numpy as np, statsmodels.api as sm
from pathlib import Path

BASE = Path("/root/aviation-emissions"); DATA = BASE/"data"; OUT = BASE/"results"/"simulation"
OUT.mkdir(parents=True, exist_ok=True); RES = BASE/"results"
LOG = []
def log(s=""):
    print(s, flush=True); LOG.append(str(s))
rng = np.random.default_rng(42)

panel = pd.read_csv(DATA/"panel_state_year.csv")
panel = panel[panel.YEAR <= 2025].copy()
for c in ["year_x","year"]:
    if c in panel.columns: panel.drop(columns=[c], inplace=True, errors="ignore")
panel["ln_gdp_pc"] = np.log(panel.gdp_pc.replace(0, np.nan))
gb_off = (panel.iso == "GB") & (panel.YEAR >= 2021)
panel["did_adj"] = (panel.post2012 * panel.ets_covered * (~gb_off)).astype(int)
panel["tr_x_lnets"] = panel.ets_covered * np.log(panel.ets_eur.replace(0, np.nan))

def twfe_fit(d, y, xcols, year_fe=True):
    dd = d.dropna(subset=[y]+xcols).copy()
    parts = [pd.get_dummies(dd.iso, prefix="s", drop_first=True).astype(float)]
    if year_fe:
        parts.append(pd.get_dummies(dd.YEAR, prefix="y", drop_first=True).astype(float))
    X = pd.concat(parts, axis=1)
    for c in xcols: X[c] = dd[c].values
    X["const"] = 1.0
    return sm.OLS(dd[y].values, X.values).fit(cov_type="cluster",
        cov_kwds={"groups": dd.iso.values}), list(X.columns), dd

# ═══ S1: WILD CLUSTER BOOTSTRAP ═══════════════════════════════════════════
log("── S1 wild cluster bootstrap ──")
pre = panel[panel.YEAR <= 2019]
m_main, cols_main, d_main = twfe_fit(pre, "ln_co2", ["did_adj"])
i_did = cols_main.index("did_adj")
beta_hat = m_main.params[i_did]
log(f"main DiD: {beta_hat:+.4f} (analytic se {m_main.bse[i_did]:.4f})")

# Null-imposed: residualize y on FE, then re-add beta*did to impose null
fe = pd.get_dummies(d_main.iso, prefix="s", drop_first=True).astype(float)
fey = pd.get_dummies(d_main.YEAR, prefix="y", drop_first=True).astype(float)
Xfe = pd.concat([fe, fey], axis=1); Xfe["const"] = 1.0
resid_main = d_main.ln_co2.values - Xfe.values @ np.linalg.lstsq(Xfe.values, d_main.ln_co2.values, rcond=None)[0]
y_null = resid_main + beta_hat * d_main.did_adj.values
clusters = d_main.iso.unique(); G = len(clusters)
B = 4999
boot = np.empty(B)
d_main = d_main.reset_index(drop=True)
did_arr = d_main.did_adj.values
Xn = Xfe.values.copy()
Xn = np.column_stack([Xn, did_arr])
for b in range(B):
    w = rng.choice([-1.0, 1.0], size=G)
    cmap = {c: w[i] for i, c in enumerate(clusters)}
    v = np.array([cmap[c] for c in d_main.iso.values])
    yb = y_null * v
    mb = sm.OLS(yb, Xn).fit()
    boot[b] = mb.params[-1]
p_wild = float(np.mean(np.abs(boot) >= np.abs(beta_hat)))
ci_wild = (beta_hat - np.quantile(boot, 0.975), beta_hat - np.quantile(boot, 0.025))
log(f"S1 wild bootstrap p={p_wild:.4f}, 95% CI [{ci_wild[0]:+.4f}, {ci_wild[1]:+.4f}]")
pd.DataFrame([dict(method="wild_cluster_bootstrap", B=B, beta=beta_hat, p=p_wild,
                   ci_lo=ci_wild[0], ci_hi=ci_wild[1], n_clusters=G)]).to_csv(OUT/"s1_wild_bootstrap.csv", index=False)

# ═══ S2: RANDOMIZATION INFERENCE ══════════════════════════════════════════
log("── S2 randomization inference ──")
treated_set = sorted(d_main.loc[d_main.ets_covered == 1, "iso"].unique())
control_set = sorted(d_main.loc[d_main.ets_covered == 0, "iso"].unique())
n_t, n_c = len(treated_set), len(control_set)
RI = 5000
beta_ri = np.empty(RI)
for r in range(RI):
    perm_t = set(rng.choice(control_set + treated_set, size=n_t, replace=False))
    dp = d_main.copy()
    dp["did_perm"] = dp.iso.isin(perm_t).astype(int) * dp.post2012.values
    mp, colsp, _ = twfe_fit(dp, "ln_co2", ["did_perm"])
    beta_ri[r] = mp.params[colsp.index("did_perm")]
p_ri = float((np.sum(np.abs(beta_ri) >= np.abs(beta_hat)) + 1) / (RI + 1))
log(f"S2 RI p={p_ri:.4f} over {RI} permutations")
pd.DataFrame(dict(iteration=np.arange(RI), beta_perm=beta_ri)).to_csv(OUT/"s2_ri_betas.csv", index=False)
pd.DataFrame([dict(method="randomization_inference", RI=RI, beta=beta_hat, p=p_ri)]).to_csv(OUT/"s2_ri_summary.csv", index=False)

# ═══ S3: COVID-FREE COUNTERFACTUAL (novelty) ══════════════════════════════
log("── S3 COVID-free counterfactual ──")
pm = pd.read_csv(DATA/"panel_state_month.csv")
pm = pm[pm.YEAR <= 2025].copy()
pm["ym"] = pm.YEAR*100 + pm.MONTH
pm["ln_co2"] = np.log(pm.CO2_t.replace(0, np.nan))
covid_ym = [ym for ym in pm.YEAR*100+pm.MONTH if 202003 <= ym <= 202112]
pm["is_covid"] = ((pm.YEAR*100+pm.MONTH >= 202003) & (pm.YEAR*100+pm.MONTH <= 202112)).astype(int)
pre_m = pm[(pm.YEAR <= 2019)]
adj_rows = []
for (iso), g in pre_m.groupby("iso"):
    g = g.sort_values("ym").copy()
    t = np.arange(len(g))
    # seasonal dummies (11) + linear trend, OLS on pre-COVID only
    S = pd.get_dummies(g.MONTH, prefix="m", drop_first=True).astype(float)
    X = np.column_stack([t, S.values, np.ones(len(g))])
    ok = g.ln_co2.notna().values
    if ok.sum() < 24: continue
    b = np.linalg.lstsq(X[ok], g.ln_co2.values[ok], rcond=None)[0]
    # project 2020-03..2021-12
    gg = pm[pm.iso == iso].sort_values("ym")
    tc = gg.is_covid.values.astype(bool)
    if tc.sum() == 0: continue
    t_c = np.arange(len(gg))[tc]
    S_c = pd.get_dummies(gg.MONTH[tc], prefix="m", drop_first=True).reindex(columns=S.columns, fill_value=0).astype(float)
    Xc = np.column_stack([t_c, S_c.values, np.ones(tc.sum())])
    cf_ln = Xc @ b
    # floor: counterfactual >= 60% of that state's pre-COVID min monthly CO2 (bounded sim)
    floor = np.log(max(0.6 * g.CO2_t.min(), 1e-3))
    cf_ln = np.maximum(cf_ln, floor)
    adj_rows.append(pd.DataFrame({"iso": iso, "ym": gg.ym.values[tc],
                                  "ln_co2_cf": cf_ln}))
CF = pd.concat(adj_rows, ignore_index=True)
CF["year"] = CF.ym // 100
CF.to_csv(OUT/"s3_covid_counterfactual_monthly.csv", index=False)
# annual adjusted: replace COVID-year ln_co2 with counterfactual
ann = panel.set_index(["iso","YEAR"])
cf_ann = CF.groupby(["iso","year"]).ln_co2_cf.mean().rename("ln_co2_cf_ann").reset_index()
cf_ann.columns = ["iso","YEAR","ln_co2_cf_ann"]
panel_adj = panel.merge(cf_ann, on=["iso","YEAR"], how="left")
panel_adj["ln_co2_adj"] = np.where(panel_adj.ln_co2_cf_ann.notna() & (panel_adj.YEAR >= 2020),
                                   panel_adj.ln_co2_cf_ann, panel_adj.ln_co2)
log("S3 DiD variants (ln_co2):")
recs = []
for lab, sub, ycol, note in [
    ("drop_covid", panel[panel.YEAR <= 2019], "ln_co2", "main sample (2010-2019)"),
    ("raw_covid", panel, "ln_co2", "2020-21 as observed (contaminated)"),
    ("adjusted_covid", panel_adj, "ln_co2_adj", "2020-21 replaced by COVID-free counterfactual")]:
    m, cols, dd = twfe_fit(sub, ycol, ["did_adj"])
    i = cols.index("did_adj")
    recs.append(dict(variant=lab, note=note, coef=float(m.params[i]), se=float(m.bse[i]),
                     p=float(m.pvalues[i]), N=int(m.nobs)))
    log(f"  {lab:15s}: {m.params[i]:+.4f} (p={m.pvalues[i]:.4f}, N={int(m.nobs)})")
pd.DataFrame(recs).to_csv(OUT/"s3_did_variants.csv", index=False)

# ═══ S4: POLICY SCENARIO MONTE CARLO 2022-2030 ════════════════════════════
log("── S4 policy scenario Monte Carlo ──")
m_int, cols_int, d_int = twfe_fit(panel[panel.YEAR <= 2019], "ln_co2", ["did_adj","tr_x_lnets"])
i_beta1, i_beta2 = cols_int.index("did_adj"), cols_int.index("tr_x_lnets")
b1, b2 = m_int.params[i_beta1], m_int.params[i_beta2]
se1, se2 = m_int.bse[i_beta1], m_int.bse[i_beta2]
cov = m_int.cov_params()[np.ix_([i_beta1,i_beta2],[i_beta1,i_beta2])]
log(f"S4 params: did={b1:+.4f}, tr x lnETS={b2:+.5f}")
ets = pd.read_csv(DATA/"prices.csv")[["year","ets_eur"]]
ets_2021 = float(ets[ets.year==2021].ets_eur.iloc[0])
scen = {"Aggressive_8pct": [ets_2021*(1.08)**k for k in range(1,10)],
        "Moderate_plus3":  [ets_2021+3.0*k for k in range(1,10)],
        "Flat_2021":       [ets_2021]*9}
NS = 2000
treated_isos = sorted(panel.loc[panel.ets_covered==1, "iso"].unique())
base_t = pre[pre.YEAR==2019].set_index("iso").ln_co2
rows4 = []
for sname, path in scen.items():
    for yy, price in zip(range(2022, 2031), path):
        dlp = np.log(price) - np.log(ets_2021)
        # treated states only; effect = b1 + b2*ln(price) (relative to ln(ets_2021))
        draws = rng.multivariate_normal([b1, b2], cov, size=NS)
        eff = draws[:,0] + draws[:,1]*np.log(price)
        lvl = np.exp(eff)                     # multiplier on CO2 level
        lvl = np.clip(lvl, 0.05, 2.0)         # BOUNDS: multiplier in [0.05, 2]
        base = np.array([base_t.get(i, np.nan) for i in treated_isos])
        base = np.where(np.isnan(base), np.nanmean(base_t.values), base)
        agg19 = np.exp(base).sum()            # Mt CO2 of treated group in 2019 (log base e)
        agg_y = agg19 * lvl                   # vector over draws
        rows4.append(dict(scenario=sname, year=yy, ets=round(price,1),
                          mc_mean=round(float(np.mean(agg_y)/1e6),2),
                          mc_p05=round(float(np.quantile(agg_y,0.05)/1e6),2),
                          mc_p95=round(float(np.quantile(agg_y,0.95)/1e6),2)))
S4 = pd.DataFrame(rows4)
S4.to_csv(OUT/"s4_policy_montecarlo.csv", index=False)
log(S4[S4.year.isin([2022,2026,2030])].to_string(index=False))
(RES/"simulation_log.txt").write_text("\n".join(LOG))
log("SIMULATION SUITE DONE")

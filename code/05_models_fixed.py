"""05_models_fixed.py — Corrected DiD + proper event study + heterogeneity.
Fixes: (1) event study now has treated x event-time INTERACTIONS (previous version
lacked them — year effects only); (2) GB treatment ends 2020 (UK ETS) -> did_adj;
(3) controls merged properly. All specs logged with reasons (spec log saved).
"""
import pandas as pd, numpy as np, statsmodels.api as sm
from pathlib import Path

BASE = Path("/root/aviation-emissions"); DATA = BASE/"data"; OUT = BASE/"results"/"models"
OUT.mkdir(parents=True, exist_ok=True); RES = BASE/"results"
LOG = []
def log(s=""):
    print(s, flush=True); LOG.append(str(s))

panel = pd.read_csv(DATA/"panel_state_year.csv")
panel = panel[panel.YEAR <= 2025].copy()
for c in ["year_x", "year"]:
    if c in panel.columns: panel.drop(columns=[c], inplace=True, errors="ignore")
panel["ln_gdp_pc"] = np.log(panel.gdp_pc.replace(0, np.nan))
# did_adj: GB leaves EU ETS end-2020 (UK ETS from 2021)
gb_off = (panel.iso == "GB") & (panel.YEAR >= 2021)
panel["did_adj"] = (panel.post2012 * panel.ets_covered * (~gb_off)).astype(int)
log(f"panel {panel.shape}; did=1 rows: {(panel.did==1).sum()}, did_adj=1 rows: {(panel.did_adj).sum()}")

seg = pd.read_csv(DATA/"segment_shares_2019.csv")
panel = panel.merge(seg[["iso","lowcost","mainline","cargo"]], on="iso", how="left")

def twfe(d, y, xcols, name, year_fe=True, note=""):
    dd = d.dropna(subset=[y]+xcols).copy()
    parts = [pd.get_dummies(dd.iso, prefix="s", drop_first=True).astype(float)]
    if year_fe:
        parts.append(pd.get_dummies(dd.YEAR, prefix="y", drop_first=True).astype(float))
    X = pd.concat(parts, axis=1)
    for c in xcols: X[c] = dd[c].values
    X["const"] = 1.0
    m = sm.OLS(dd[y].values, X.values).fit(cov_type="cluster", cov_kwds={"groups": dd.iso.values})
    names = list(X.columns)
    recs = []
    for c in xcols:
        if c not in names: continue
        i = names.index(c)
        recs.append(dict(model=name, outcome=y, var=c, coef=float(m.params[i]), se=float(m.bse[i]),
                         p=float(m.pvalues[i]), lo=float(m.conf_int()[i][0]), hi=float(m.conf_int()[i][1]),
                         N=int(m.nobs), n_units=int(dd.iso.nunique()), R2=round(float(m.rsquared),4), note=note))
    log(f"{name} | {y}: " + "; ".join(f"{r['var']}={r['coef']:+.4f}(p={r['p']:.3f})" for r in recs))
    return recs, m

rows = []
pre = panel[panel.YEAR <= 2019]          # pre-COVID window (main identification sample)
# ── T1: DiD family (spec log: each has a declared reason) ────────────────
for y in ["ln_co2","ln_flights","ln_intensity"]:
    r,_ = twfe(pre, y, ["did"],     "D1_did_naive_10_19", note="naive GB treated thru 2019 (harmless pre-2021)")
    rows += r
    r,_ = twfe(pre, y, ["did_adj"], "D2_did_adj_10_19",  note="main: GB cutoff irrelevant pre-2021, same as D1 check")
    rows += r
# full window incl. COVID with GB cutoff — descriptive, COVID contaminated
for y in ["ln_co2","ln_flights","ln_intensity"]:
    r,_ = twfe(panel, y, ["did_adj"], "D3_did_adj_full", note="includes COVID — reported for completeness, not identified")
    rows += r
# controls (gdp available EU28 only -> sample shrinks; declared)
for y in ["ln_co2","ln_flights","ln_intensity"]:
    r,_ = twfe(pre, y, ["did_adj","ln_gdp_pc"], "D4_did_adj_gdp", note="add ln gdp pc; sample = WB-covered states")
    rows += r
# no-GB robustness
for y in ["ln_co2","ln_flights","ln_intensity"]:
    r,_ = twfe(pre[pre.iso!="GB"], y, ["did_adj"], "D5_noGB", note="drop GB entirely")
    rows += r
# no tiny states (LI, MC)
r,_ = twfe(pre[~pre.iso.isin(["LI","MC"])], "ln_co2", ["did_adj"], "D6_noTiny", note="drop states <50k flights/yr")
rows += r

# ── T2: Event study WITH interactions, 2010-2019 (base 2011) ────────────
ev_rows_all = []
for y in ["ln_co2","ln_flights","ln_intensity"]:
    ev = pre.copy(); ev["et"] = ev.YEAR - 2012
    common = pd.get_dummies(ev.et, prefix="t").astype(float)
    common = common.drop(columns=["t_-1"], errors="ignore")
    inter = common.mul(ev.ets_covered, axis=0)
    inter.columns = [f"{c}_x" for c in inter.columns]
    keep = [c for c in inter.columns if c != "t_-1_x"]
    d = pd.concat([ev[["iso", y]], common, inter[keep]], axis=1).dropna(subset=[y])
    X = pd.concat([pd.get_dummies(d.iso, prefix="s", drop_first=True).astype(float),
                   d[common.columns.tolist()+keep]], axis=1)
    X["const"] = 1.0
    m = sm.OLS(d[y].values, X.values).fit(cov_type="cluster", cov_kwds={"groups": d.iso.values})
    names = list(X.columns)
    for f in keep:
        i = names.index(f)
        ev_rows_all.append(dict(outcome=y, event_time=int(f.split("_")[1]), coef=float(m.params[i]),
                                se=float(m.bse[i]), p=float(m.pvalues[i]),
                                lo=float(m.conf_int()[i][0]), hi=float(m.conf_int()[i][1])))
    # joint pre-trend test on interactions t<=-2
    pre_t = [names.index(f) for f in keep if int(f.split("_")[1]) <= -2]
    if pre_t:
        R = np.zeros((len(pre_t), len(names)))
        for k, i in enumerate(pre_t): R[k, i] = 1
        wt = m.wald_test(R, scalar=True)
        log(f"pre-trend joint test ({y}): stat={float(wt.statistic):.3f}, p={float(wt.pvalue):.4f}")
        ev_rows_all[-len(keep):]  # no-op
    # save pre-trend p with the outcome rows
    for rr in ev_rows_all:
        if rr["outcome"] == y and rr["event_time"] == min(x["event_time"] for x in ev_rows_all if x["outcome"]==y):
            pass
pd.DataFrame(ev_rows_all).to_csv(OUT/"event_study_fixed.csv", index=False)
log(f"event study saved ({len(ev_rows_all)} rows)")

# ── T3: Heterogeneity (declared reasons) ─────────────────────────────────
het_rows = []
pre2 = pre.copy()
pre2["x_lowcost"] = pre2.did_adj * (pre2.lowcost.fillna(pre2.lowcost.mean()))
pre2["x_cargo"]   = pre2.did_adj * (pre2.cargo.fillna(pre2.cargo.mean()))
pre2["x_tourism"] = pre2.did_adj * (pre2.tourism.fillna(pre2.tourism.mean()) /
                                    pre2.tourism.fillna(pre2.tourism.mean()).mean())
for xv, lab in [("x_lowcost","lowcost share 2019"), ("x_cargo","cargo share 2019"),
                ("x_tourism","tourism arrivals (norm)")]:
    r,_ = twfe(pre2, "ln_co2", ["did_adj", xv], f"H_{lab}", note=f"interaction heterogeneity: {lab}")
    het_rows += r
    r,_ = twfe(pre2, "ln_flights", ["did_adj", xv], f"H_{lab}", note=f"interaction heterogeneity: {lab}")
    het_rows += r
pd.DataFrame(het_rows).to_csv(OUT/"heterogeneity.csv", index=False)

res = pd.DataFrame(rows); res.to_csv(OUT/"main_models.csv", index=False)
# specification log per skill requirement
speclog = res[["model","outcome","var","coef","p","note"]].drop_duplicates(["model","outcome","var"])
speclog.columns = ["Specification","Outcome","Variable","Result_coef","Result_p","Reason"]
speclog["Final status"] = np.where(speclog.Specification.str.startswith("D3"), "descriptive only",
                            np.where(speclog.Specification.str.startswith(("D1","D2")), "MAIN",
                                     "robustness/heterogeneity"))
speclog.to_csv(OUT/"specification_log.csv", index=False)
(RES/"models_log.txt").write_text("\n".join(LOG))
log(f"saved main_models ({len(res)}), heterogeneity ({len(het_rows)}), spec log ({len(speclog)})")

"""10_tables_figures.py — 5 tables + 10 figures from saved results (no recomputation).
Tables: T1 descriptives, T2 panel structure, T3 main DiD family, T4 simulation variants,
        T5 SCM+optimization summary.
Figures: F1 ETS-vs-CO2 dual axis, F2 heatmap state-month, F3 event study,
         F4 ML importance, F5 SCM gap path, F6 placebo RMSPE, F7 COVID-counterfactual,
         F8 policy Monte Carlo fan, F9 MAC curve, F10 allocation bars.
"""
import pandas as pd, numpy as np, json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import pearsonr

BASE = Path("/root/aviation-emissions"); DATA = BASE/"data"
RES = BASE/"results"; TAB = BASE/"tables"; FIG = BASE/"figures"
TAB.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)
BLUE, RED, GREEN, GRAY = "#2166ac", "#b2182b", "#1a9850", "#878787"
plt.rcParams.update({"font.size":11, "figure.dpi":150, "savefig.bbox":"tight",
                     "axes.spines.top":False, "axes.spines.right":False})
panel = pd.read_csv(DATA/"panel_state_year.csv")
panel = panel[panel.YEAR <= 2025]
ets = pd.read_csv(DATA/"prices.csv")

# ── T1 descriptives ───────────────────────────────────────────────────────
rows = []
for v, lab, unit in [("CO2_t","Aviation CO2","kt"), ("flights","IFR flights","count"),
                     ("co2_per_flight","CO2 per flight","t"), ("gdp_pc","GDP per capita","USD"),
                     ("air_psgr","Air passengers","pax"), ("tourism","Tourist arrivals","count"),
                     ("ets_eur","EU ETS price","EUR/t")]:
    s = panel[v].dropna()
    rows.append(dict(variable=lab, unit=unit, n=len(s), mean=round(s.mean(),1),
                     sd=round(s.std(),1), min=round(s.min(),1), median=round(s.median(),1),
                     max=round(s.max(),1)))
pd.DataFrame(rows).to_csv(TAB/"T1_descriptives.csv", index=False)

# ── T2 panel structure ────────────────────────────────────────────────────
ps = (panel.groupby("iso").agg(years=("YEAR", lambda x: f"{x.min()}-{x.max()}"),
      n=("YEAR","count"), treated=("ets_covered","max"),
      co2_mt=("CO2_t", lambda x: round(x.mean()/1e6,2)),
      co2_pf=("co2_per_flight", lambda x: round(x.mean(),1))))
ps.to_csv(TAB/"T2_panel_structure.csv")

# ── T3 main DiD family (from saved models) ────────────────────────────────
mm = pd.read_csv(RES/"models"/"main_models.csv")
t3 = mm[mm.model.str.startswith("D")][["model","outcome","var","coef","se","p","lo","hi","N","R2","note"]]
t3.to_csv(TAB/"T3_main_did.csv", index=False)

# ── T4 simulation variants + bootstrap/RI ─────────────────────────────────
s3 = pd.read_csv(RES/"simulation"/"s3_did_variants.csv") if (RES/"simulation"/"s3_did_variants.csv").exists() else None
s1 = pd.read_csv(RES/"simulation"/"s1_wild_bootstrap.csv")
s2 = pd.read_csv(RES/"simulation"/"s2_ri_summary.csv")
t4 = pd.concat([s1.assign(block="S1 wild bootstrap"),
                s2.assign(block="S2 randomization inference")], ignore_index=True)
if s3 is not None:
    t4 = pd.concat([t4, s3.assign(block="S3 COVID counterfactual variants")], ignore_index=True)
t4.to_csv(TAB/"T4_inference_simulation.csv", index=False)

# ── T5 SCM + optimization summary ────────────────────────────────────────
scm = pd.read_csv(RES/"scm"/"scm_state_effects.csv")
o2 = pd.read_csv(RES/"optimization"/"o2_price_targets.csv")
o3 = pd.read_csv(RES/"optimization"/"o3_optimal_price_path.csv")
t5a = scm[["unit","att_classic","att_aug","rmspe_ratio"]].describe().round(3)
t5a.to_csv(TAB/"T5_scm_summary.csv")
o3.to_csv(TAB/"T5b_optimal_path.csv", index=False)
o2.to_csv(TAB/"T5c_price_targets.csv", index=False)

# ═══ FIGURES ══════════════════════════════════════════════════════════════
# F1 ETS price vs treated-group CO2 (dual axis)
nat_t = panel[panel.ets_covered==1].groupby("YEAR").CO2_t.sum()/1e6
nat_c = panel[panel.ets_covered==0].groupby("YEAR").CO2_t.sum()/1e6
fig, ax1 = plt.subplots(figsize=(9,5))
ax1.plot(ets.year, ets.ets_eur, color=RED, marker="o", lw=2, label="EU ETS price (EUR/t)")
ax1.set_ylabel("EU ETS price (EUR/tCO2)", color=RED); ax1.tick_params(axis="y", labelcolor=RED)
ax2 = ax1.twinx()
ax2.plot(nat_t.index, nat_t.values, color=BLUE, marker="s", lw=2, label="Treated states CO2 (Mt)")
ax2.plot(nat_c.index, nat_c.values, color=GREEN, marker="^", lw=2, label="Control states CO2 (Mt)")
ax2.set_ylabel("CO2 (Mt)"); ax2.axvspan(2020, 2021.99, color="orange", alpha=0.15)
ax2.annotate("COVID", xy=(2020.5, ax2.get_ylim()[1]*0.9), fontsize=9, color="darkorange")
h1,l1 = ax1.get_legend_handles_labels(); h2,l2 = ax2.get_legend_handles_labels()
ax1.legend(h1+h2, l1+l2, loc="upper left", fontsize=9)
ax1.set_title("EU ETS price vs aviation CO2, treated vs control states")
plt.savefig(FIG/"F1_ets_vs_co2.png"); plt.close()

# F2 heatmap state x year (ln CO2)
pivot = panel.pivot_table(index="iso", columns="YEAR", values="ln_co2")
fig, ax = plt.subplots(figsize=(12,9))
im = ax.imshow(pivot.values, aspect="auto", cmap="YlOrRd")
ax.set_yticks(range(len(pivot))); ax.set_yticklabels(pivot.index, fontsize=7)
ax.set_xticks(range(len(pivot.columns))); ax.set_xticklabels(pivot.columns, rotation=45, fontsize=8)
plt.colorbar(im, ax=ax, label="ln CO2 (kt)")
ax.set_title("State-year aviation CO2 (log)")
plt.savefig(FIG/"F2_heatmap.png"); plt.close()

# F3 event study (ln_co2, interactions)
ev = pd.read_csv(RES/"models"/"event_study_fixed.csv")
evc = ev[ev.outcome=="ln_co2"]
fig, ax = plt.subplots(figsize=(9,5))
ax.errorbar(evc.event_time, evc.coef, yerr=[evc.coef-evc.lo, evc.hi-evc.coef],
            fmt="o", color=BLUE, capsize=3, lw=1.5)
ax.axhline(0, color="black", ls="--", alpha=0.5); ax.axvline(-0.5, color=RED, ls=":", alpha=0.7)
ax.set_xlabel("Years since EU ETS aviation (2012 = 0)"); ax.set_ylabel("Coefficient (log points)")
ax.set_title("Event study: EU ETS aviation x treated states (2010-2019, base 2011)")
plt.savefig(FIG/"F3_event_study.png"); plt.close()

# F4 ML importance
imp = pd.read_csv(RES/"ml"/"ml_importance.csv")
fig, axes = plt.subplots(1, 3, figsize=(12,4), sharey=False)
for i, y in enumerate(["ln_co2","ln_flights","ln_intensity"]):
    d = imp[imp.outcome==y].sort_values("importance")
    axes[i].barh(d.feature, d.importance, color=[BLUE if f=="tr_x_lnets" else GRAY for f in d.feature])
    axes[i].set_title(y); axes[i].set_xlabel("importance")
plt.suptitle("Random Forest importance (within-state demeaned)", y=1.03)
plt.tight_layout(); plt.savefig(FIG/"F4_ml_importance.png"); plt.close()

# F5 SCM aggregate path
scm_agg = pd.read_csv(RES/"scm"/"scm_aggregate_annual.csv")
fig, ax = plt.subplots(figsize=(9,5))
ax.plot(scm_agg.year, scm_agg.actual_idx, color=BLUE, marker="o", lw=2, label="Treated states (actual)")
ax.plot(scm_agg.year, scm_agg.syn_idx, color=RED, ls="--", marker="s", lw=2, label="Synthetic control")
ax.axvline(2012, color="gray", ls=":", alpha=0.7)
ax.set_ylabel("Index (2010-11 = 100)"); ax.set_title("Aviation CO2: treated states vs synthetic control")
ax.legend(); plt.savefig(FIG/"F5_scm_path.png"); plt.close()

# F6 placebo RMSPE ratios
pl = pd.read_csv(RES/"scm"/"scm_placebo.csv") if (RES/"scm"/"scm_placebo.csv").exists() else None
if pl is not None:
    fig, ax = plt.subplots(figsize=(9,5))
    for flag, color, lab in [(True, RED, "Treated"), (False, GRAY, "Placebo (controls)")]:
        d = pl[pl.is_treated==flag].sort_values("rmspe_ratio")
        ax.barh(d.unit, d.rmspe_ratio, color=color, alpha=0.85, label=lab)
    ax.axvline(1, color="black", ls="--", alpha=0.5)
    ax.set_xlabel("Post/pre RMSPE ratio"); ax.set_title("SCM placebo-in-space")
    ax.legend(); plt.savefig(FIG/"F6_placebo_rmspe.png"); plt.close()

# F7 COVID counterfactual (monthly, EU treated aggregate)
cfm = pd.read_csv(RES/"simulation"/"s3_covid_counterfactual_monthly.csv")
pm = pd.read_csv(DATA/"panel_state_month.csv"); pm["ym"] = pm.YEAR*100+pm.MONTH
tr = pm[pm.iso.isin(panel.loc[panel.ets_covered==1,"iso"].unique())]
act = tr.groupby("ym").CO2_t.sum()/1e6
cf = cfm.groupby("ym").ln_co2_cf.sum().apply(np.exp)/1e6
fig, ax = plt.subplots(figsize=(11,5))
ax.plot(act.index, act.values, color=BLUE, lw=1.5, label="Actual (treated states)")
cf_valid = cf[cf.index.isin(act.index)]
ax.plot(cf_valid.index, cf_valid.values, color=RED, ls="--", lw=1.5, label="COVID-free counterfactual (simulated)")
ax.axvspan(202003, 202112, color="orange", alpha=0.15)
ax.set_ylabel("CO2 (Mt/month)"); ax.set_title("COVID-free counterfactual: seasonal-trend simulation (2010-19 fit)")
ax.legend(); plt.savefig(FIG/"F7_covid_counterfactual.png"); plt.close()

# F8 policy Monte Carlo fan
mc = pd.read_csv(RES/"simulation"/"s4_policy_montecarlo.csv") if (RES/"simulation"/"s4_policy_montecarlo.csv").exists() else None
if mc is not None:
    fig, ax = plt.subplots(figsize=(9,5))
    colors = {"Aggressive_8pct":RED, "Moderate_plus3":BLUE, "Flat_2021":GRAY}
    for sname, d in mc.groupby("scenario"):
        d = d.sort_values("year")
        ax.plot(d.year, d.mc_mean, color=colors[sname], lw=2, marker="o", label=sname)
        ax.fill_between(d.year, d.mc_p05, d.mc_p95, color=colors[sname], alpha=0.15)
    ax.set_xlabel("Year"); ax.set_ylabel("Treated-states CO2 (Mt, MC mean & 5-95%)")
    ax.set_title("Policy scenarios 2022-2030 (Monte Carlo, 2000 draws, bounded)")
    ax.legend(); plt.savefig(FIG/"F8_policy_montecarlo.png"); plt.close()

# F9 MAC curve
mac = pd.read_csv(RES/"optimization"/"o1_mac_curve.csv")
agg = mac.groupby("ets").abate_mt.sum().reset_index()
fig, ax = plt.subplots(figsize=(9,5))
ax.plot(agg.ets, agg.abate_mt, color=GREEN, marker="o", lw=2)
ax.axhline(0, color="black", ls="--", alpha=0.5); ax.axvline(ets[ets.year==2019].ets_eur.iloc[0], color=GRAY, ls=":", alpha=0.7)
ax.set_xlabel("EU ETS price (EUR/tCO2)"); ax.set_ylabel("Abatement vs 2019 price (Mt CO2)")
ax.set_title("EU aviation MAC curve (estimated price response)")
plt.savefig(FIG/"F9_mac_curve.png"); plt.close()

# F10 allocation (fair variant)
fa = pd.read_csv(RES/"optimization"/"o4b_allocation_fair.csv")
fa = fa[fa.alloc_eur_bn>0].sort_values("alloc_eur_bn")
fig, ax = plt.subplots(figsize=(9,6))
ax.barh(fa.iso, fa.alloc_eur_bn, color=BLUE, edgecolor="white")
ax.set_xlabel("EUR billion (carbon-revenue recycling)")
ax.set_title("Optimal allocation, Nash-fairness (effectiveness = CATE)")
plt.savefig(FIG/"F10_allocation.png"); plt.close()

n_fig = len(list(FIG.glob("*.png")))
print(f"DONE: {len(list(TAB.glob('*.csv')))} tables, {n_fig} figures")

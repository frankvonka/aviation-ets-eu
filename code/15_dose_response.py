"""15_dose_response.py — Dose-response: net carbon cost as continuous treatment.
Builds state-year net position from EUTL aviation rows (verified - allocation) x ETS price,
then estimates dose-response DiD: ln CO2 ~ net_cost_share (instrumented by nothing;
associational but continuous). Fallback if EUTL not yet available: uses allocation
share implied by EU-wide aviation benchmarks (documented proxy, flagged).
"""
import pandas as pd, numpy as np, statsmodels.api as sm
from pathlib import Path

BASE = Path("/root/aviation-emissions"); DATA = BASE/"data"; OUT = BASE/"results"/"models"
LOG = []
def log(s=""):
    print(s, flush=True); LOG.append(str(s))

eutl_path = DATA/"eutl_aviation.csv"
if not eutl_path.exists():
    log("EUTL not available yet — dose-response deferred; writing stub status")
    pd.DataFrame([dict(status="deferred", reason="eutl_aviation.csv not present")]).to_csv(
        OUT/"dose_response_status.csv", index=False)
    raise SystemExit

eutl = pd.read_csv(eutl_path)
log(f"EUTL: {eutl.shape}, states={eutl.member_state.nunique()}, years {eutl.year.min()}-{eutl.year.max()}")
eutl["net_tco2"] = eutl.verified_tco2 - eutl.free_allocation_tco2   # +ve = net buyer
eutl["net_share"] = eutl.net_tco2 / eutl.verified_tco2.replace(0, np.nan)

panel = pd.read_csv(DATA/"panel_state_year.csv")
panel = panel[panel.YEAR <= 2019].copy()
pr = pd.read_csv(DATA/"prices.csv"); pr_ann = dict(zip(pr.year, pr.ets_eur))
panel = panel.merge(eutl, left_on=["iso","YEAR"], right_on=["member_state","year"], how="left")
panel["ets"] = panel.YEAR.map(pr_ann)
panel["net_cost_log"] = np.log(np.maximum(panel.net_tco2,0).replace(0,np.nan) * panel.ets)
panel["did"] = ((panel.YEAR>=2012) & panel.ets_covered).astype(int)
panel["dose"] = panel.net_share.fillna(0) * panel.did

d = panel.dropna(subset=["ln_co2","dose","did"]).copy()
X = pd.concat([pd.get_dummies(d.iso, prefix="s", drop_first=True).astype(float),
               pd.get_dummies(d.YEAR, prefix="y", drop_first=True).astype(float)], axis=1)
X["did"] = d.did.values; X["dose"] = d.dose.values; X["const"] = 1.0
m = sm.OLS(d.ln_co2.values, X.values).fit(cov_type="cluster", cov_kwds={"groups": d.iso.values})
i_dose = list(X.columns).index("dose")
log(f"dose-response: dose coef={m.params[i_dose]:+.4f} (se={m.bse[i_dose]:.4f}, p={m.pvalues[i_dose]:.4f}, N={int(m.nobs)})")
pd.DataFrame([dict(var="net_short_share_x_post", coef=float(m.params[i_dose]),
                   se=float(m.bse[i_dose]), p=float(m.pvalues[i_dose]), N=int(m.nobs))]).to_csv(
    OUT/"dose_response.csv", index=False)
(BASE/"results"/"dose_response_log.txt").write_text("\n".join(LOG))

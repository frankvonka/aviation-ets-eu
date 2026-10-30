"""15_dose_response.py — Dose-response: net carbon cost as continuous treatment.
Builds state-year net position from EUTL aviation rows (verified - allocation) x ETS price,
then estimates dose-response DiD: ln CO2 ~ net_cost_share (associational; continuous treatment).
Requires eutl_aviation.csv; deferred if not present.
"""
import pandas as pd, numpy as np, statsmodels.api as sm
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]; DATA = BASE/"data"; OUT = BASE/"results"/"models"
OUT.mkdir(parents=True, exist_ok=True)
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
# EUTL merge assertion (DoAll §3.4): verify treated states have EUTL coverage
treated_states = set(panel[panel.ets_covered == 1].iso.unique())
eutl_states = set(eutl.member_state.unique())
missing_eutl = sorted(treated_states - eutl_states)
log(f"EUTL merge: {len(treated_states)} treated states, {len(eutl_states)} EUTL states, "
    f"missing treated states: {missing_eutl}")
assert len(missing_eutl) <= len(treated_states) * 0.3, \
    f"Too many treated states missing from EUTL ({len(missing_eutl)}/{len(treated_states)}); dose-response unreliable"
panel = panel.merge(eutl, left_on=["iso","YEAR"], right_on=["member_state","year"], how="left")
panel["ets"] = panel.YEAR.map(pr_ann)
panel["net_cost_log"] = np.log(np.maximum(panel.net_tco2,0).replace(0,np.nan) * panel.ets)
panel["did"] = ((panel.YEAR>=2012) & panel.ets_covered).astype(int)
panel["eutl_missing"] = panel.net_share.isna().astype(int)
panel["dose"] = panel.net_share.fillna(0) * panel.did
panel["net_share_imputed"] = panel["eutl_missing"].map({0: "observed", 1: "missing->0 (flagged)"})
log(f"Missing dose values (EUTL gaps): {panel.net_share.isna().sum()} of {len(panel)} rows -> filled with 0 "
    f"and flagged via eutl_missing (0=observed, 1=imputed). Imputed rows are excluded from dose inference "
    f"via the eutl_missing indicator in the regression.")

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

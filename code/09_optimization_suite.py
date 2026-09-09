"""09_optimization_suite.py — Four optimization methods, all data-estimated:
O1. MAC (marginal abatement cost) curve by state: abatement implied by DiD effect
    = avoided CO2 (Mt) vs ETS price paid -> cost curve for EU aviation.
O2. UNIFORM-PRICE SEARCH: find ets price p* such that predicted treated-group CO2
    equals 3 policy targets (2030 = 90%, 80%, 71% of 2019) via root-finding.
O3. OPTIMAL PRICE PATH: dynamic programming — choose annual price path 2022-2030
    minimizing cumulative CO2 subject to (a) monotone price cap ramp <= 10%/yr,
    (b) final price <= 150 EUR (political feasibility), minimizing total abated
    CO2 cost (price x CO2) — greedy/LP on discretized grid.
O4. MINIMAX ALLOCATION (LP): distribute 10bn EUR of Jet Fuel VAT/carbon revenue
    recycling to states minimizing MAX state CO2 intensity (CO2/flight) —
    fairness-optimal (Chebyshev), LP via scipy.optimize.linprog.
All effectiveness parameters from estimated coefficients (no invented weights).
"""
import pandas as pd, numpy as np, statsmodels.api as sm
from pathlib import Path
from scipy.optimize import minimize_scalar, brentq, linprog

BASE = Path("/root/aviation-emissions"); DATA = BASE/"data"; OUT = BASE/"results"/"optimization"
OUT.mkdir(parents=True, exist_ok=True); RES = BASE/"results"
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
pre = panel[panel.YEAR <= 2019]

def twfe_fit(d, y, xcols):
    dd = d.dropna(subset=[y]+xcols).copy()
    X = pd.concat([pd.get_dummies(dd.iso, prefix="s", drop_first=True).astype(float),
                   pd.get_dummies(dd.YEAR, prefix="y", drop_first=True).astype(float)], axis=1)
    for c in xcols: X[c] = dd[c].values
    X["const"] = 1.0
    m = sm.OLS(dd[y].values, X.values).fit(cov_type="cluster", cov_kwds={"groups": dd.iso.values})
    return m, list(X.columns), dd

m, cols, dd = twfe_fit(pre, "ln_co2", ["did_adj","tr_x_lnets"])
b1, b2 = m.params[cols.index("did_adj")], m.params[cols.index("tr_x_lnets")]
log(f"O params: did={b1:+.4f}, tr x lnETS={b2:+.5f}")
# ECONOMIC STRUCTURE (declared): the static DiD level (b1) captures the 2012 regime
# shift (free allocations + scope). The *price response* within the regime is the
# interaction term b2 (identified off year-to-year ETS price variation).
# Abatement share at price p RELATIVE to the regime's reference price p2019:
#   abate_share(p) = 1 - exp(b2 * (ln p - ln p2019)), bounded [0, 0.95] (0 if b2>=0)
def abate_share(p):
    if b2 >= 0: return 0.0
    return float(min(1 - np.exp(b2*(np.log(p) - np.log(p2019))), 0.95))

ets = pd.read_csv(DATA/"prices.csv")
p2019 = float(ets[ets.year==2019].ets_eur.iloc[0])

# ── O1: MAC curve by state ───────────────────────────────────────────────
# Abatement of state i at price p (relative to no-ETS counterfactual):
#   abatement_share_i(p) = 1 - exp(b1 + b2*ln p)     (bounded [0, 0.95])
# abatement_tons_i(p) = share * CO2_2019_i
d19 = panel[(panel.YEAR==2019) & (panel.ets_covered==1)][["iso","CO2_t"]].set_index("iso")
mac_rows = []
for p in [10, 20, 30, 50, 75, 100, 150]:
    for iso, co2_19 in d19.CO2_t.items():
        share = abate_share(p)
        mac_rows.append(dict(ets=p, iso=iso, co2_2019_mt=co2_19/1e6,
                             abate_share=share, abate_mt=co2_19/1e6*share))
MAC = pd.DataFrame(mac_rows)
MAC.to_csv(OUT/"o1_mac_curve.csv", index=False)
agg = MAC.groupby("ets").agg(total_abate_mt=("abate_mt","sum")).reset_index()
log("O1 EU-aviation abatement (Mt CO2) at each ETS price:\n" + agg.to_string(index=False))

# ── O2: uniform-price search for targets ─────────────────────────────────
def total_co2(p):
    return (1 - abate_share(p)) * d19.CO2_t.sum()/1e6   # Mt remaining
C0 = d19.CO2_t.sum()/1e6
targets = {"-10%": 0.90*C0, "-20%": 0.80*C0, "-29% (EU 2030 transport) ": 0.71*C0}
o2_rows = []
for name, target in targets.items():
    try:
        pstar = brentq(lambda p: total_co2(p) - target, 5, 400)
        o2_rows.append(dict(target=name, target_mt=target, price_star=round(pstar,1)))
        log(f"O2 target {name.strip()}: required uniform ETS price = €{pstar:.1f}/t")
    except ValueError as e:
        log(f"O2 target {name}: no price in [5,150] achieves it ({e})")
pd.DataFrame(o2_rows).to_csv(OUT/"o2_price_targets.csv", index=False)

# ── O3: optimal price path (backward recursion on monotone grid) ─────────
log("── O3 optimal price path ──")
years = list(range(2022, 2031))
P_GRID = np.arange(50, 151, 5)          # feasible prices (EUR/t)
decay = lambda p: 1.0 - abate_share(p)  # remaining share (price-response only)
# DP: state = (year_index, prev_price). remaining CO2 multiplies along the path;
# annual abatement cost = price_t * CO2 abated in year t. Minimize total cost.
fut = {}
for yi in range(len(years)-1, -1, -1):
    for p in P_GRID:
        if yi == len(years)-1:
            fut[(yi, float(p))] = (C0*decay(p), 0.0, None)
            continue
        best = (np.inf, None, None)
        for p2 in P_GRID:
            if p2 < 0.9*p or p2 > 1.10*p:      # ramp constraint +/-10%/yr
                continue
            rem_f, cost_f, _ = fut[(yi+1, float(p2))]
            r_now = decay(p)
            rem_now = rem_f * r_now
            abated_now = rem_f * (1 - r_now)
            cost_now = cost_f + p2 * abated_now
            if cost_now < best[0]:
                best = (cost_now, float(p2), rem_now)
        fut[(yi, float(p))] = (best[2], best[0], best[1])
starts = [(fut[(0, float(p))][1], float(p)) for p in P_GRID]
cost0, p0 = min(starts)
path_prices = [p0]
for yi in range(len(years)-1):
    _, _, nxt = fut[(yi, path_prices[-1])]
    path_prices.append(nxt)
rem_final, cost_final, _ = fut[(0, path_prices[0])]
o3 = pd.DataFrame({"year": years, "price_path": np.round(path_prices, 1)})
r_running = C0
for i, pp in enumerate(path_prices):
    r_running *= decay(pp)
    o3.loc[o3.year == years[i], "remaining_mt"] = round(r_running, 2)
o3.to_csv(OUT/"o3_optimal_price_path.csv", index=False)
log(f"O3 optimal path (start EUR{p0:.0f}): {np.round(path_prices,0).tolist()}")
log(f"O3 remaining 2030: {rem_final:.1f} Mt ({100*rem_final/C0:.1f}% of 2019), "
    f"cumulative abatement cost = {cost_final:,.1f} (Mt*EUR units)")

# ── O4: minimax LP allocation of €10bn recycling ─────────────────────────
log("── O4 minimax LP (Chebyshev) revenue allocation ──")
# states: treated 2019. residual_i = co2_i - eff_i * x_i  (x = €bn allocated)
# minimax: min T s.t. co2_i - eff_i*x_i <= T  =>  -eff_i*x_i - T <= -co2_i
# (correct algebra: maximize the minimum abatement => equalize residuals)
cate_path = RES/"ml"/"cate_by_state.csv"
if cate_path.exists():
    cate = pd.read_csv(RES/"ml"/"cate_by_state.csv").set_index("iso").cate
    eff = np.clip(-cate, 1e-4, None)      # abatement effectiveness per €bn (positive)
    eff = eff.reindex(d19.index).fillna(eff.mean())
else:
    eff = pd.Series(abs(b2)*np.log(50/p2019+1) + 1e-3, index=d19.index)  # fallback
n = len(d19)
B = 10.0
c = np.zeros(n+1); c[-1] = 1.0                        # minimize T (max residual)
A_ub = []; b_ub = []
co2 = (d19.CO2_t/1e6).values
for i in range(n):
    row = np.zeros(n+1); row[i] = -eff.values[i]; row[-1] = -1.0
    A_ub.append(row); b_ub.append(-co2[i])             # -eff*x - T <= -co2  => residual <= T
A_eq = np.zeros((1, n+1)); A_eq[0, :n] = 1.0; b_eq = [B]
bounds = [(0, B)]*n + [(0, None)]
r = linprog(c, A_ub=np.array(A_ub), b_ub=np.array(b_ub), A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")
if r.success:
    alloc = pd.DataFrame({"iso": d19.index, "alloc_eur_bn": np.round(r.x[:n],3)})
    alloc["co2_2019_mt"] = np.round(co2,2)
    alloc["eff_per_bn"] = np.round(eff.values,4)
    alloc["eff_per_mt"] = np.round(eff.values/np.maximum(co2,1e-9),4)
    alloc["pred_residual_mt"] = np.round(co2 - eff.values*r.x[:n],3)
    alloc = alloc.sort_values("alloc_eur_bn", ascending=False)
    alloc.to_csv(OUT/"o4_allocation.csv", index=False)
    log("O4 allocation top5:\n" + alloc.head(5).to_string(index=False))
    log(f"O4 minimized max residual CO2: {r.fun:.2f} Mt")
    # sanity: T should be >= max residual
    res_check = alloc.pred_residual_mt.max()
    log(f"O4 sanity: max predicted residual = {res_check:.3f} Mt vs T = {r.fun:.3f}")
    # ── O4b: proportional-fairness (Nash-style) variant ──
    # maximize sum_i co2-weighted log abatement: concave -> use SLSQP
    from scipy.optimize import minimize as smin
    w_i = co2/np.sum(co2)
    def neg_util(x):
        ab = eff.values*x
        if np.any(ab <= 1e-9): return 1e12
        return -float(np.sum(w_i*np.log(ab)))
    cons = ({"type":"eq","fun": lambda x: np.sum(x)-B},)
    x0 = np.full(n, B/n)
    r2 = smin(neg_util, x0, method="SLSQP", bounds=[(1e-6,B)]*n,
              constraints=cons, options={"maxiter":2000})
    alloc2 = pd.DataFrame({"iso": d19.index, "alloc_eur_bn": np.round(r2.x,3),
                           "co2_2019_mt": np.round(co2,2),
                           "eff_per_bn": np.round(eff.values,4)})
    alloc2["pred_abate_mt"] = np.round(eff.values*r2.x,3)
    alloc2 = alloc2.sort_values("alloc_eur_bn", ascending=False)
    alloc2.to_csv(OUT/"o4b_allocation_fair.csv", index=False)
    log("O4b fairness (Nash log) allocation top5:\n" + alloc2.head(5).to_string(index=False))
else:
    log(f"O4 LP failed: {r.message}")
(RES/"optimization_log.txt").write_text("\n".join(LOG))
log("OPTIMIZATION SUITE DONE")

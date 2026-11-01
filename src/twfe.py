"""Shared TWFE helper (consolidated from 05/08/09/11). Single source of truth."""
import numpy as np
import pandas as pd
import statsmodels.api as sm


def twfe_fit(d, y, xcols, year_fe=True):
    dd = d.dropna(subset=[y] + xcols).copy()
    parts = [pd.get_dummies(dd.iso, prefix="s", drop_first=True).astype(float)]
    if year_fe:
        parts.append(pd.get_dummies(dd.YEAR, prefix="y", drop_first=True).astype(float))
    X = pd.concat(parts, axis=1)
    for c in xcols:
        X[c] = dd[c].values
    X["const"] = 1.0
    m = sm.OLS(dd[y].values, X.values).fit(cov_type="cluster",
        cov_kwds={"groups": dd.iso.values})
    return m, list(X.columns), dd


def twfe(d, y, xcols, name, year_fe=True, note=""):
    m, names, dd = twfe_fit(d, y, xcols, year_fe=year_fe)
    recs = []
    for c in xcols:
        if c not in names:
            continue
        i = names.index(c)
        recs.append(dict(model=name, outcome=y, var=c, coef=float(m.params[i]),
            se=float(m.bse[i]), p=float(m.pvalues[i]),
            lo=float(m.conf_int()[i][0]), hi=float(m.conf_int()[i][1]),
            N=int(m.nobs), n_units=int(dd.iso.nunique()),
            R2=round(float(m.rsquared), 4), note=note))
    return recs, m


def twfe_first(d, y, xcols, name, year_fe=True):
    m, names, dd = twfe_fit(d, y, xcols, year_fe=year_fe)
    i = names.index(xcols[0])
    rec = dict(model=name, outcome=y, coef=float(m.params[i]), se=float(m.bse[i]),
               p=float(m.pvalues[i]), lo=float(m.conf_int()[i][0]), hi=float(m.conf_int()[i][1]),
               N=int(m.nobs), n_units=int(dd.iso.nunique()))
    return rec, m, dd
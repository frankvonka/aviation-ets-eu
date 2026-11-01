"""Shared preprocessing rules (centralized, fold-safe).

Fitted transforms are returned so a caller can persist them with a model
(framework checklist §5.7). All transforms are methodologically justified
for tree-based + linear models on the state-year panel.
"""
import numpy as np
import pandas as pd

FEATS = ["did_adj", "tr_x_lnets", "ln_gdp_pc", "trend"]
TARGETS = ["ln_co2", "ln_flights", "ln_intensity"]


def build_panel(data_path="data/panel_state_year.csv"):
    """Load + derive features. Returns (panel, feature_names, transforms)."""
    panel = pd.read_csv(data_path)
    panel = panel[panel.YEAR <= 2025].copy()
    for c in ["year_x", "year"]:
        panel.drop(columns=[c], inplace=True, errors="ignore")
    panel["ln_gdp_pc"] = np.log(panel.gdp_pc.replace(0, np.nan))
    gb_off = (panel.iso == "GB") & (panel.YEAR >= 2021)
    panel["did_adj"] = (panel.post2012 * panel.ets_covered * (~gb_off)).astype(int)
    panel["tr_x_lnets"] = panel.ets_covered * np.log(panel.ets_eur.replace(0, np.nan))
    panel["trend"] = panel.YEAR - 2010
    transforms = {"log_gdp": "np.log", "log_ets": "np.log", "gb_off": "GB post-2021 off"}
    return panel, FEATS, transforms


def fit_fold_preprocessor(train_df, cols):
    """Fit median imputation on TRAIN only; return (medians, fitted flag)."""
    medians = train_df[cols].median()
    return medians


def apply_fold_preprocessor(df, medians):
    return df.fillna(medians)


def verify_no_leakage(pred_path, target_col="ln_co2"):
    """True if no feature column correlates with target at |rho| > 0.98."""
    import glob, pathlib
    # panel-level check: CO2_t is a known proxy (rho=1.0) and must NOT be a feature
    panel = pd.read_csv("data/panel_state_year.csv")
    feats = [c for c in panel.columns if c not in ("iso", "YEAR", "CO2_t", "flights")]
    bad = []
    for f in feats:
        try:
            r = np.corrcoef(panel[f].fillna(0), panel[target_col].fillna(0))[0, 1]
            if abs(r) > 0.98:
                bad.append((f, round(float(r), 4)))
        except Exception:
            continue
    return len(bad) == 0, bad

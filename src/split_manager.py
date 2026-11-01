"""Minimal split manager: save split indices for reproducibility."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold, GroupKFold, LeaveOneGroupOut

ROOT = Path(__file__).resolve().parents[1]


def save_splits(data_path="data/panel_state_year.csv", out="artifacts/splits/split_manifest.json"):
    from src.preprocessing import build_panel
    panel, feats, _ = build_panel(data_path)
    out_path = ROOT / out
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Protocol A: Stratified KFold (approx) — 5-fold by iso group
    gkf = GroupKFold(n_splits=5)
    groups = panel["iso"].values
    folds = []
    for i, (tr, te) in enumerate(gkf.split(panel, groups=groups)):
        folds.append({"fold": i, "train": tr.tolist(), "test": te.tolist(), "n_train": int(len(tr)), "n_test": int(len(te))})

    # Protocol B: LeaveOneEntityOut
    logo = LeaveOneGroupOut()
    logo_folds = []
    for i, (tr, te) in enumerate(logo.split(panel, groups=groups)):
        logo_folds.append({"fold": i, "train": tr.tolist(), "test": te.tolist(), "n_train": int(len(tr)), "n_test": int(len(te))})

    manifest = {
        "task": "ln_co2",
        "n": len(panel),
        "groups": panel["iso"].nunique(),
        "cv_folds": 5,
        "split_seed": 42,
        "protocol_version": "1.0",
        "protocol_a_folds": folds,
        "protocol_b_folds": logo_folds,
        "output_path": str(out_path),
    }
    out_path.write_text(json.dumps(manifest, indent=2))
    print(f"saved split manifest: {out_path} ({len(panel)} rows, {panel['iso'].nunique()} groups)")
    return manifest


if __name__ == "__main__":
    save_splits()

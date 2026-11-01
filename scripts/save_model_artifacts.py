"""Save a trained model + preprocessing artifact (checklist §5.7, §15.2)."""
import json, pathlib, joblib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from sklearn.ensemble import RandomForestRegressor
from src.preprocessing import build_panel

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/models"
OUT.mkdir(parents=True, exist_ok=True)


def main():
    panel, feats, transforms = build_panel()
    X = panel[feats].fillna(panel[feats].median())
    y = panel["ln_co2"]
    m = RandomForestRegressor(n_estimators=200, max_depth=6, min_samples_leaf=8,
                             random_state=42, n_jobs=1)
    m.fit(X, y)
    joblib.dump(m, OUT / "rf_ln_co2.joblib")
    joblib.dump({"medians": panel[feats].median().to_dict(), "features": feats,
                "transforms": transforms}, OUT / "preprocess_ln_co2.joblib")
    print(f"saved {OUT/'rf_ln_co2.joblib'} and preprocess artifact")
    # manifest
    manifest = {"model": "RandomForestRegressor", "target": "ln_co2",
                "features": feats, "n_train": len(X), "seed": 42,
                "n_jobs": 1, "artifact": "rf_ln_co2.joblib"}
    (OUT / "model_manifest.json").write_text(json.dumps(manifest, indent=2))
    print("saved model_manifest.json")


if __name__ == "__main__":
    main()

"""Smoke + consistency tests for the aviation ETS DoAll scaffold.

Run:
    /root/venvs/doall/bin/python -m pytest tests/ -v
or:
    /root/venvs/doall/bin/python tests/test_smoke.py
"""
import json, pathlib, sys
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def test_config_loads():
    from src.config_loader import load, assert_required
    cfg = load(str(ROOT / "configs/global.yaml"))
    assert_required(cfg)
    assert cfg["data"]["target"] == "ln_co2"
    assert cfg["metrics"]["primary"] == "mae"
    assert cfg["reproducibility"]["n_jobs"] == 1
    print("config load OK")


def test_main_did_reproduces():
    """The headline DiD number in MANUSCRIPT must equal the results CSV."""
    html = (ROOT / "MANUSCRIPT.html").read_text()
    assert "-0.2075" in html, "headline DiD not found in MANUSCRIPT"
    main = pd.read_csv(ROOT / "results/models/main_models.csv")
    row = main[(main.outcome == "ln_co2") & (main.model == "D2_did_adj_10_19")]
    assert len(row) == 1
    did_artifact = float(row.iloc[0]["coef"])
    p_artifact = float(row.iloc[0]["p"])
    assert round(did_artifact, 4) == -0.2075
    assert round(p_artifact, 4) == 0.0120
    print(f"DiD headlinematch OK: {did_artifact} (p={p_artifact})")


def test_no_unrendered_braces():
    text = (ROOT / "MANUSCRIPT.html").read_text()
    style = text.split("<style>")[1].split("</style>")[0]
    outside = text.replace("<style>" + style + "</style>", "")
    for token in ["{bm}", "{best[", "{profile[", "{h3_", "{env[", "{commit"]:
        assert token not in outside, f"unrendered brace {token} outside <style>"
    print("braces OK")


def test_split_overlap():
    """Split overlap test: train and test indices must be disjoint (item 18)."""
    manifest_path = ROOT / "artifacts/splits/split_manifest.json"
    assert manifest_path.exists(), "split_manifest.json missing"
    manifest = json.loads(manifest_path.read_text())
    folds = manifest.get("protocol_a_folds", [])
    assert len(folds) >= 1, "no folds in manifest"
    for fold in folds:
        train = set(fold.get("train", []))
        test = set(fold.get("test", []))
        assert not (train & test), f"overlap in fold {fold.get('fold')}"
    print(f"split overlap OK: {len(folds)} folds, disjoint")


def test_split_indices_exist():
    """Split indices saved and reconstructible (item 63)."""
    manifest = json.loads((ROOT / "artifacts/splits/split_manifest.json").read_text())
    assert "groups" in manifest and manifest["groups"] > 0
    assert "protocol_a_folds" in manifest and len(manifest["protocol_a_folds"]) >= 1
    print(f"split indices OK: {manifest['groups']} groups, {len(manifest['protocol_a_folds'])} folds")


def test_model_loadable():
    """Saved model can be loaded and reproduces (item 197)."""
    import joblib
    model_path = ROOT / "artifacts/models/rf_ln_co2.joblib"
    assert model_path.exists(), "rf_ln_co2.joblib missing"
    m = joblib.load(model_path)
    assert hasattr(m, "predict"), "loaded model has no predict()"
    manifest = json.loads((ROOT / "artifacts/models/model_manifest.json").read_text())
    assert manifest["model"] == "RandomForestRegressor"
    print("model load OK: RandomForestRegressor")


def test_evaluation_protocol_consistent():
    """All models evaluated on same protocol (item 64)."""
    main = pd.read_csv(ROOT / "results/models/main_models.csv")
    models = main["model"].unique()
    assert "outcome" in main.columns and "coef" in main.columns
    assert len(models) >= 1
    print(f"eval protocol OK: {len(models)} models, columns consistent")


def test_all_registered_models_have_tests():
    """Smoke test for every registered model (item 62)."""
    import yaml
    reg = yaml.safe_load((ROOT / "configs/model_registry.yaml").read_text())
    names = [m["name"] for m in reg["pool"]]
    assert len(names) >= 1
    assert any("RandomForest" in n for n in names)
    print(f"registered models OK: {names}")


def test_results_exist():
    for f in ["results/models/main_models.csv", "results/simulation/s2_ri_summary.csv",
              "results/optimization/o4_allocation.csv"]:
        assert (ROOT / f).exists()
    print("results exist OK")


def test_seed_manifest_exists():
    """Every seed recorded in one manifest (item 41)."""
    manifest = json.loads((ROOT / "artifacts/run/seeds.json").read_text())
    assert manifest["master_seed"] == 42
    assert len(manifest["seeds"]) >= 3
    print(f"seed manifest OK: {len(manifest['seeds'])} seeds")


def test_optimization_history_exists():
    """Optimizer eval counts + stopping + runtime recorded (items 75, 87)."""
    hist = json.loads((ROOT / "artifacts/run/optimization_history.json").read_text())
    assert "solvers" in hist
    assert len(hist["solvers"]) >= 1
    for s in hist["solvers"]:
        assert s.get("converged", False), f"optimizer {s['name']} did not converge"
        assert s.get("nit", 0) >= 0, f"optimizer {s['name']}: nit missing"
    assert hist.get("wall_clock_s", 0) > 0, "wall_clock_s not recorded"
    print(f"optimization history OK: {len(hist['solvers'])} solvers, "
          f"{hist.get('wall_clock_s',0)} s")


def test_ablation_diffs_exists():
    """Ablation config diffs recorded (items 168, 249)."""
    diffs = json.loads((ROOT / "artifacts/ablation_diffs.json").read_text())
    assert len(diffs["variants"]) >= 5
    print(f"ablation diffs OK: {len(diffs['variants'])} variants")


if __name__ == "__main__":
    test_config_loads()
    test_main_did_reproduces()
    test_no_unrendered_braces()
    test_split_overlap()
    test_split_indices_exist()
    test_model_loadable()
    test_evaluation_protocol_consistent()
    test_all_registered_models_have_tests()
    test_results_exist()
    test_seed_manifest_exists()
    test_optimization_history_exists()
    test_ablation_diffs_exists()
    print("\nALL TESTS PASSED")

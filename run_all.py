#!/usr/bin/env python3
"""run_all.py — one-command reproducibility for the aviation ETS evidence package.

Usage:
    python run_all.py            # full offline pipeline (stages that need shipped data)
    python run_all.py --stage 05 # run a single numbered stage

Stages needing live network (13/13b jet-fuel fetch, download_eea_ets) are SKIPPED
by default: their outputs are shipped in data/ so the pipeline is reproducible
offline. Pass --fetch to attempt live downloads.

All scripts use repo-relative paths; no /root, no absolute paths.
"""
import subprocess, sys, argparse
from pathlib import Path

BASE = Path(__file__).resolve().parent
PY = sys.executable

OFFLINE = [
    "02_clean_build.py",
    "05_models_fixed.py",
    "05_reconcile.py",
    "06_ml_suite.py",
    "07_scm_suite.py",
    "08_simulation_suite.py",
    "09_optimization_suite.py",
    "10_tables_figures.py",
    "11_null_precision.py",
    "12_mechanism_pass_through.py",
    "14_fuel_crosscheck.py",
    "15_dose_response.py",
]
FETCH = ["13b_jetfuel_fetch_v2.py", "download_eea_ets.py"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", help="run only this stage number prefix, e.g. 05")
    ap.add_argument("--fetch", action="store_true", help="also run live network fetch stages")
    args = ap.parse_args()

    stages = OFFLINE + (FETCH if args.fetch else [])
    if args.stage:
        stages = [s for s in stages if s.startswith(args.stage)]
    if not stages:
        print(f"no stage matches '{args.stage}'")
        return 1

    for name in stages:
        print(f"\n{'='*70}\nRUNNING {name}\n{'='*70}", flush=True)
        r = subprocess.run([PY, str(BASE / "code" / name)], cwd=BASE)
        if r.returncode != 0:
            print(f"FAILED: {name} (exit {r.returncode}) — stopping pipeline.")
            return r.returncode

    # Post-analysis: environment capture, model artifacts, freeze manifest
    print(f"\n{'='*70}\nPOST: helper scripts\n{'='*70}", flush=True)
    helpers = [
        ("capture_environment", "scripts/capture_environment.py"),
        ("save_model_artifacts", "scripts/save_model_artifacts.py"),
        ("freeze_manifest", "scripts/freeze_manifest.py"),
        ("postprocess_results", "scripts/postprocess_results.py"),
    ]
    for label, rel in helpers:
        print(f"\n--- {label} ---", flush=True)
        r = subprocess.run([PY, str(BASE / rel)], cwd=BASE)
        if r.returncode != 0:
            print(f"FAILED: {label} (exit {r.returncode}) — stopping pipeline.")
            return r.returncode
    # verify_determinism is optional: needs two runs to compare
    det_dir1 = BASE / "results"
    det_dir2 = BASE / "results_prev"
    if det_dir2.exists():
        print("\n--- verify_determinism ---", flush=True)
        r = subprocess.run([PY, str(BASE / "scripts" / "verify_determinism.py"),
                           str(det_dir1), str(det_dir2)], cwd=BASE)
        if r.returncode != 0:
            print(f"FAILED: verify_determinism (exit {r.returncode}) — stopping pipeline.")
            return r.returncode
    else:
        print("\n--- verify_determinism: skipped (no results_prev/ to compare) ---", flush=True)

    print("\nPIPELINE COMPLETE — all stages exited 0. Results in results/, tables/, figures/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

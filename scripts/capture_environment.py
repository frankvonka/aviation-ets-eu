"""Capture environment snapshot for provenance (checklist §4.6, §15.3–15.6)."""
import sys, json, platform, importlib, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _git_available() -> bool:
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--is-inside-work-tree"],
                              capture_output=True, timeout=5).returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def main():
    from importlib.metadata import distributions
    pkgs = {}
    for d in distributions():
        name = d.metadata.get("Name")
        if name:
            pkgs[name.lower()] = d.version
    commit = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip() if _git_available() else "nongit"
    env = {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "os": platform.platform(),
        "machine": platform.machine(),
        "commit": commit,
        "n_jobs": 1,
        "deterministic": True,
        "captured_by": "scripts/capture_environment.py",
        "captured_at": __import__("datetime").datetime.now().isoformat(),
        "pinned_packages": {k: pkgs[k] for k in ["numpy", "pandas", "scipy",
            "scikit-learn", "statsmodels", "matplotlib"] if k in pkgs},
    }
    out = ROOT / "artifacts/logs/environment.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(env, indent=2))
    print(json.dumps(env, indent=2))

if __name__ == "__main__":
    main()

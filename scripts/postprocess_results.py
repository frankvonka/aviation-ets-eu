"""Postprocess: stamp run_id / protocol_version / git_commit on result CSVs (checklist §4.6, §15.3-15.6)."""
import subprocess, pathlib, hashlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main():
    try:
        commit = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        commit = "nongit"
    run_id = hashlib.sha1(commit.encode()).hexdigest()[:12]
    for sub in ["results/models", "results/mechanisms", "results/optimization",
                "results/simulation"]:
        d = ROOT / sub
        if not d.is_dir():
            continue
        for f in d.glob("*.csv"):
            lines = f.read_text().splitlines()
            if not lines or lines[0].startswith("run_id"):
                continue
            header = lines[0] + ",run_id,protocol_version,git_commit"
            body = [ln + f",{run_id},1.0,{commit[:12]}" for ln in lines[1:]]
            f.write_text("\n".join([header] + body) + "\n")
    print(f"stamped run_id={run_id} protocol=1.0 on result CSVs")
    # Record the stamp mapping for audit: which files got which stamp, when.
    import datetime
    stamp_log = {
        "run_id": run_id,
        "commit": commit[:12],
        "protocol_version": "1.0",
        "stamped_at": datetime.datetime.now().isoformat(),
        "files": [str(f) for sub in ["results/models", "results/mechanisms", "results/optimization",
                "results/simulation"] for f in (ROOT / sub).glob("*.csv")],
    }
    (ROOT / "artifacts/logs/stamp_log.json").write_text(
        __import__("json").dumps(stamp_log, indent=2))


if __name__ == "__main__":
    main()

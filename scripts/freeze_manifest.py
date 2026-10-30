#!/usr/bin/env python3
"""Freeze + recompute published-artifact hashes on every audit (DoAll §17.272).

Usage:
    /root/venvs/doall/bin/python scripts/freeze_manifest.py [--check]

Auto-discovers all CSV/JSON/PARQUET/TXT files under results/, tables/, figures/
and artifacts/logs/. Writes artifacts/freeze/freeze_manifest.json with fresh SHA256.
`--check` exits non-zero if any hash changed since the last freeze.
"""
import hashlib, json, pathlib, sys, datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
FREEZE = ROOT / "artifacts/freeze/freeze_manifest.json"
COMMIT = "65bb6e7"

# ponytail: expand as new artifacts are added; auto-discovers CSV/JSON/TXT/PARQUET
# under results/, tables/, figures/ and artifacts/logs/
DISCOVERY_DIRS = ["results", "tables", "figures", ROOT / "artifacts" / "logs"]

EXTENSIONS = {".csv", ".json", ".txt", ".parquet", ".png", ".html"}


def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def main():
    check = "--check" in sys.argv
    if FREEZE.exists():
        manifest = json.loads(FREEZE.read_text())
    else:
        manifest = {"items": [], "generated_at": None}

    # Build current items from discovery
    current = {}
    for d in DISCOVERY_DIRS:
        if isinstance(d, str):
            d = ROOT / d
        if not d.is_dir():
            continue
        for p in sorted(d.rglob("*")):
            if p.is_file() and p.suffix.lower() in EXTENSIONS:
                rel = p.relative_to(ROOT).as_posix()
                current[rel] = {"path": rel, "sha256": sha256(p)}

    # Merge with existing manifest items (preserve ids)
    by_path = {item["path"]: item for item in manifest["items"]}
    new_items = []
    changed = []
    for path, data in sorted(current.items()):
        if path in by_path:
            old_hash = by_path[path].get("sha256")
            item = dict(by_path[path])
            item["sha256"] = data["sha256"]
            if old_hash and old_hash != data["sha256"]:
                changed.append((path, old_hash[:8], data["sha256"][:8]))
            new_items.append(item)
        else:
            new_items.append({
                "id": f"freeze_{len(new_items)+1:03d}",
                "path": path,
                "sha256": data["sha256"],
                "source": "auto-discovered",
            })

    manifest["items"] = new_items
    manifest["recomputed"] = datetime.datetime.now().isoformat(timespec="seconds")
    manifest["git_commit"] = COMMIT
    manifest["n_items"] = len(new_items)
    manifest["discovery_dirs"] = [str(d) for d in DISCOVERY_DIRS]
    manifest["changed_since_last"] = len(changed)
    FREEZE.write_text(json.dumps(manifest, indent=2) + "\n")
    if check:
        if changed:
            print("FREEZE CHANGED:", changed)
            return 1
        print(f"freeze OK: {len(new_items)} artifacts hashed, 0 changed")
        return 0
    print(f"freeze written: {len(new_items)} artifacts hashed, {len(changed)} changed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

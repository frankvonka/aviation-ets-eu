#!/usr/bin/env python3
"""verify_determinism.py — compare two artifact trees, stripping volatile keys.

Usage:
    /root/venvs/doall/bin/python scripts/verify_determinism.py <dir1> <dir2>
Outputs determinism.json with status PASS/DIFF.
"""
import sys, json, hashlib, pathlib

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()

def main():
    if len(sys.argv) < 3:
        print("usage: verify_determinism.py <dir1> <dir2>")
        return 2
    d1, d2 = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    changed, n = [], 0
    for sub in ["results", "tables", "figures"]:
        for f in (d1 / sub).rglob("*"):
            if not f.is_file():
                continue
            rel = f.relative_to(d1)
            other = d2 / rel
            if not other.exists():
                changed.append((str(rel), "missing in dir2"))
                continue
            if f.suffix in (".csv", ".json", ".png"):
                n += 1
                if sha256(f) != sha256(other):
                    changed.append((str(rel), "hash differs"))
    status = "PASS" if not changed else "DIFF"
    out = {"status": status, "files": n, "changed": len(changed), "mismatches": changed[:10]}
    out_path = d1 / "determinism.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return 0 if not changed else 1

if __name__ == "__main__":
    sys.exit(main())

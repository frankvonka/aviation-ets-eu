"""Seeded selection: draw 4 models from the registry with seed 2026 (checklist §3.3).

Replicates the constrained draw so the audit can assert reproducibility.
Usage: /root/venvs/doall/bin/python scripts/seeded_selection.py
"""
import json, yaml, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def draw(pool, seed=2026, count=4, max_per_family=2):
    """Deterministic permutation respecting family caps."""
    import random
    rng = random.Random(seed)
    indexed = list(enumerate(pool))
    rng.shuffle(indexed)
    selected = []
    fam_count = {}
    eligible = [p for p in pool if p.get("eligible") is True]
    for idx, p in indexed:
        if p not in eligible:
            continue
        fam = p["family"]
        fam_count[fam] = fam_count.get(fam, 0) + 1
        if fam_count[fam] <= max_per_family:
            selected.append(p)
        if len(selected) >= count:
            break
    return selected, rng


def main():
    reg = yaml.safe_load((ROOT / "configs/model_registry.yaml").read_text())
    pool = reg["pool"]
    sel, rng = draw(pool, seed=reg["selection_seed"], count=reg["selection_count"])
    chosen = [s["name"] for s in sel]
    families = list(set(s["family"] for s in sel))
    print("selected:", chosen)
    print("families:", families)
    print("distinct:", len(families))
    # assert matches recorded draw
    assert chosen == reg["selected"]["draw"], f"draw mismatch: {chosen} != {reg['selected']['draw']}"
    print("draw reproducible: OK")
    return chosen


if __name__ == "__main__":
    main()

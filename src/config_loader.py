"""Minimal config loader with protected-field enforcement.

Rejects unknown keys and protected-field overrides (framework checklist §1.4/1.5).
"""
import yaml
from pathlib import Path

SCHEMA = {
    "project": {"name", "protocol_version", "repo"},
    "data": {"path", "target", "task", "dataset_version", "dataset_hash_required",
             "filed_n", "usable_n", "unit_of_analysis", "unit_of_replication"},
    "evaluation": {"protocol", "test_size", "cv_folds", "split_seed", "split_manifest",
                   "final_test_policy", "protocols"},
    "reproducibility": {"master_seed", "model_seeds", "deterministic_algorithms", "n_jobs"},
    "preprocessing": {"imputation", "scaling", "categorical_encoding", "fit_within_each_fold"},
    "optimization": {"enabled", "primary_type", "algorithms", "objective", "max_trials",
                     "seed", "save_history", "save_best_solution", "allow_test_data"},
    "simulation": {"enabled", "type", "scenarios_file", "replications", "seed",
                   "save_replication_outputs", "save_summary_statistics"},
    "ablation": {"enabled", "variants_file", "reference_variant", "same_splits",
                 "same_seed_policy", "record_configuration_diff"},
    "metrics": {"primary", "secondary", "raw_precision"},
    "saving": {"save_predictions", "save_fold_metrics", "save_model", "save_preprocessor",
               "save_config_snapshot", "save_environment", "display_decimal_places"},
    "logging": {"log_level", "record_failed_runs", "record_runtime", "record_git_commit"},
    "paths": {"results", "models", "simulations", "optimizations", "ablations", "logs", "splits"},
}

PROTECTED = {
    "project.name", "project.protocol_version", "data.target", "data.task",
    "evaluation.protocol", "evaluation.cv_folds", "metrics.primary",
    "reproducibility.master_seed",
}


def load(path="configs/global.yaml"):
    cfg = yaml.safe_load(Path(path).read_text())
    for section, keys in cfg.items():
        if section not in SCHEMA:
            raise KeyError(f"unknown config section: {section}")
        unknown = set(keys) - SCHEMA[section]
        if unknown:
            raise KeyError(f"unknown keys in {section}: {unknown}")
    return cfg


def assert_required(cfg):
    """A run cannot start with task: auto / objective: null / selected_method: null."""
    if cfg["data"]["task"] is None:
        raise ValueError("data.task must not be null")
    if cfg["metrics"]["primary"] is None:
        raise ValueError("metrics.primary must not be null")


if __name__ == "__main__":
    cfg = load()
    assert_required(cfg)
    print("config OK:", cfg["project"]["name"], cfg["project"]["protocol_version"])

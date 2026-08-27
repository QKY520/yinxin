#!/usr/bin/env python3
"""Validate and materialize the reviewer baseline experiment matrix.

M1 deliberately performs no model calls.  It creates deterministic run
specifications that later runners consume, while refusing test-informed tuning
and output collisions.  The existing A/B/C/D artifacts remain outside the
new output root and are never overwritten.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import hashlib
import json


DATASET_NAMES = ("domain", "cluener")
SEEDS = (42, 43, 44)
K_VALUES = (1, 5, 10)
NEW_K5_VARIANTS = ("zero_shot", "glossary_only", "bm25_only", "rag_only")
K_SCAN_VARIANTS = ("A", "D")
ALL_VARIANTS = NEW_K5_VARIANTS + ("bert_crf",) + K_SCAN_VARIANTS


@dataclass(frozen=True)
class RunSpec:
    dataset: str
    variant: str
    k: int
    seed: int
    support_path: str
    tune_path: str
    evaluation_path: str
    output_dir: str

    @property
    def run_id(self) -> str:
        return f"{self.dataset}_{self.variant.lower()}_k{self.k}_seed{self.seed}"


def _require_string(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def validate_manifest(manifest: Mapping[str, Any]) -> None:
    if manifest.get("gate") != "JISE_ECFSIE_REVIEW_BASELINE_EXPERIMENTS_APPROVED":
        raise ValueError("unexpected human gate")
    if manifest.get("task") != "ner":
        raise ValueError("reviewer baseline package is NER-only")
    datasets = manifest.get("datasets")
    if not isinstance(datasets, Mapping):
        raise ValueError("datasets must be a mapping")
    for name in DATASET_NAMES:
        block = datasets.get(name)
        if not isinstance(block, Mapping):
            raise ValueError(f"missing dataset block {name}")
        for key in ("support", "tune", "evaluation"):
            value = _require_string(block, key)
            if "test" in value.lower() and key != "evaluation":
                raise ValueError(f"test path cannot be used for {name}.{key}")
    policy = manifest.get("evaluation_policy")
    if not isinstance(policy, Mapping) or policy.get("test_is_read_only") is not True:
        raise ValueError("test_is_read_only must be true")
    if policy.get("tune_only_on_declared_tune_split") is not True:
        raise ValueError("tuning boundary is not locked")
    if tuple(manifest.get("seeds", ())) != SEEDS:
        raise ValueError("seeds must be exactly 42,43,44")
    if int(manifest.get("primary_k", -1)) != 5:
        raise ValueError("primary K must be 5")
    outputs = manifest.get("outputs")
    if not isinstance(outputs, Mapping) or outputs.get("no_overwrite_existing") is not True:
        raise ValueError("new outputs must refuse overwrite")


def build_run_specs(manifest: Mapping[str, Any]) -> list[RunSpec]:
    validate_manifest(manifest)
    datasets = manifest["datasets"]
    specs: list[RunSpec] = []
    for dataset in DATASET_NAMES:
        block = datasets[dataset]
        specs.extend(
            RunSpec(dataset, variant, 5, seed, block["support"], block["tune"], block["evaluation"], f"{manifest['outputs']['remote_root']}/{dataset}/{variant}/k5/seed{seed}")
            for variant in NEW_K5_VARIANTS + ("bert_crf",)
            for seed in SEEDS
        )
        specs.extend(
            RunSpec(dataset, variant, k, seed, block["support"], block["tune"], block["evaluation"], f"{manifest['outputs']['remote_root']}/{dataset}/{variant}/k{k}/seed{seed}")
            for variant in K_SCAN_VARIANTS
            for k in (1, 10)
            for seed in SEEDS
        )
    return specs


def manifest_sha256(manifest: Mapping[str, Any]) -> str:
    payload = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def write_run_manifest(manifest: Mapping[str, Any], path: str | Path) -> int:
    specs = build_run_specs(manifest)
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = [{"run_id": spec.run_id, **spec.__dict__} for spec in specs]
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump({"manifest_sha256": manifest_sha256(manifest), "runs": rows}, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return len(rows)


def load_yaml(path: str | Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required") from exc
    with Path(path).open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError("manifest must be a YAML mapping")
    return value


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(write_run_manifest(load_yaml(args.manifest), args.output))

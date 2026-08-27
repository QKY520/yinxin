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
import subprocess
import sys


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


def _schema_block() -> dict[str, Any]:
    return {
        "task": "ner",
        "entity_types": {
            "EQUIPMENT": "完整装备、武器平台、系统或型号名称。",
            "MODULE": "装备的部件、组件、子系统、传感器、载荷或功能模块。",
            "TECH_SCHEME": "技术体制、制导方式、作战/测试/改进方案或能力方案。",
            "METRIC": "数值指标、性能参数、射程、速度、重量、时间或数量表达。",
        },
        "relation_types": {},
    }


def build_qwen_baseline_config(
    spec: RunSpec,
    *,
    model_path: str = "/root/autodl-tmp/models/qwen2.5-7b",
    glossary_path: str = "/root/project/data/domain_dict.jsonl",
    rag_corpus_path: str | None = None,
    output_root: str | None = None,
) -> dict[str, Any]:
    """Build one locked Qwen config consumed by ``run_p3_extraction.py``.

    The config is deliberately not authorized here. A later bounded execution
    gate must set the execution fields and choose whether evaluation is allowed.
    """
    if spec.variant not in NEW_K5_VARIANTS:
        raise ValueError("Qwen materialization only supports the four new K=5 baselines")
    root = output_root or spec.output_dir
    config: dict[str, Any] = {
        "run_id": spec.run_id,
        "config_name": f"reviewer_{spec.dataset}_{spec.variant}_k{spec.k}_seed{spec.seed}",
        "execution": {
            "phase": "REVIEWER_BASELINE_PREP",
            "authorized": False,
            "human_gate": None,
            "model_calls_allowed": False,
            "gpu_required": True,
        },
        "data": {
            "dataset": spec.dataset,
            "support_path": spec.support_path,
            "query_path": spec.tune_path,
            "evaluation_path": spec.evaluation_path,
        },
        "schema": _schema_block(),
        "examples": {"mode": "none", "k": 0, "seed": spec.seed},
        "prompt": {
            "output_instruction": "只返回JSON,不要任何解释,不要markdown代码块",
            "retry_suffix": "只返回合法JSON",
        },
        "model": {
            "name": model_path,
            "base_url": "http://127.0.0.1:8000",
            "timeout_seconds": 300,
            "api_key": "EMPTY",
        },
        "generation": {"temperature": 0.0, "top_p": 1.0, "max_tokens": 768, "seed": spec.seed},
        "cache": {"dir": "/root/project/cache/reviewer_baselines_20260827"},
        "outputs": {
            "dry_run_prompts": f"{root}/dry_run_prompts.jsonl",
            "manifest": f"{root}/dry_run_manifest.json",
            "per_query": f"{root}/per_query.jsonl",
            "summary": f"{root}/summary.json",
        },
        "parsing": {"drop_invalid_entities": False},
    }
    if spec.variant == "glossary_only":
        config["glossary"] = {"path": glossary_path, "max_entries": 20, "match_mode": "substring"}
    elif spec.variant in {"bm25_only", "rag_only"}:
        if not rag_corpus_path:
            raise ValueError(f"{spec.variant} requires rag_corpus_path")
        config["rag"] = {
            "enabled": True,
            "mode": "bm25" if spec.variant == "bm25_only" else "bge_faiss_rerank",
            "corpus_path": rag_corpus_path,
            "top_k": 3,
            "retrieve_top_k": 20,
            "chunk_chars": 260,
            "overlap_chars": 40,
            "max_passage_chars": 300,
            "embedding": {"model_path": "/root/autodl-tmp/models/bge-m3", "device": "cuda"},
            "reranker": {"model_path": "/root/autodl-tmp/models/bge-reranker", "device": "cuda"},
        }
    return config


def materialize_b1_configs(
    manifest: Mapping[str, Any],
    output_dir: str | Path,
    *,
    yaml_writer: Any | None = None,
) -> list[Path]:
    """Write non-authorized B1 Qwen configs; never overwrites existing files."""
    specs = [s for s in build_run_specs(manifest) if s.variant in NEW_K5_VARIANTS]
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    corpus_by_dataset = {
        "domain": "/root/autodl-tmp/data/domain_rag_corpus.jsonl",
        "cluener": "/root/autodl-tmp/data/cluener_train_pool.jsonl",
    }
    paths: list[Path] = []
    try:
        import yaml
    except ImportError:
        raise RuntimeError("PyYAML is required to materialize runner configs")
    writer = yaml_writer or (lambda value, handle: yaml.safe_dump(value, handle, allow_unicode=True, sort_keys=False))
    for spec in specs:
        path = output / f"{spec.run_id}.yaml"
        if path.exists():
            raise FileExistsError(f"refusing to overwrite {path}")
        value = build_qwen_baseline_config(spec, rag_corpus_path=corpus_by_dataset[spec.dataset])
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            writer(value, handle)
        paths.append(path)
    return paths


def run_p3_config(config_path: str | Path, *, python_executable: str | None = None) -> int:
    """Execute one already-authorized Qwen config through the canonical runner."""
    command = [python_executable or sys.executable, str(Path(__file__).with_name("run_p3_extraction.py")), "--config", str(config_path)]
    return subprocess.run(command, check=False).returncode


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

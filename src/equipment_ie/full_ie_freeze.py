"""F5 protocol-freeze contract for the fixed 60-cell full-IE evaluation."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .full_ie_manifest import build_planned_manifest, expected_full_ie_cells, validate_full_ie_manifest


FREEZE_VERSION = "full-ie-f5-freeze-v1"
F5_GATE = "FULL_IE_F5_PROTOCOL_FREEZE_APPROVED"
FREEZE_STATUS = "FROZEN_NOT_AUTHORIZED"
SEEDS = (42, 43, 44)
K_VALUES = (1, 5, 10)
SOURCE_CONFIG = {
    "A": "A",
    "B": "B",
    "C": "C",
    "D": "D",
    "E": "D",
    "E-prime": "C",
}
P5_REUSED_STAGE_N_CONFIG_NAMES = {
    "A": "A_fixed_random_domain_test_p5_draft",
    "B": "B_knn_domain_test_p5_draft",
    "C": "C_knn_glossary_domain_test_p5_draft",
    "D": "D_knn_glossary_rag_domain_test_p5_draft",
}
FUTURE_GATES = {
    "domain": "FULL_IE_DOMAIN_FINAL_BATCH_APPROVED",
    "cluener": "FULL_IE_CLUENER_FINAL_BATCH_APPROVED",
}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

EXPECTED_RESOURCE_ROWS: dict[str, int | None] = {
    "domain_support": 30,
    "domain_test": 170,
    "domain_rag_corpus": 230,
    "domain_glossary": 73,
    "domain_frozen_marker": None,
    "domain_dedup_log": None,
    "cluener_dev": 1343,
    "cluener_support": 30,
    "cluener_glossary": 61,
    "cluener_rag_corpus": 9584,
    "cluener_rag_dedup_report": None,
    "model_file_manifest": 65,
    "model_manifest_metadata": 2,
}

REQUIRED_SOURCE_PATHS = (
    "AGENT_PLAYBOOK.md",
    "AGENTS.md",
    "configs/full_ie_f4a_domain_dev_r1_20260731/domain_a_stage_n.yaml",
    "configs/full_ie_f4a_domain_dev_r1_20260731/domain_a_stage_r.yaml",
    "configs/full_ie_f4a_domain_dev_r1_20260731/domain_b_stage_n.yaml",
    "configs/full_ie_f4a_domain_dev_r1_20260731/domain_b_stage_r.yaml",
    "configs/full_ie_f4a_domain_dev_r1_20260731/domain_c_stage_n.yaml",
    "configs/full_ie_f4a_domain_dev_r1_20260731/domain_c_stage_r.yaml",
    "configs/full_ie_f4a_domain_dev_r1_20260731/domain_d_stage_n.yaml",
    "configs/full_ie_f4a_domain_dev_r1_20260731/domain_d_stage_r.yaml",
    "configs/full_ie_f4a_domain_dev_r1_20260731/domain_e_verify.yaml",
    "configs/full_ie_f4a_domain_dev_r1_20260731/domain_eprime_verify.yaml",
    "configs/full_ie_f4a_domain_dev_r1_20260731/run_matrix.yaml",
    "configs/full_ie_f4b_cluener_tune_20260802/cluener_a_stage_n.yaml",
    "configs/full_ie_f4b_cluener_tune_20260802/cluener_b_stage_n.yaml",
    "configs/full_ie_f4b_cluener_tune_20260802/cluener_c_stage_n.yaml",
    "configs/full_ie_f4b_cluener_tune_20260802/cluener_d_stage_n.yaml",
    "configs/full_ie_f4b_cluener_tune_20260802/cluener_e_verify.yaml",
    "configs/full_ie_f4b_cluener_tune_20260802/cluener_eprime_verify.yaml",
    "configs/full_ie_f5_freeze_20260802/freeze_inputs.json",
    "refine-logs/FULL_IE_MINIMUM_EXPERIMENT_PLAN_20260730.md",
    "requirements.lock.txt",
    "scripts/prepare_full_ie_f5.py",
    "scripts/run_full_ie_verification.py",
    "scripts/run_p3_extraction.py",
    "scripts/run_stage_r.py",
    "scripts/validate_full_ie_f5.py",
    "src/equipment_ie/extraction.py",
    "src/equipment_ie/full_ie.py",
    "src/equipment_ie/full_ie_f3.py",
    "src/equipment_ie/full_ie_freeze.py",
    "src/equipment_ie/full_ie_manifest.py",
    "src/equipment_ie/llm_labeling.py",
    "src/equipment_ie/schema.py",
)

PER_QUERY_REQUIRED_FIELDS = (
    "id",
    "dataset",
    "config",
    "k",
    "seed",
    "gold",
    "pred_entities_stage_n",
    "pred_relations_stage_r",
    "pred_raw",
    "pred_verified",
    "ner_prompt_hash",
    "relation_prompt_hash",
    "verifier_prompt_hashes",
    "raw_ner_output_hash",
    "raw_relation_output_hash",
    "example_ids",
    "glossary_terms",
    "rag_passage_ids",
    "parse_failure_ner",
    "parse_failure_relation",
    "sanitization_flags",
    "verifier_decisions",
    "latency_ner_ms",
    "latency_relation_ms",
    "latency_verifier_ms",
)


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def nonempty_line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for line in handle if line.strip())


def _require_mapping(value: Any, *, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def _validate_file_lock(
    value: Any,
    *,
    label: str,
    expected_rows: int | None,
    verify_file: bool,
) -> dict[str, Any]:
    lock = _require_mapping(value, label=label)
    path_value = lock.get("path")
    digest = lock.get("sha256")
    rows = lock.get("rows")
    if not isinstance(path_value, str) or not Path(path_value).is_absolute():
        raise ValueError(f"{label}.path must be absolute")
    if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
        raise ValueError(f"{label}.sha256 must be lowercase SHA256")
    if rows != expected_rows:
        raise ValueError(f"{label}.rows must be {expected_rows!r}, found {rows!r}")
    role = lock.get("role")
    if not isinstance(role, str) or not role:
        raise ValueError(f"{label}.role must be non-empty")
    if verify_file:
        path = Path(path_value)
        if not path.is_file():
            raise ValueError(f"{label}: missing file {path}")
        actual = sha256_file(path)
        if actual != digest:
            raise ValueError(f"{label}: SHA256 mismatch for {path}")
        if expected_rows is not None and nonempty_line_count(path) != expected_rows:
            raise ValueError(f"{label}: row count changed for {path}")
    return dict(lock)


def _expected_reuse_cell_ids() -> set[str]:
    return {
        f"domain:{config}:k5:s{seed}"
        for config in ("A", "B", "C", "D")
        for seed in SEEDS
    }


def _load_jsonl_objects(path: Path, *, label: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{label}:{line_number}: invalid JSON") from exc
            if not isinstance(value, dict):
                raise ValueError(f"{label}:{line_number}: expected object")
            rows.append(value)
    return rows


def _verify_reused_stage_n_semantics(
    reused_stage_n: Sequence[Mapping[str, Any]],
    *,
    domain_test_path: Path,
) -> int:
    gold_rows = _load_jsonl_objects(domain_test_path, label="domain_test")
    gold_by_id: dict[str, dict[str, Any]] = {}
    for row in gold_rows:
        record_id = row.get("id")
        if not isinstance(record_id, str) or record_id in gold_by_id:
            raise ValueError("domain_test IDs must be unique strings")
        gold_by_id[record_id] = row
    if len(gold_by_id) != 170:
        raise ValueError("domain_test must contain 170 unique IDs")

    example_ids_by_cell: dict[str, dict[str, tuple[str, ...]]] = {}
    query_ids_by_cell: dict[str, set[str]] = {}
    fixed_a_examples: dict[str, tuple[str, ...]] = {}
    checked = 0
    for lock in reused_stage_n:
        cell_identifier = str(lock["cell_id"])
        parts = cell_identifier.split(":")
        if len(parts) != 4 or parts[0] != "domain" or parts[2] != "k5":
            raise ValueError(f"invalid reused Stage N cell ID {cell_identifier}")
        expected_config = parts[1]
        expected_seed = int(parts[3].removeprefix("s"))
        expected_legacy_config = P5_REUSED_STAGE_N_CONFIG_NAMES[expected_config]
        rows = _load_jsonl_objects(Path(str(lock["path"])), label=cell_identifier)
        if len(rows) != 170:
            raise ValueError(f"{cell_identifier}: expected 170 rows")
        examples_for_query: dict[str, tuple[str, ...]] = {}
        ids: set[str] = set()
        for row in rows:
            record_id = row.get("id")
            if not isinstance(record_id, str) or record_id in ids:
                raise ValueError(f"{cell_identifier}: row IDs must be unique strings")
            ids.add(record_id)
            if (
                row.get("dataset") != "domain_test"
                or row.get("config") != expected_legacy_config
                or row.get("k") != 5
                or row.get("seed") != expected_seed
            ):
                actual = (
                    row.get("dataset"),
                    row.get("config"),
                    row.get("k"),
                    row.get("seed"),
                )
                expected = (
                    "domain_test",
                    expected_legacy_config,
                    5,
                    expected_seed,
                )
                raise ValueError(
                    f"{cell_identifier}: per-query metadata {actual!r} != {expected!r}"
                )
            gold = row.get("gold")
            expected_gold = gold_by_id.get(record_id)
            if not isinstance(gold, Mapping) or expected_gold is None:
                raise ValueError(f"{cell_identifier}: missing aligned gold record")
            if canonical_sha256(gold) != canonical_sha256(expected_gold):
                raise ValueError(f"{cell_identifier}: gold record does not match domain_test")
            pred_raw = row.get("pred_raw")
            if not isinstance(pred_raw, Mapping) or pred_raw.get("id") != record_id:
                raise ValueError(f"{cell_identifier}: invalid pred_raw record")
            if pred_raw.get("text") != gold.get("text"):
                raise ValueError(f"{cell_identifier}: prediction text mismatch")
            if row.get("pred_verified") is not None:
                raise ValueError(f"{cell_identifier}: Stage N reuse must be unverified")
            if row.get("parse_failure") is not False:
                raise ValueError(f"{cell_identifier}: preserved P5 Stage N parse failure changed")
            for hash_field in ("prompt_hash", "raw_llm_output_hash"):
                digest = row.get(hash_field)
                if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
                    raise ValueError(f"{cell_identifier}: invalid {hash_field}")
            example_ids = row.get("example_ids")
            if not isinstance(example_ids, list) or len(example_ids) != 5:
                raise ValueError(f"{cell_identifier}: expected five demonstration IDs")
            normalized_examples = tuple(str(value) for value in example_ids)
            if len(set(normalized_examples)) != 5:
                raise ValueError(f"{cell_identifier}: demonstration IDs must be unique")
            examples_for_query[record_id] = normalized_examples
            for field in ("glossary_terms", "rag_passage_ids", "rag_passages", "sanitization_flags"):
                if not isinstance(row.get(field), list):
                    raise ValueError(f"{cell_identifier}: {field} must be a list")
            if expected_config in {"A", "B"} and row["glossary_terms"]:
                raise ValueError(f"{cell_identifier}: A/B may not inject glossary terms")
            if expected_config != "D" and (row["rag_passage_ids"] or row["rag_passages"]):
                raise ValueError(f"{cell_identifier}: only D may inject RAG evidence")
            if expected_config == "D" and (
                len(row["rag_passage_ids"]) != 3 or len(row["rag_passages"]) != 3
            ):
                raise ValueError(f"{cell_identifier}: D must retain exactly three RAG passages")
            checked += 1
        if ids != set(gold_by_id):
            raise ValueError(f"{cell_identifier}: query IDs do not match domain_test")
        example_ids_by_cell[cell_identifier] = examples_for_query
        query_ids_by_cell[cell_identifier] = ids
        if expected_config == "A":
            unique_example_sets = set(examples_for_query.values())
            if len(unique_example_sets) != 1:
                raise ValueError(f"{cell_identifier}: fixed-random examples changed by query")
            fixed_a_examples[cell_identifier] = next(iter(unique_example_sets))

    if len(set(fixed_a_examples.values())) != 3:
        raise ValueError("domain A seeds must preserve three distinct fixed-random sets")
    for seed in SEEDS:
        b = example_ids_by_cell[f"domain:B:k5:s{seed}"]
        for config in ("C", "D"):
            candidate = example_ids_by_cell[f"domain:{config}:k5:s{seed}"]
            if candidate != b:
                raise ValueError(f"domain {config} seed {seed} does not replay B demonstrations")
    if any(ids != set(gold_by_id) for ids in query_ids_by_cell.values()):
        raise ValueError("reused Stage N query sets diverge")
    return checked


def validate_freeze_inputs(
    inputs: Mapping[str, Any],
    *,
    verify_files: bool = False,
) -> dict[str, Any]:
    if inputs.get("freeze_version") != FREEZE_VERSION:
        raise ValueError(f"freeze_version must be {FREEZE_VERSION}")
    if inputs.get("approved_gate") != F5_GATE:
        raise ValueError(f"approved_gate must be {F5_GATE}")
    if inputs.get("freeze_date") != "2026-08-02":
        raise ValueError("freeze_date must be 2026-08-02")

    authorization = _require_mapping(inputs.get("authorization"), label="authorization")
    expected_authorization = {
        "gpu_required": False,
        "model_calls_allowed": False,
        "final_evaluation_allowed": False,
        "f6_allowed": False,
        "paper_edits_allowed": False,
        "github_sync_allowed": False,
    }
    if dict(authorization) != expected_authorization:
        raise ValueError("authorization does not match the bounded F5 gate")

    resources = _require_mapping(inputs.get("resources"), label="resources")
    if set(resources) != set(EXPECTED_RESOURCE_ROWS):
        raise ValueError("resources must match the exact F5 resource inventory")
    for key, expected_rows in EXPECTED_RESOURCE_ROWS.items():
        _validate_file_lock(
            resources[key],
            label=f"resources.{key}",
            expected_rows=expected_rows,
            verify_file=verify_files,
        )

    raw_reuse = inputs.get("reused_stage_n")
    if not isinstance(raw_reuse, list):
        raise ValueError("reused_stage_n must be a list")
    reuse_ids: set[str] = set()
    reuse_paths: set[str] = set()
    for index, raw in enumerate(raw_reuse):
        lock = _require_mapping(raw, label=f"reused_stage_n[{index}]")
        cell_identifier = lock.get("cell_id")
        if not isinstance(cell_identifier, str) or cell_identifier in reuse_ids:
            raise ValueError("reused_stage_n cell IDs must be unique strings")
        reuse_ids.add(cell_identifier)
        normalized = _validate_file_lock(
            lock,
            label=f"reused_stage_n[{index}]",
            expected_rows=170,
            verify_file=verify_files,
        )
        if normalized["path"] in reuse_paths:
            raise ValueError("reused_stage_n paths must be unique")
        reuse_paths.add(normalized["path"])
        if lock.get("artifact_kind") != "stage_n_per_query":
            raise ValueError("reused_stage_n artifact_kind must be stage_n_per_query")
    if reuse_ids != _expected_reuse_cell_ids():
        raise ValueError("reused_stage_n must contain the exact 12 domain A-D K=5 cells")
    semantic_rows = 0
    if verify_files:
        semantic_rows = _verify_reused_stage_n_semantics(
            [dict(item) for item in raw_reuse],
            domain_test_path=Path(str(resources["domain_test"]["path"])),
        )

    source_paths = inputs.get("source_paths")
    if not isinstance(source_paths, list) or any(not isinstance(path, str) for path in source_paths):
        raise ValueError("source_paths must be a string list")
    if len(source_paths) != len(set(source_paths)):
        raise ValueError("source_paths must be unique")
    if set(source_paths) != set(REQUIRED_SOURCE_PATHS):
        raise ValueError("source_paths do not match the fixed F5 source inventory")
    return {
        "resources": len(resources),
        "reused_stage_n": len(raw_reuse),
        "reused_stage_n_semantic_rows": semantic_rows,
        "source_paths": len(source_paths),
    }


def build_source_locks(repo_root: Path, source_paths: Sequence[str]) -> list[dict[str, str]]:
    locks: list[dict[str, str]] = []
    for relative in sorted(source_paths):
        path = repo_root / relative
        if not path.is_file():
            raise ValueError(f"missing frozen source file {relative}")
        locks.append({"path": relative, "sha256": sha256_file(path)})
    return locks


def _slug(config: str) -> str:
    return config.lower().replace("-", "")


def stage_n_node_id(dataset: str, source_config: str, k: int, seed: int) -> str:
    return f"stage-n:{dataset}:{source_config}:k{k}:s{seed}"


def stage_r_node_id(source_config: str, k: int, seed: int) -> str:
    return f"stage-r:domain:{source_config}:k{k}:s{seed}"


def verifier_node_id(dataset: str, config: str, k: int, seed: int) -> str:
    return f"verify:{dataset}:{config}:k{k}:s{seed}"


def _stage_n_contract(
    *,
    dataset: str,
    source_config: str,
    k: int,
    seed: int,
    reuse_lock: Mapping[str, Any] | None,
) -> dict[str, Any]:
    token = f"{dataset}_{_slug(source_config)}_k{k}_seed{seed}"
    if source_config == "A":
        example_mode = "fixed_random"
        example_dependency = None
    elif source_config == "B":
        example_mode = "knn_retrieval"
        example_dependency = None
    elif k == 5:
        example_mode = "knn_replay"
        example_dependency = stage_n_node_id(dataset, "B", k, seed)
    else:
        example_mode = "knn_retrieval"
        example_dependency = None
    uses_glossary = source_config in {"C", "D"}
    uses_rag = source_config == "D"
    if reuse_lock is None:
        action = "PLANNED_MODEL_CALL"
        per_query = f"/root/project/results/full_ie/final_v1/stages/stage_n/{token}_per_query.jsonl"
        artifact_sha256 = None
    else:
        action = "REUSE_LOCKED_ARTIFACT"
        per_query = str(reuse_lock["path"])
        artifact_sha256 = str(reuse_lock["sha256"])
    return {
        "node_id": stage_n_node_id(dataset, source_config, k, seed),
        "kind": "stage_n",
        "dataset": dataset,
        "source_config": source_config,
        "k": k,
        "seed": seed,
        "action": action,
        "artifact_sha256": artifact_sha256,
        "query_resource": "domain_test" if dataset == "domain" else "cluener_dev",
        "support_resource": "domain_support" if dataset == "domain" else "cluener_support",
        "example_mode": example_mode,
        "example_dependency": example_dependency,
        "glossary_resource": (
            ("domain_glossary" if dataset == "domain" else "cluener_glossary")
            if uses_glossary
            else None
        ),
        "rag_resource": (
            ("domain_rag_corpus" if dataset == "domain" else "cluener_rag_corpus")
            if uses_rag
            else None
        ),
        "parsing": {
            "mode": "proposal_stage_sanitize",
            "drop_invalid_entities": True,
            "retry_mode": "parser_error_aware_once",
        },
        "generation": {
            "temperature": 0.0,
            "top_p": 1.0,
            "max_tokens": 768,
            "seed": seed,
        },
        "per_query_path": per_query,
        "summary_path": (
            None
            if reuse_lock is not None
            else f"/root/project/results/full_ie/final_v1/stages/stage_n/{token}_summary.json"
        ),
        "cache_dir": (
            None
            if reuse_lock is not None
            else f"/root/project/cache/full_ie/final_v1/stage_n/{token}"
        ),
        "authorized": False,
        "model_calls_allowed": False,
    }


def _stage_r_contract(stage_n: Mapping[str, Any]) -> dict[str, Any]:
    source_config = str(stage_n["source_config"])
    k = int(stage_n["k"])
    seed = int(stage_n["seed"])
    token = f"domain_{_slug(source_config)}_k{k}_seed{seed}"
    return {
        "node_id": stage_r_node_id(source_config, k, seed),
        "kind": "stage_r",
        "dataset": "domain",
        "source_config": source_config,
        "k": k,
        "seed": seed,
        "input_stage_n_node": stage_n["node_id"],
        "prompt_version": "stage_r_same_sentence_v1",
        "metadata_replay": ["example_ids", "glossary_terms", "rag_passages"],
        "parsing": {
            "protocol_revision": "r1_drop_invalid_relation_units",
            "drop_invalid_relations": True,
            "retry_mode": "parser_error_aware_once",
        },
        "generation": {
            "temperature": 0.0,
            "top_p": 1.0,
            "max_tokens": 768,
            "seed": seed,
        },
        "per_query_path": f"/root/project/results/full_ie/final_v1/stages/stage_r/{token}_per_query.jsonl",
        "summary_path": f"/root/project/results/full_ie/final_v1/stages/stage_r/{token}_summary.json",
        "cache_dir": f"/root/project/cache/full_ie/final_v1/stage_r/{token}",
        "authorized": False,
        "model_calls_allowed": False,
    }


def _verifier_contract(
    *,
    dataset: str,
    config: str,
    k: int,
    seed: int,
    input_node: str,
) -> dict[str, Any]:
    token = f"{dataset}_{_slug(config)}_k{k}_seed{seed}"
    return {
        "node_id": verifier_node_id(dataset, config, k, seed),
        "kind": "verification",
        "dataset": dataset,
        "config": config,
        "source_config": SOURCE_CONFIG[config],
        "k": k,
        "seed": seed,
        "input_node": input_node,
        "unit_kinds": ["entity", "relation"] if dataset == "domain" else ["entity"],
        "evidence_mode": "reuse_source_rag_passages" if config == "E" else "source_text_only",
        "prompt_version": "full_ie_atomic_source_first_v1",
        "decision_policy": "drop_only_valid_no_keep_invalid",
        "type_gate_enabled": False,
        "generation": {
            "temperature": 0.0,
            "top_p": 1.0,
            "max_tokens": 8,
            "seed": seed,
        },
        "per_query_path": f"/root/project/results/full_ie/final_v1/stages/verification/{token}_per_query.jsonl",
        "summary_path": f"/root/project/results/full_ie/final_v1/stages/verification/{token}_summary.json",
        "cache_dir": f"/root/project/cache/full_ie/final_v1/verification/{token}",
        "authorized": False,
        "model_calls_allowed": False,
    }


def _protocol_contract() -> dict[str, Any]:
    return {
        "matrix": {
            "datasets": ["domain", "cluener"],
            "configs_k5": ["A", "B", "C", "D", "E", "E-prime"],
            "configs_k_scan": ["A", "E"],
            "k_values": list(K_VALUES),
            "seeds": list(SEEDS),
            "reported_cells": 60,
        },
        "model": {
            "name": "Qwen2.5-7B-Instruct",
            "path": "/root/autodl-tmp/models/qwen2.5-7b",
            "dtype": "float16",
            "server": "vLLM",
            "temperature": 0.0,
            "top_p": 1.0,
        },
        "retrieval": {
            "embedding": "BGE-M3 normalized vectors",
            "index": "FAISS inner product",
            "retrieve_top_k": 20,
            "reranker": "bge-reranker-v2-m3",
            "rerank_top_k": 3,
            "rag_chunk_chars": 260,
            "rag_overlap_chars": 40,
            "max_passage_chars": 300,
            "glossary_max_entries": 20,
        },
        "stage_r": {
            "same_sentence_only": True,
            "entity_array_immutable": True,
            "directed_relation_types": ["USES", "HAS_METRIC", "PART_OF"],
            "prompt_version": "stage_r_same_sentence_v1",
            "parser_revision": "r1_drop_invalid_relation_units",
            "drop_invalid_relations": True,
        },
        "verification": {
            "configs": {"E": "D", "E-prime": "C"},
            "prompt_version": "full_ie_atomic_source_first_v1",
            "policy": "original_atomic_valid_no_deletion_only",
            "type_gate_enabled": False,
            "invalid_output_policy": "keep",
            "entity_drop_cascades_relations": True,
            "positive_claim_drop_precision_threshold": 0.70,
            "f4b_observed_drop_precision": {"E": 25 / 36, "E-prime": 25 / 38},
            "current_positive_cove_claim_supported": False,
            "negative_and_mixed_rows_retained": True,
        },
        "metrics": {
            "entity_primary": "exact_span_type_micro_precision_recall_f1",
            "relation_primary": "end_to_end_exact_directed_triple_micro_precision_recall_f1",
            "relation_key": [
                "head_start",
                "head_end",
                "head_type",
                "relation_type",
                "tail_start",
                "tail_end",
                "tail_type",
            ],
            "required_diagnostics": [
                "tp_fp_fn",
                "false_discovery_rate",
                "per_type_metrics",
                "gold_endpoint_coverage",
                "conditional_relation_accuracy",
                "zero_gold_predictions",
                "parse_failure_rate",
                "retry_count",
                "latency",
                "sanitizer_counts",
                "verification_drop_audit",
            ],
        },
        "aggregation": {
            "seed_summary": "mean_and_sample_standard_deviation",
            "paired_bootstrap_replicates": 10000,
            "paired_unit": "passage",
            "primary_contrasts": ["B-A", "C-B", "D-C", "E-D"],
            "secondary_contrasts": ["E-prime-C", "E-E-prime"],
            "multiple_comparison": "Holm adjustment when p-values are used",
        },
        "per_query_required_fields": list(PER_QUERY_REQUIRED_FIELDS),
        "failure_policy": {
            "no_test_informed_change": True,
            "preserve_all_negative_rows": True,
            "parse_failure_counts_as_empty_prediction": True,
            "official_cluener_test_unused": True,
            "paper_changes_require_separate_gate": True,
        },
    }


def build_freeze_manifest(
    inputs: Mapping[str, Any],
    *,
    source_locks: Sequence[Mapping[str, str]],
) -> dict[str, Any]:
    validate_freeze_inputs(inputs)
    source_lock_map: dict[str, str] = {}
    for index, raw in enumerate(source_locks):
        lock = _require_mapping(raw, label=f"source_locks[{index}]")
        path = lock.get("path")
        digest = lock.get("sha256")
        if not isinstance(path, str) or path in source_lock_map:
            raise ValueError("source lock paths must be unique strings")
        if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
            raise ValueError("source lock SHA256 must be lowercase")
        source_lock_map[path] = digest
    if set(source_lock_map) != set(REQUIRED_SOURCE_PATHS):
        raise ValueError("source locks do not match the fixed F5 source inventory")

    resources = {key: dict(value) for key, value in inputs["resources"].items()}
    reuse_by_cell = {item["cell_id"]: dict(item) for item in inputs["reused_stage_n"]}
    expected_cells = expected_full_ie_cells()

    stage_n_nodes: dict[str, dict[str, Any]] = {}
    for cell in expected_cells:
        dataset = str(cell["dataset"])
        source_config = SOURCE_CONFIG[str(cell["config"])]
        k = int(cell["k"])
        seed = int(cell["seed"])
        node_identifier = stage_n_node_id(dataset, source_config, k, seed)
        if node_identifier not in stage_n_nodes:
            reuse_lock = reuse_by_cell.get(
                f"{dataset}:{source_config}:k{k}:s{seed}"
            )
            stage_n_nodes[node_identifier] = _stage_n_contract(
                dataset=dataset,
                source_config=source_config,
                k=k,
                seed=seed,
                reuse_lock=reuse_lock,
            )

    stage_r_nodes = {
        stage_r_node_id(str(node["source_config"]), int(node["k"]), int(node["seed"])): _stage_r_contract(node)
        for node in stage_n_nodes.values()
        if node["dataset"] == "domain"
    }

    verifier_nodes: dict[str, dict[str, Any]] = {}
    for cell in expected_cells:
        config = str(cell["config"])
        if config not in {"E", "E-prime"}:
            continue
        dataset = str(cell["dataset"])
        k = int(cell["k"])
        seed = int(cell["seed"])
        source_config = SOURCE_CONFIG[config]
        input_node = (
            stage_r_node_id(source_config, k, seed)
            if dataset == "domain"
            else stage_n_node_id(dataset, source_config, k, seed)
        )
        node = _verifier_contract(
            dataset=dataset,
            config=config,
            k=k,
            seed=seed,
            input_node=input_node,
        )
        verifier_nodes[node["node_id"]] = node

    run_manifest = build_planned_manifest()
    for cell in run_manifest["cells"]:
        identifier = str(cell["cell_id"])
        dataset = str(cell["dataset"])
        config = str(cell["config"])
        k = int(cell["k"])
        seed = int(cell["seed"])
        source_config = SOURCE_CONFIG[config]
        stage_n_id = stage_n_node_id(dataset, source_config, k, seed)
        stage_r_id = stage_r_node_id(source_config, k, seed) if dataset == "domain" else None
        verify_id = (
            verifier_node_id(dataset, config, k, seed)
            if config in {"E", "E-prime"}
            else None
        )
        token = f"{dataset}_{_slug(config)}_k{k}_seed{seed}"
        execution = {
            "report_cell_id": identifier,
            "config_id": f"full-ie-final-v1-{dataset}-{_slug(config)}-k{k}-seed{seed}",
            "source_config": source_config,
            "stage_n_node": stage_n_id,
            "stage_r_node": stage_r_id,
            "verification_node": verify_id,
            "final_per_query_path": f"/root/project/results/full_ie/final_v1/cells/{token}_per_query.jsonl",
            "final_summary_path": f"/root/project/results/full_ie/final_v1/cells/{token}_summary.json",
            "required_future_gate": FUTURE_GATES[dataset],
            "authorized": False,
            "model_calls_allowed": False,
        }
        cell["execution"] = execution
        cell["config_contract_sha256"] = canonical_sha256(execution)
        reuse_lock = reuse_by_cell.get(identifier)
        if reuse_lock is not None:
            cell["status"] = "STAGE_N_DONE"
            cell["stage_n"] = {
                "status": "DONE",
                "artifact_sha256": reuse_lock["sha256"],
            }

    manifest = {
        "freeze_version": FREEZE_VERSION,
        "freeze_date": "2026-08-02",
        "approved_gate": F5_GATE,
        "status": FREEZE_STATUS,
        "authorization": dict(inputs["authorization"]),
        "resources": resources,
        "reused_stage_n": [dict(item) for item in inputs["reused_stage_n"]],
        "source_locks": [
            {"path": path, "sha256": source_lock_map[path]}
            for path in sorted(source_lock_map)
        ],
        "protocol_contract": _protocol_contract(),
        "execution_nodes": {
            "stage_n": list(stage_n_nodes.values()),
            "stage_r": list(stage_r_nodes.values()),
            "verification": list(verifier_nodes.values()),
        },
        "run_manifest": run_manifest,
        "claim_boundary": {
            "current_result_to_claim": "partial",
            "positive_cove_claim": False,
            "public_generalization_claim": False,
            "full_ie_claim": False,
            "matrix_complete_cells": 0,
            "note": "F5 freezes evaluation only; it creates no model result.",
        },
        "future_sequence": ["F6_REPLAY_PREP", "F7_DOMAIN_BATCHES", "F8_CLUENER_BATCHES", "F9_AGGREGATION_RESULT_TO_CLAIM"],
    }
    validate_freeze_manifest(manifest)
    return manifest


def _validate_source_locks(
    raw_locks: Any,
    *,
    repo_root: Path | None,
    verify_files: bool,
) -> None:
    if not isinstance(raw_locks, list):
        raise ValueError("source_locks must be a list")
    seen: dict[str, str] = {}
    for index, raw in enumerate(raw_locks):
        lock = _require_mapping(raw, label=f"source_locks[{index}]")
        path = lock.get("path")
        digest = lock.get("sha256")
        if not isinstance(path, str) or path in seen:
            raise ValueError("source lock paths must be unique strings")
        if not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None:
            raise ValueError("source lock SHA256 must be lowercase")
        seen[path] = digest
        if verify_files:
            if repo_root is None:
                raise ValueError("repo_root is required to verify source locks")
            actual_path = repo_root / path
            if not actual_path.is_file() or sha256_file(actual_path) != digest:
                raise ValueError(f"source lock mismatch for {path}")
    if set(seen) != set(REQUIRED_SOURCE_PATHS):
        raise ValueError("source locks do not match the fixed F5 source inventory")


def validate_freeze_manifest(
    manifest: Mapping[str, Any],
    *,
    repo_root: Path | None = None,
    verify_files: bool = False,
) -> dict[str, Any]:
    if manifest.get("freeze_version") != FREEZE_VERSION:
        raise ValueError(f"freeze_version must be {FREEZE_VERSION}")
    if manifest.get("freeze_date") != "2026-08-02":
        raise ValueError("freeze_date must be 2026-08-02")
    if manifest.get("approved_gate") != F5_GATE or manifest.get("status") != FREEZE_STATUS:
        raise ValueError("manifest gate/status does not represent the F5 freeze")

    authorization = _require_mapping(manifest.get("authorization"), label="authorization")
    if any(authorization.values()):
        raise ValueError("F5 manifest must not authorize any execution or later phase")

    resources = _require_mapping(manifest.get("resources"), label="resources")
    if set(resources) != set(EXPECTED_RESOURCE_ROWS):
        raise ValueError("manifest resources do not match the fixed inventory")
    for key, expected_rows in EXPECTED_RESOURCE_ROWS.items():
        _validate_file_lock(
            resources[key],
            label=f"resources.{key}",
            expected_rows=expected_rows,
            verify_file=verify_files,
        )

    reuse_inputs = {
        "freeze_version": FREEZE_VERSION,
        "approved_gate": F5_GATE,
        "freeze_date": "2026-08-02",
        "authorization": dict(authorization),
        "resources": dict(resources),
        "reused_stage_n": manifest.get("reused_stage_n"),
        "source_paths": list(REQUIRED_SOURCE_PATHS),
    }
    validate_freeze_inputs(reuse_inputs, verify_files=verify_files)
    _validate_source_locks(
        manifest.get("source_locks"),
        repo_root=repo_root,
        verify_files=verify_files,
    )

    protocol = _require_mapping(manifest.get("protocol_contract"), label="protocol_contract")
    verification = _require_mapping(protocol.get("verification"), label="protocol_contract.verification")
    if verification.get("policy") != "original_atomic_valid_no_deletion_only":
        raise ValueError("verification policy changed after F4")
    if verification.get("type_gate_enabled") is not False:
        raise ValueError("type-gated verification is not part of the frozen main matrix")
    if verification.get("current_positive_cove_claim_supported") is not False:
        raise ValueError("F5 may not create a positive CoVe claim")
    stage_r_protocol = _require_mapping(protocol.get("stage_r"), label="protocol_contract.stage_r")
    if stage_r_protocol.get("parser_revision") != "r1_drop_invalid_relation_units":
        raise ValueError("Stage R must freeze the sole F4a r1 parser revision")
    if stage_r_protocol.get("drop_invalid_relations") is not True:
        raise ValueError("Stage R must retain proposal-stage relation sanitization")

    run_manifest = _require_mapping(manifest.get("run_manifest"), label="run_manifest")
    run_report = validate_full_ie_manifest(run_manifest)
    if run_report["status_counts"] != {"PLANNED": 48, "STAGE_N_DONE": 12}:
        raise ValueError("F5 accounting must remain 12 Stage N partial and 48 planned")

    execution_nodes = _require_mapping(manifest.get("execution_nodes"), label="execution_nodes")
    expected_node_counts = {"stage_n": 48, "stage_r": 24, "verification": 24}
    node_maps: dict[str, dict[str, Mapping[str, Any]]] = {}
    output_paths: set[str] = set()
    cache_paths: set[str] = set()
    for kind, expected_count in expected_node_counts.items():
        raw_nodes = execution_nodes.get(kind)
        if not isinstance(raw_nodes, list) or len(raw_nodes) != expected_count:
            raise ValueError(f"execution_nodes.{kind} must contain {expected_count} nodes")
        node_map: dict[str, Mapping[str, Any]] = {}
        for index, raw in enumerate(raw_nodes):
            node = _require_mapping(raw, label=f"execution_nodes.{kind}[{index}]")
            identifier = node.get("node_id")
            if not isinstance(identifier, str) or identifier in node_map:
                raise ValueError(f"execution_nodes.{kind} node IDs must be unique")
            if node.get("authorized") is not False or node.get("model_calls_allowed") is not False:
                raise ValueError(f"{identifier}: frozen node must not authorize model calls")
            node_map[identifier] = node
            for field in ("per_query_path", "summary_path"):
                path = node.get(field)
                if path is None:
                    continue
                if not isinstance(path, str) or path in output_paths:
                    raise ValueError(f"duplicate or invalid node output path {path!r}")
                output_paths.add(path)
            cache_dir = node.get("cache_dir")
            if cache_dir is not None:
                if not isinstance(cache_dir, str) or cache_dir in cache_paths:
                    raise ValueError(f"duplicate or invalid cache path {cache_dir!r}")
                cache_paths.add(cache_dir)
        node_maps[kind] = node_map

    stage_n_nodes = node_maps["stage_n"]
    if sum(node.get("action") == "REUSE_LOCKED_ARTIFACT" for node in stage_n_nodes.values()) != 12:
        raise ValueError("exactly 12 Stage N nodes must reuse P5 artifacts")
    if sum(node.get("action") == "PLANNED_MODEL_CALL" for node in stage_n_nodes.values()) != 36:
        raise ValueError("exactly 36 Stage N nodes must remain planned")
    for node in stage_n_nodes.values():
        dependency = node.get("example_dependency")
        if dependency is not None and dependency not in stage_n_nodes:
            raise ValueError(f"{node['node_id']}: missing example replay dependency")
    for node in node_maps["stage_r"].values():
        if node.get("input_stage_n_node") not in stage_n_nodes:
            raise ValueError(f"{node['node_id']}: missing Stage N dependency")
        parsing = _require_mapping(node.get("parsing"), label=f"{node['node_id']}.parsing")
        if parsing.get("drop_invalid_relations") is not True:
            raise ValueError(f"{node['node_id']}: relation sanitizer must remain enabled")
    all_prediction_nodes = set(stage_n_nodes) | set(node_maps["stage_r"])
    for node in node_maps["verification"].values():
        if node.get("input_node") not in all_prediction_nodes:
            raise ValueError(f"{node['node_id']}: missing verifier input dependency")
        if node.get("type_gate_enabled") is not False:
            raise ValueError(f"{node['node_id']}: type gate must remain disabled")

    config_ids: set[str] = set()
    final_paths: set[str] = set()
    for cell in run_manifest["cells"]:
        execution = _require_mapping(cell.get("execution"), label=f"{cell['cell_id']}.execution")
        config_id = execution.get("config_id")
        if not isinstance(config_id, str) or config_id in config_ids:
            raise ValueError("all 60 final config IDs must be unique")
        config_ids.add(config_id)
        if execution.get("report_cell_id") != cell["cell_id"]:
            raise ValueError(f"{cell['cell_id']}: report_cell_id mismatch")
        if execution.get("authorized") is not False or execution.get("model_calls_allowed") is not False:
            raise ValueError(f"{cell['cell_id']}: final config is not execution-authorized")
        if execution.get("required_future_gate") != FUTURE_GATES[cell["dataset"]]:
            raise ValueError(f"{cell['cell_id']}: wrong future gate")
        if execution.get("stage_n_node") not in stage_n_nodes:
            raise ValueError(f"{cell['cell_id']}: missing Stage N node")
        stage_r_node = execution.get("stage_r_node")
        if cell["dataset"] == "domain":
            if stage_r_node not in node_maps["stage_r"]:
                raise ValueError(f"{cell['cell_id']}: missing Stage R node")
        elif stage_r_node is not None:
            raise ValueError(f"{cell['cell_id']}: CLUENER must not reference Stage R")
        verifier_node = execution.get("verification_node")
        if cell["config"] in {"E", "E-prime"}:
            if verifier_node not in node_maps["verification"]:
                raise ValueError(f"{cell['cell_id']}: missing verifier node")
        elif verifier_node is not None:
            raise ValueError(f"{cell['cell_id']}: non-verifier config references verifier")
        for field in ("final_per_query_path", "final_summary_path"):
            path = execution.get(field)
            if not isinstance(path, str) or path in final_paths or path in output_paths:
                raise ValueError(f"duplicate or invalid final output path {path!r}")
            final_paths.add(path)
        if cell.get("config_contract_sha256") != canonical_sha256(execution):
            raise ValueError(f"{cell['cell_id']}: config contract hash mismatch")

    claim_boundary = _require_mapping(manifest.get("claim_boundary"), label="claim_boundary")
    if claim_boundary.get("matrix_complete_cells") != 0:
        raise ValueError("F5 must not count any complete final cell")
    if any(
        claim_boundary.get(field) is not False
        for field in ("positive_cove_claim", "public_generalization_claim", "full_ie_claim")
    ):
        raise ValueError("F5 must not promote an unsupported result claim")
    return {
        "freeze_version": FREEZE_VERSION,
        "status": FREEZE_STATUS,
        "cells": run_report["cells"],
        "domain_cells": run_report["domain_cells"],
        "cluener_cells": run_report["cluener_cells"],
        "complete_cells": 0,
        "stage_n_done_cells": 12,
        "planned_cells": 48,
        "stage_n_nodes": len(stage_n_nodes),
        "stage_n_reused": 12,
        "stage_n_planned": 36,
        "stage_r_nodes": len(node_maps["stage_r"]),
        "verification_nodes": len(node_maps["verification"]),
        "source_locks": len(manifest["source_locks"]),
        "resource_locks": len(resources),
        "unique_config_ids": len(config_ids),
        "unique_final_output_paths": len(final_paths),
        "model_calls_allowed": False,
        "gpu_required": False,
    }

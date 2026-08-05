#!/usr/bin/env python3
"""Prepare the authorized 12-cell CLUENER public-NER execution package."""

from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.full_ie_freeze import canonical_sha256, sha256_file  # noqa: E402
from equipment_ie.schema import iter_jsonl  # noqa: E402


GATE = "NER_PUBLIC_CLUENER_ABCD_K5_FINAL_APPROVED"
PHASE = "NER_PUBLIC_CLUENER_FINAL"
FREEZE_MANIFEST_SHA256 = (
    "592949022da8fa0743ce821efc8dae9deac22825eeb2b9b2c230f9390422237e"
)
FREEZE_CANONICAL_SHA256 = (
    "e7187f5607b2b9f4e351ea45bb41902304e7049b99d80fc6bcd5fa4ef50258ae"
)
EXPECTED_RESOURCE_HASHES = {
    "cluener_dev": "f452c4199fd4b0656b05e0070aea2f00190a127ff3cd7d29e5760605e5260a5e",
    "cluener_support": "abd6a338bf393426f35e12a08d073c6661e59131bc52ae77ca9f96d8859a5219",
    "cluener_glossary": "0ac4dc41ceb9c458250354fef3826c8b21a9d128c9491a6477b2171f03ba3a9b",
    "cluener_rag_corpus": "f0b0cef66415bff65537076d1ab16552038dcb4388ed22c133255057ac2eb7ee",
}
REPLAY_MANIFEST_SHA256 = (
    "36a529b9cd8cd0a78d2438376885263d5b9d63cb4967a0e88ad50eedbdffb455"
)
REPLAY_ROWS_SHA256 = (
    "ba592a229ee96f32538a4b2a44b82b3149a8b02a9db0130c7380c32efc80c262"
)
F6_BACKUP_MANIFEST_SHA256 = (
    "e098c138c201fdc1e0804183da5eb97e1d6e8208fb2abd5b20d27adcb18f2947"
)
UPSTREAM_RUNNER_SHA256 = (
    "c5603e71e16382d437673c5da35b1109219b5d34dc13aa7d05c27f07e2bb5361"
)
VARIANTS = "ABCD"
SEEDS = (42, 43, 44)
CELL_ORDER = tuple(
    f"cluener:{variant}:k5:s{seed}" for seed in SEEDS for variant in VARIANTS
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze-manifest", required=True)
    parser.add_argument("--freeze-report", required=True)
    parser.add_argument("--template-dir", required=True)
    parser.add_argument("--replay-manifest", required=True)
    parser.add_argument("--replay-rows", required=True)
    parser.add_argument("--f6-backup-manifest", required=True)
    parser.add_argument("--runner", required=True)
    parser.add_argument("--upstream-runner", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--base-commit", required=True)
    parser.add_argument("--paid-preflight-at", required=True)
    parser.add_argument("--hourly-price-cny", required=True, type=float)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def load_yaml(path: Path) -> dict[str, Any]:
    import yaml

    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected YAML object")
    return value


def yaml_bytes(value: Mapping[str, Any]) -> bytes:
    import yaml

    return yaml.safe_dump(
        dict(value), allow_unicode=True, sort_keys=False, width=100
    ).encode("utf-8")


def json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def write_exclusive(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def count_jsonl(path: Path) -> int:
    return sum(1 for _ in iter_jsonl(path, validate=False))


def require_hash(path: Path, expected: str, label: str) -> None:
    observed = sha256_file(path)
    if observed != expected:
        raise ValueError(f"{label} SHA256 mismatch: {observed} != {expected}")


def validate_replay(path: Path) -> dict[str, Any]:
    replay = load_json(path)
    rows = replay.get("rows")
    if not isinstance(rows, list) or len(rows) != 1343:
        raise ValueError("F6 replay must contain exactly 1343 rows")
    seen: set[str] = set()
    passage_count = 0
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("F6 replay row must be an object")
        record_id = row.get("id")
        passages = row.get("selected_passages")
        if not isinstance(record_id, str) or not record_id or record_id in seen:
            raise ValueError("F6 replay IDs must be unique non-empty strings")
        if not isinstance(passages, list) or len(passages) != 3:
            raise ValueError(f"{record_id}: F6 replay must retain exactly top-3 passages")
        seen.add(record_id)
        passage_count += len(passages)
    if passage_count != 4029:
        raise ValueError(f"F6 replay passage count changed: {passage_count}")
    return {"rows": len(rows), "passages": passage_count}


def validate_template(template: Mapping[str, Any], variant: str) -> None:
    if template.get("config_name") != variant:
        raise ValueError(f"{variant}: template config_name mismatch")
    if template.get("schema", {}).get("task") != "ner":
        raise ValueError(f"{variant}: template task must be NER")
    if template.get("schema", {}).get("relation_types") != {}:
        raise ValueError(f"{variant}: relation schema must remain empty")
    if len(template.get("schema", {}).get("entity_types", {})) != 10:
        raise ValueError(f"{variant}: expected 10 CLUENER entity types")
    if template.get("prompt", {}).get("output_instruction") != "只返回JSON,不要任何解释,不要markdown代码块":
        raise ValueError(f"{variant}: output instruction changed")
    if template.get("prompt", {}).get("retry_suffix") != "只返回合法JSON":
        raise ValueError(f"{variant}: retry suffix changed")
    model = template.get("model", {})
    if model.get("name") != "/root/autodl-tmp/models/qwen2.5-7b":
        raise ValueError(f"{variant}: model path changed")


def output_paths(root: Path, variant: str, seed: int) -> dict[str, Path]:
    slug = f"cluener_{variant.lower()}_k5_seed{seed}"
    return {
        "per_query": root / "results" / f"{slug}_per_query.jsonl",
        "summary": root / "results" / f"{slug}_summary.json",
        "dry_run_prompts": root / "validation" / f"{slug}_dry_run_prompts.jsonl",
        "manifest": root / "validation" / f"{slug}_dry_run_manifest.json",
        "cache": root / "cache" / slug,
        "log": root / "runtime" / f"{slug}.log",
    }


def main() -> int:
    args = parse_args()
    freeze_path = Path(args.freeze_manifest).resolve()
    freeze_report_path = Path(args.freeze_report).resolve()
    template_dir = Path(args.template_dir).resolve()
    replay_path = Path(args.replay_manifest).resolve()
    replay_rows_path = Path(args.replay_rows).resolve()
    f6_backup_path = Path(args.f6_backup_manifest).resolve()
    runner_path = Path(args.runner).resolve()
    upstream_runner_path = Path(args.upstream_runner).resolve()
    output_root = Path(args.output_root).resolve()
    config_dir = output_root / "configs"

    require_hash(freeze_path, FREEZE_MANIFEST_SHA256, "F5 freeze manifest")
    freeze = load_json(freeze_path)
    if canonical_sha256(freeze) != FREEZE_CANONICAL_SHA256:
        raise ValueError("F5 canonical manifest SHA256 mismatch")
    freeze_report = load_json(freeze_report_path)
    if freeze_report.get("freeze_manifest_canonical_sha256") != FREEZE_CANONICAL_SHA256:
        raise ValueError("F5 freeze report canonical SHA256 mismatch")

    resources = freeze.get("resources", {})
    for name, expected_hash in EXPECTED_RESOURCE_HASHES.items():
        resource = resources.get(name)
        if not isinstance(resource, dict) or resource.get("sha256") != expected_hash:
            raise ValueError(f"F5 resource lock changed for {name}")
        require_hash(Path(resource["path"]), expected_hash, name)
    if count_jsonl(Path(resources["cluener_dev"]["path"])) != 1343:
        raise ValueError("CLUENER dev must contain exactly 1343 rows")
    if count_jsonl(Path(resources["cluener_support"]["path"])) != 30:
        raise ValueError("CLUENER support must contain exactly 30 rows")
    if count_jsonl(Path(resources["cluener_glossary"]["path"])) != 61:
        raise ValueError("CLUENER glossary must contain exactly 61 rows")

    require_hash(replay_path, REPLAY_MANIFEST_SHA256, "F6 replay manifest")
    require_hash(replay_rows_path, REPLAY_ROWS_SHA256, "F6 replay rows")
    require_hash(f6_backup_path, F6_BACKUP_MANIFEST_SHA256, "F6 backup manifest")
    replay_report = validate_replay(replay_path)
    if count_jsonl(replay_rows_path) != 1343:
        raise ValueError("F6 replay row file must contain exactly 1343 rows")
    require_hash(upstream_runner_path, UPSTREAM_RUNNER_SHA256, "F5 upstream runner")
    runner_text = runner_path.read_text(encoding="utf-8")
    if GATE not in runner_text or PHASE not in runner_text:
        raise ValueError("versioned runner does not register the public-NER gate")

    cells = {
        cell["cell_id"]: cell
        for cell in freeze.get("run_manifest", {}).get("cells", [])
        if cell.get("cell_id") in CELL_ORDER
    }
    nodes = {
        node["node_id"]: node
        for node in freeze.get("execution_nodes", {}).get("stage_n", [])
        if node.get("node_id", "").startswith("stage-n:cluener:")
    }
    if tuple(cell_id for cell_id in CELL_ORDER if cell_id in cells) != CELL_ORDER:
        raise ValueError("F5 does not contain the exact 12 public-NER cells")

    for directory in (config_dir, output_root / "results", output_root / "cache"):
        directory.mkdir(parents=True, exist_ok=True)
        if any(directory.iterdir()):
            raise FileExistsError(f"refusing non-empty execution directory: {directory}")
    (output_root / "runtime").mkdir(parents=True, exist_ok=True)
    (output_root / "validation").mkdir(parents=True, exist_ok=True)

    generated_cells: list[dict[str, Any]] = []
    for cell_id in CELL_ORDER:
        cell = cells[cell_id]
        variant = str(cell["config"])
        seed = int(cell["seed"])
        node_id = str(cell["execution"]["stage_n_node"])
        node = nodes[node_id]
        if (
            cell.get("dataset") != "cluener"
            or cell.get("k") != 5
            or cell.get("status") != "PLANNED"
            or node.get("query_resource") != "cluener_dev"
            or node.get("support_resource") != "cluener_support"
            or node.get("generation", {}).get("seed") != seed
        ):
            raise ValueError(f"{cell_id}: F5 cell contract changed")

        template_path = template_dir / f"cluener_{variant.lower()}_stage_n.yaml"
        template = load_yaml(template_path)
        validate_template(template, variant)
        paths = output_paths(output_root, variant, seed)
        for key in ("per_query", "summary", "dry_run_prompts", "manifest", "cache"):
            if paths[key].exists():
                raise FileExistsError(f"{cell_id}: output collision at {paths[key]}")

        config = copy.deepcopy(template)
        config["run_id"] = f"ner-public-cluener-{variant.lower()}-k5-seed{seed}"
        config["prepared_under_gate"] = GATE
        config["execution"] = {
            "phase": PHASE,
            "authorized": True,
            "human_gate": GATE,
            "approval_record": (
                "Human confirmed RTX 4090 24GB at 2.8 CNY/hour on 2026-08-05."
            ),
            "model_calls_allowed": True,
            "gpu_required": True,
            "explicit_exclusions": [
                "cluener_test_unlabeled",
                "sampled_cluener_dev",
                "E_or_E-prime",
                "K1_or_K10",
                "relation_extraction_or_stage_r",
                "verification",
                "domain_rerun",
                "IE051_or_other_matrix_cells",
                "online_rag_retrieval",
                "result_to_claim",
                "paper_edits",
                "github_sync",
            ],
        }
        config["data"] = {
            "dataset": "cluener",
            "support_path": resources["cluener_support"]["path"],
            "query_path": resources["cluener_dev"]["path"],
        }
        if variant == "A":
            config["examples"] = {"mode": "fixed_random", "k": 5, "seed": seed}
        elif variant == "B":
            config["examples"] = {"mode": "knn_retrieval", "k": 5, "seed": seed}
        else:
            b_path = output_paths(output_root, "B", seed)["per_query"]
            config["examples"] = {
                "mode": "knn_replay",
                "k": 5,
                "seed": seed,
                "source_per_query_path": str(b_path),
                "source_note": "Replay the same-seed B example_ids for clean C-B and D-C comparisons.",
            }
        if config["examples"]["mode"] != node["example_mode"]:
            raise ValueError(f"{cell_id}: example mode differs from F5")

        config["generation"] = copy.deepcopy(node["generation"])
        config["parsing"] = {
            "drop_invalid_entities": True,
            "mode": "proposal_stage_sanitize",
            "retry_mode": "parser_error_aware_once",
            "note": "Frozen F5 final NER parsing semantics.",
        }
        config["cache"] = {"dir": str(paths["cache"])}
        config["outputs"] = {
            "per_query": str(paths["per_query"]),
            "summary": str(paths["summary"]),
            "dry_run_prompts": str(paths["dry_run_prompts"]),
            "manifest": str(paths["manifest"]),
        }
        config["dry_run"] = {"max_queries": 1}

        config.pop("glossary", None)
        config.pop("rag", None)
        if variant in "CD":
            config["glossary"] = {
                "path": resources["cluener_glossary"]["path"],
                "max_entries": 20,
                "match_mode": "substring",
                "source_note": "Frozen support-bank-only CLUENER glossary.",
            }
        if variant == "D":
            config["rag"] = {
                "enabled": True,
                "mode": "replay_manifest",
                "replay_manifest_path": str(replay_path),
                "top_k": 3,
                "source_note": "Frozen F6 top-3 replay; no online embedding or reranking.",
            }

        lock = {
            "query": copy.deepcopy(resources["cluener_dev"]),
            "support": copy.deepcopy(resources["cluener_support"]),
            "freeze_manifest": {
                "path": str(freeze_path),
                "sha256": FREEZE_MANIFEST_SHA256,
                "canonical_sha256": FREEZE_CANONICAL_SHA256,
            },
            "runner": {
                "path": str(runner_path),
                "sha256": sha256_file(runner_path),
                "base_commit": args.base_commit,
                "change_scope": "authorization gate registration only",
            },
        }
        if variant in "CD":
            lock["glossary"] = copy.deepcopy(resources["cluener_glossary"])
        if variant == "D":
            lock["rag_corpus"] = copy.deepcopy(resources["cluener_rag_corpus"])
            lock["f6_replay_manifest"] = {
                "path": str(replay_path),
                "sha256": REPLAY_MANIFEST_SHA256,
                **replay_report,
            }
            lock["f6_replay_rows"] = {
                "path": str(replay_rows_path),
                "sha256": REPLAY_ROWS_SHA256,
                "rows": 1343,
            }
            lock["f6_backup_manifest"] = {
                "path": str(f6_backup_path),
                "sha256": F6_BACKUP_MANIFEST_SHA256,
            }
        config["resource_lock"] = lock
        config["f5_contract"] = {
            "cell_id": cell_id,
            "config_id": cell["execution"]["config_id"],
            "config_contract_sha256": cell["config_contract_sha256"],
            "canonical_final_per_query_path": cell["execution"]["final_per_query_path"],
            "canonical_final_summary_path": cell["execution"]["final_summary_path"],
            "stage_work": "stage_n_ner_only",
        }

        config_path = config_dir / f"cluener_{variant.lower()}_k5_seed{seed}.yaml"
        write_exclusive(config_path, yaml_bytes(config))
        generated_cells.append(
            {
                "cell_id": cell_id,
                "config": variant,
                "seed": seed,
                "rows": 1343,
                "config_id": cell["execution"]["config_id"],
                "config_contract_sha256": cell["config_contract_sha256"],
                "execution_config_path": str(config_path),
                "execution_config_sha256": sha256_file(config_path),
                "per_query_path": str(paths["per_query"]),
                "summary_path": str(paths["summary"]),
                "cache_dir": str(paths["cache"]),
                "log_path": str(paths["log"]),
                "dependency": None if variant in "AB" else f"cluener:B:k5:s{seed}",
            }
        )

    prepared_at = datetime.now(timezone.utc).isoformat()
    execution_manifest = {
        "schema_version": "ner-public-cluener-abcd-k5-final-v1",
        "status": "AUTHORIZED_PREINFERENCE",
        "approved_gate": GATE,
        "phase": PHASE,
        "prepared_at": prepared_at,
        "base_commit": args.base_commit,
        "scope": {
            "dataset": "cluener",
            "split": "complete_labeled_official_dev",
            "rows_per_cell": 1343,
            "task": "ner_only",
            "k": 5,
            "seeds": list(SEEDS),
            "configs": list(VARIANTS),
            "cell_order": list(CELL_ORDER),
        },
        "authorization": {
            "model_calls_allowed": True,
            "gpu_required": True,
            "relation_extraction_allowed": False,
            "verification_allowed": False,
            "online_rag_retrieval_allowed": False,
            "paper_edits_allowed": False,
            "github_sync_allowed": False,
        },
        "locks": {
            "freeze_manifest_sha256": FREEZE_MANIFEST_SHA256,
            "freeze_canonical_sha256": FREEZE_CANONICAL_SHA256,
            "resources": EXPECTED_RESOURCE_HASHES,
            "f6_replay_manifest_sha256": REPLAY_MANIFEST_SHA256,
            "f6_replay_rows_sha256": REPLAY_ROWS_SHA256,
            "f6_backup_manifest_sha256": F6_BACKUP_MANIFEST_SHA256,
            "upstream_runner_sha256": UPSTREAM_RUNNER_SHA256,
            "execution_runner_sha256": sha256_file(runner_path),
        },
        "paid_window": {
            "preflight_at": args.paid_preflight_at,
            "hourly_price_cny": args.hourly_price_cny,
            "target_hours": 8.0,
            "target_cost_cny": round(args.hourly_price_cny * 8.0, 2),
            "hard_stop_hours": 10.0,
            "hard_stop_cost_cny": round(args.hourly_price_cny * 10.0, 2),
        },
        "stop_conditions": [
            "any locked hash or row count mismatch",
            "any output collision or overwrite risk",
            "any completed cell parse_failure_rate >= 0.05",
            "any out-of-scope model request",
            "10 paid-GPU hours from the successful preflight",
        ],
        "matrix_before": "4/60",
        "matrix_after_if_all_cells_validate": "16/60",
        "cells": generated_cells,
    }
    manifest_path = output_root / "execution_manifest.json"
    write_exclusive(manifest_path, json_bytes(execution_manifest))
    lock_lines = [f"{sha256_file(manifest_path)}  {manifest_path}\n"]
    lock_lines.extend(
        f"{cell['execution_config_sha256']}  {cell['execution_config_path']}\n"
        for cell in generated_cells
    )
    write_exclusive(output_root / "PREINFERENCE_SHA256.txt", "".join(lock_lines).encode("utf-8"))
    report = {
        "status": "AUTHORIZED_PREINFERENCE",
        "cells": len(generated_cells),
        "rows_per_cell": 1343,
        "model_calls": 0,
        "manifest": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "runner_sha256": sha256_file(runner_path),
    }
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

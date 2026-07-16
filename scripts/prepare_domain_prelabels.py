#!/usr/bin/env python3
"""Generate deterministic P2 distant-supervision proposals without a GPU."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.domain_data import (  # noqa: E402
    build_distant_supervision_review_row,
    iter_objects_jsonl,
    prelabel_candidate,
    validate_candidate,
    validate_distant_supervision_review_row,
    write_objects_jsonl_atomic,
    write_review_csv_atomic,
)
from equipment_ie.schema import (  # noqa: E402
    iter_jsonl,
    sha256_file,
    write_jsonl_atomic,
)


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def append_log(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def verify_file(path: Path, expected_sha256: str) -> dict[str, Any]:
    actual = sha256_file(path)
    if actual != expected_sha256:
        raise ValueError(f"{path}: expected {expected_sha256}, got {actual}")
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": actual}


def git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def staged_path(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.with_name(f".{path.name}.stage-{os.getpid()}")


def validate_csv(path: Path, expected_records: int) -> None:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != expected_records:
        raise AssertionError("review CSV row count differs from proposals")
    for row in rows:
        if row["human_review_status"] != "NOT_STARTED":
            raise AssertionError("review CSV unexpectedly starts human annotation")
        if row["disagreement_status"] != "NOT_COMPUTED_LLM_NOT_RUN":
            raise AssertionError("review CSV unexpectedly contains LLM disagreement")
        if any(
            row[field]
            for field in (
                "annotator_a_entities_json",
                "annotator_a_relations_json",
                "annotator_a_notes",
                "annotator_b_entities_json",
                "annotator_b_relations_json",
                "annotator_b_notes",
                "adjudicated_entities_json",
                "adjudicated_relations_json",
                "adjudication_notes",
            )
        ):
            raise AssertionError("review CSV human fields must be blank")


def prepare(config_path: Path) -> dict[str, Any]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict) or config.get("phase") != "P2":
        raise ValueError("expected a P2 YAML config")
    if config.get("stage") != "distant_supervision_prelabel":
        raise ValueError("unexpected P2 stage")
    guards = config["guards"]
    if guards != {
        "require_gpu_free": True,
        "llm_allowed": False,
        "human_annotation_allowed": False,
        "split_or_freeze_allowed": False,
    }:
        raise ValueError("P2 distant-supervision guards were weakened")
    if Path("/dev/nvidia0").exists():
        raise RuntimeError("distant supervision must run in GPU-free mode")
    if config["method"] != {
        "name": "qaonmilitarykg_exact_longest_nonoverlap",
        "minimum_term_characters": 2,
        "proposed_entity_type": "EQUIPMENT",
        "infer_relations": False,
    }:
        raise ValueError("distant-supervision method differs from the approved plan")

    schema_spec = config["schema"]
    schema_path = Path(schema_spec["path"])
    schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    if schema.get("schema_id") != schema_spec["id"]:
        raise ValueError("schema id mismatch")
    if schema.get("version") != schema_spec["version"]:
        raise ValueError("schema version mismatch")
    if schema.get("status") != schema_spec["required_status"]:
        raise ValueError("schema has not passed human approval")
    approval = schema.get("approval", {})
    if not all(approval.get(key) for key in ("approved_by", "approved_at", "decision_record")):
        raise ValueError("schema approval record is incomplete")

    candidate_spec = config["inputs"]["candidates"]
    seed_spec = config["inputs"]["seed_terms"]
    candidate_path = Path(candidate_spec["path"])
    seed_path = Path(seed_spec["path"])
    input_artifacts = {
        "candidates": verify_file(candidate_path, candidate_spec["sha256"]),
        "seed_terms": verify_file(seed_path, seed_spec["sha256"]),
    }

    candidates = list(iter_objects_jsonl(candidate_path))
    if len(candidates) != int(candidate_spec["expected_records"]):
        raise ValueError("candidate count mismatch")
    candidate_ids: set[str] = set()
    for candidate in candidates:
        validate_candidate(candidate)
        if candidate["id"] in candidate_ids:
            raise ValueError(f"duplicate candidate id: {candidate['id']}")
        candidate_ids.add(candidate["id"])

    seed_rows = list(iter_objects_jsonl(seed_path))
    if len(seed_rows) != int(seed_spec["expected_records"]):
        raise ValueError("seed-term count mismatch")
    terms: list[str] = []
    seen_terms: set[str] = set()
    for index, row in enumerate(seed_rows, start=1):
        term = row.get("term")
        if not isinstance(term, str) or not term:
            raise ValueError(f"seed row {index} has no term")
        if term in seen_terms:
            raise ValueError(f"duplicate seed term: {term}")
        seen_terms.add(term)
        terms.append(term)

    proposals = [prelabel_candidate(candidate, terms) for candidate in candidates]
    review_rows = [
        build_distant_supervision_review_row(
            candidate,
            proposal,
            schema_version=schema_spec["version"],
        )
        for candidate, proposal in zip(candidates, proposals, strict=True)
    ]
    for row in review_rows:
        validate_distant_supervision_review_row(row)

    outputs = config["outputs"]
    if outputs.get("overwrite") is not False:
        raise ValueError("distant-supervision outputs must not overwrite")
    final_paths = {
        "proposals_jsonl": Path(outputs["proposals_jsonl"]),
        "review_jsonl": Path(outputs["review_jsonl"]),
        "review_csv": Path(outputs["review_csv"]),
        "report": Path(outputs["report"]),
    }
    existing = [str(path) for path in final_paths.values() if path.exists()]
    if existing:
        raise FileExistsError(f"refusing to overwrite outputs: {existing}")
    staged = {name: staged_path(path) for name, path in final_paths.items()}

    try:
        write_jsonl_atomic(staged["proposals_jsonl"], proposals)
        write_objects_jsonl_atomic(staged["review_jsonl"], review_rows)
        write_review_csv_atomic(staged["review_csv"], review_rows)

        reloaded_proposals = list(iter_jsonl(staged["proposals_jsonl"]))
        reloaded_reviews = list(iter_objects_jsonl(staged["review_jsonl"]))
        if reloaded_proposals != proposals:
            raise AssertionError("proposal JSONL round trip changed content")
        if reloaded_reviews != review_rows:
            raise AssertionError("review JSONL round trip changed content")
        for row in reloaded_reviews:
            validate_distant_supervision_review_row(row)
        validate_csv(staged["review_csv"], len(review_rows))

        source_records = Counter(candidate["source_type"] for candidate in candidates)
        source_matched = Counter(
            candidate["source_type"]
            for candidate, proposal in zip(candidates, proposals, strict=True)
            if proposal["entities"]
        )
        matched_records = sum(bool(proposal["entities"]) for proposal in proposals)
        total_entities = sum(len(proposal["entities"]) for proposal in proposals)
        matched_spans = sorted(
            {
                entity["span"]
                for proposal in proposals
                for entity in proposal["entities"]
            }
        )
        generated_at = datetime.now(timezone.utc).isoformat()
        output_artifacts = {
            name: {
                "path": str(final_paths[name]),
                "bytes": staged[name].stat().st_size,
                "sha256": sha256_file(staged[name]),
            }
            for name in ("proposals_jsonl", "review_jsonl", "review_csv")
        }
        output_artifacts["proposals_jsonl"]["records"] = len(proposals)
        output_artifacts["review_jsonl"]["records"] = len(review_rows)
        output_artifacts["review_csv"]["records"] = len(review_rows)
        report = {
            "phase": "P2",
            "stage": "distant_supervision_prelabel",
            "run_id": config["run_id"],
            "generated_at": generated_at,
            "code_commit": git_commit(),
            "config_path": str(config_path),
            "config_sha256": sha256_file(config_path),
            "schema": {
                "path": str(schema_path),
                "id": schema["schema_id"],
                "version": schema["version"],
                "status": schema["status"],
                "sha256": sha256_file(schema_path),
                "approval": approval,
            },
            "inputs": input_artifacts,
            "method": config["method"],
            "statistics": {
                "candidate_records": len(candidates),
                "matched_records": matched_records,
                "unmatched_records": len(candidates) - matched_records,
                "match_coverage": matched_records / len(candidates),
                "proposed_entities": total_entities,
                "proposed_relations": 0,
                "unique_matched_spans": len(matched_spans),
                "source_records": dict(sorted(source_records.items())),
                "source_matched_records": dict(sorted(source_matched.items())),
            },
            "outputs": output_artifacts,
            "guards": {
                "gpu_device_present": False,
                "paid_gpu_used": False,
                "llm_used": False,
                "llm_disagreement_computed": False,
                "human_annotation_started": False,
                "dataset_split_or_frozen": False,
            },
        }
        write_json_atomic(staged["report"], report)
        json.loads(staged["report"].read_text(encoding="utf-8"))
        published: list[Path] = []
        try:
            for name, destination in final_paths.items():
                staged[name].replace(destination)
                published.append(destination)
        except BaseException:
            for destination in published:
                destination.unlink(missing_ok=True)
            raise
        return report
    except BaseException:
        for path in staged.values():
            path.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "configs" / "p2_distant_supervision.yaml",
    )
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    log_path = Path(config["outputs"]["log"])
    started = time.monotonic()
    event = {
        "phase": "P2",
        "step": "distant_supervision_prelabel",
        "run_id": config.get("run_id"),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "config_sha256": sha256_file(config_path),
    }
    try:
        report = prepare(config_path)
        event.update(
            {
                "status": "ok",
                "duration_seconds": round(time.monotonic() - started, 3),
                "statistics": report["statistics"],
                "output_hashes": {
                    name: artifact["sha256"]
                    for name, artifact in report["outputs"].items()
                },
                "paid_gpu_used": False,
                "llm_used": False,
                "human_annotation_started": False,
            }
        )
        append_log(log_path, event)
        print(json.dumps(report["statistics"], ensure_ascii=False, sort_keys=True))
        return 0
    except BaseException as exc:
        event.update(
            {
                "status": "error",
                "duration_seconds": round(time.monotonic() - started, 3),
                "error_type": type(exc).__name__,
                "error": str(exc),
                "paid_gpu_used": False,
                "llm_used": False,
                "human_annotation_started": False,
            }
        )
        append_log(log_path, event)
        raise


if __name__ == "__main__":
    raise SystemExit(main())

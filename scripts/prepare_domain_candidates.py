#!/usr/bin/env python3
"""Collect the fixed 400-passage P2 candidate corpus without using a GPU."""

from __future__ import annotations

import argparse
import json
import os
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
    cmnee_candidates,
    collect_baike_candidates,
    extract_seed_terms,
    iter_objects_jsonl,
    patent_candidates,
    select_quotas_with_dedup,
    validate_candidate,
    write_objects_jsonl_atomic,
)
from equipment_ie.schema import sha256_file  # noqa: E402


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


def verify_source(path: Path, expected: str) -> dict[str, Any]:
    actual = sha256_file(path)
    if actual != expected:
        raise ValueError(f"{path}: expected {expected}, got {actual}")
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": actual}


def prepare(config_path: Path) -> dict[str, Any]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict) or config.get("phase") != "P2":
        raise ValueError("expected a P2 YAML config")
    sources = config["sources"]
    source_artifacts: dict[str, Any] = {}
    qa_path = Path(sources["qaonmilitarykg"]["data_path"])
    source_artifacts["qaonmilitarykg"] = verify_source(
        qa_path, sources["qaonmilitarykg"]["data_sha256"]
    )
    patent_files = sources["kppatent_zh"]["files"]
    source_artifacts["kppatent_zh"] = [
        verify_source(Path(file_spec["path"]), file_spec["sha256"])
        for file_spec in patent_files
    ]
    source_artifacts["kppatent_zh_license"] = verify_source(
        Path(sources["kppatent_zh"]["license_path"]),
        sources["kppatent_zh"]["license_sha256"],
    )
    cmnee_path = Path(sources["cmnee"]["data_path"])
    source_artifacts["cmnee"] = verify_source(
        cmnee_path, sources["cmnee"]["data_sha256"]
    )

    seed_terms = extract_seed_terms(qa_path, sources["qaonmilitarykg"]["revision"])
    seed_path = Path(config["data_root"]) / "domain_seed_terms.jsonl"
    seed_count = write_objects_jsonl_atomic(seed_path, seed_terms)

    min_chars = int(config["min_chars"])
    max_chars = int(config["max_chars"])
    specific = config["equipment_keywords"]["specific"]
    general = config["equipment_keywords"]["general"]
    baike_config = config["baidu_baike"]
    baike = collect_baike_candidates(
        seed_terms,
        cache_path=baike_config["cache_path"],
        pool_target=int(baike_config["pool_target"]),
        max_attempts=int(baike_config["max_attempts"]),
        min_chars=min_chars,
        max_chars=max_chars,
        seed=int(config["seed"]),
        timeout_seconds=int(baike_config["timeout_seconds"]),
        delay_seconds=float(baike_config["request_delay_seconds"]),
        user_agent=baike_config["user_agent"],
    )
    patent_pool = patent_candidates(
        patent_files,
        min_chars=min_chars,
        max_chars=max_chars,
        specific_keywords=specific,
        general_keywords=general,
        revision=sources["kppatent_zh"]["revision"],
    )
    cmnee_pool = cmnee_candidates(
        cmnee_path,
        min_chars=min_chars,
        max_chars=max_chars,
        specific_keywords=specific,
        general_keywords=general,
        revision=sources["cmnee"]["revision"],
    )
    pools = {
        "baidu_baike": baike.candidates,
        "patent": patent_pool,
        "cmnee": cmnee_pool,
    }
    candidates, removed = select_quotas_with_dedup(
        pools,
        config["source_quotas"],
        seed=int(config["seed"]),
        ngram_size=int(config["deduplication"]["ngram_size"]),
        containment_threshold=float(
            config["deduplication"]["containment_threshold"]
        ),
    )
    if len(candidates) != int(config["candidate_target"]):
        raise AssertionError("candidate target was not met")

    candidate_path = Path(config["data_root"]) / "domain_candidates.jsonl"
    candidate_count = write_objects_jsonl_atomic(candidate_path, candidates)
    source_counts = Counter(row["source_type"] for row in candidates)
    reloaded_count = 0
    reloaded_ids: set[str] = set()
    reloaded_sources: Counter[str] = Counter()
    for row in iter_objects_jsonl(candidate_path):
        validate_candidate(row)
        if row["id"] in reloaded_ids:
            raise AssertionError(f"duplicate candidate id after reload: {row['id']}")
        reloaded_ids.add(row["id"])
        reloaded_sources[row["source_type"]] += 1
        reloaded_count += 1
    if reloaded_count != candidate_count or dict(reloaded_sources) != dict(source_counts):
        raise AssertionError("candidate write/read counts differ")
    report_root = Path(config["report_root"])
    dedup_path = report_root / "candidate_dedup.json"
    write_json_atomic(dedup_path, removed)
    report = {
        "phase": "P2",
        "stage": "candidate_collection_before_pause_a",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config_path": str(config_path),
        "config_sha256": sha256_file(config_path),
        "sources": sources,
        "source_artifacts": source_artifacts,
        "seed_dictionary": {
            "path": str(seed_path),
            "records": seed_count,
            "bytes": seed_path.stat().st_size,
            "sha256": sha256_file(seed_path),
            "redistribution": "prohibited; source license not stated",
        },
        "candidate_pools": {
            "baidu_baike": len(baike.candidates),
            "patent": len(patent_pool),
            "cmnee": len(cmnee_pool),
        },
        "baidu_audit": {
            "attempts": baike.attempts,
            "cache_hits": baike.cache_hits,
            "failures": baike.failures,
        },
        "candidates": {
            "path": str(candidate_path),
            "records": candidate_count,
            "source_counts": dict(sorted(source_counts.items())),
            "bytes": candidate_path.stat().st_size,
            "sha256": sha256_file(candidate_path),
            "min_chars": min(len(row["text"]) for row in candidates),
            "max_chars": max(len(row["text"]) for row in candidates),
            "round_trip": True,
        },
        "deduplication": {
            **config["deduplication"],
            "removed": len(removed),
            "log_path": str(dedup_path),
            "log_sha256": sha256_file(dedup_path),
        },
        "paid_gpu_used": False,
        "formal_annotation_started": False,
    }
    report_path = report_root / "collection_report.json"
    write_json_atomic(report_path, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "configs" / "p2_domain_data.yaml",
    )
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    started = time.monotonic()
    event = {
        "phase": "P2",
        "step": "collect_domain_candidates",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "config_sha256": sha256_file(config_path),
    }
    try:
        report = prepare(config_path)
        event.update(
            {
                "status": "ok",
                "duration_seconds": round(time.monotonic() - started, 3),
                "candidate_sha256": report["candidates"]["sha256"],
                "candidate_counts": report["candidates"]["source_counts"],
            }
        )
        append_log(Path(config["log_path"]), event)
        print(json.dumps(report["candidates"], ensure_ascii=False, sort_keys=True))
        return 0
    except BaseException as exc:
        event.update(
            {
                "status": "error",
                "duration_seconds": round(time.monotonic() - started, 3),
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
        )
        append_log(Path(config["log_path"]), event)
        raise


if __name__ == "__main__":
    raise SystemExit(main())

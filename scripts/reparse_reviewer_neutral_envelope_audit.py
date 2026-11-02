#!/usr/bin/env python3
"""Reparse saved Qwen responses with one baseline-neutral NER envelope policy."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

try:
    from scripts.audit_reviewer_occurrence_sanitized_pilot import BASELINES, SYSTEMS, metrics, paired_bootstrap
except ModuleNotFoundError:
    from audit_reviewer_occurrence_sanitized_pilot import BASELINES, SYSTEMS, metrics, paired_bootstrap

from equipment_ie.extraction import parse_extraction_output


GATE = "JISE_ECFSIE_REVIEW_BASELINE_QWEN_NEUTRAL_ENVELOPE_REPARSE_AUDIT_APPROVED"
ENTITY_TYPES = {"EQUIPMENT", "MODULE", "TECH_SCHEME", "METRIC"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_cache(cache_dir: Path, request_hash: str) -> dict:
    path = cache_dir / request_hash[:2] / f"{request_hash}.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value.get("content"), str):
        raise ValueError(f"{path}: cache content missing")
    return value


def counts(gold: dict, pred: dict) -> tuple[int, int, int]:
    def entities(record: dict) -> set[tuple[int, int, str]]:
        return {(int(e["start"]), int(e["end"]), str(e["type"])) for e in record["entities"]}

    gold_set, pred_set = entities(gold), entities(pred)
    return len(gold_set & pred_set), len(pred_set - gold_set), len(gold_set - pred_set)


def reparse_row(row: dict, cache_dir: Path) -> dict:
    errors: list[str] = []
    for attempt in row["attempts"]:
        cached = load_cache(cache_dir, str(attempt["request_hash"]))
        flags: list[dict] = []
        try:
            pred = parse_extraction_output(
                cached["content"],
                record_id=str(row["id"]),
                text=str(row["gold"]["text"]),
                entity_types=ENTITY_TYPES,
                relation_types={},
                drop_invalid_entities=True,
                sanitization_flags=flags,
                output_mode="occurrence",
                ner_only_envelope_policy="entities_or_entities_relations_v2",
            )
        except Exception as exc:
            errors.append(f"{type(exc).__name__}: {exc}")
            continue
        return {
            "id": row["id"],
            "gold": row["gold"],
            "pred_raw": pred,
            "parse_failure": False,
            "accepted_attempt": len(errors) + 1,
            "attempt_errors_before_acceptance": errors,
            "sanitization_flags": flags,
            "source_request_hash": attempt["request_hash"],
            "source_raw_output_hash": cached.get("raw_output_hash"),
        }
    return {
        "id": row["id"],
        "gold": row["gold"],
        "pred_raw": {"id": row["id"], "text": row["gold"]["text"], "entities": [], "relations": []},
        "parse_failure": True,
        "accepted_attempt": None,
        "attempt_errors_before_acceptance": errors,
        "sanitization_flags": [],
        "source_request_hash": None,
        "source_raw_output_hash": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--human-gate", required=True)
    parser.add_argument("--bootstrap-reps", type=int, default=10000)
    args = parser.parse_args()
    if args.human_gate != GATE:
        raise ValueError(f"exact gate required: {GATE}")
    input_root = Path(args.input_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    if "domain_test" in str(input_root) or "domain_test" in str(output_dir):
        raise ValueError("frozen test paths are forbidden")
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite {output_dir}")
    output_dir.mkdir(parents=True)

    reparsed: dict[str, list[dict]] = {}
    sources: dict[str, str] = {}
    ids: list[str] | None = None
    for system in SYSTEMS:
        source = input_root / "pilot20" / system / "per_query.jsonl"
        cache_dir = input_root / "pilot20" / system / "cache"
        original = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()]
        current_ids = [str(row["id"]) for row in original]
        if ids is None:
            ids = current_ids
        elif current_ids != ids:
            raise ValueError("query ID/order mismatch")
        reparsed[system] = [reparse_row(row, cache_dir) for row in original]
        sources[system] = sha256(source)
        path = output_dir / f"{system}_reparsed.jsonl"
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in reparsed[system]),
            encoding="utf-8",
        )

    per_counts = {
        system: [counts(row["gold"], row["pred_raw"]) for row in reparsed[system]]
        for system in SYSTEMS
    }
    valid_all = [i for i in range(20) if all(not reparsed[s][i]["parse_failure"] for s in SYSTEMS)]
    report = {
        "gate": GATE,
        "policy": "occurrence_entities_or_entities_relations_v2",
        "model_calls": 0,
        "gold_or_bert_repair": False,
        "source_per_query_sha256": sources,
        "query_records": 20,
        "common_valid_records": len(valid_all),
        "systems": {},
        "common_valid_systems": {},
        "ec_fsie_full_paired_bootstrap": {},
        "common_valid_ec_fsie_full_paired_bootstrap": {},
    }
    for system in SYSTEMS:
        report["systems"][system] = {
            **metrics(per_counts[system]),
            "parse_failures": sum(row["parse_failure"] for row in reparsed[system]),
            "relations_defaulted_rows": sum(
                any(flag.get("kind") == "NER_RELATIONS_DEFAULTED" for flag in row["sanitization_flags"])
                for row in reparsed[system]
            ),
            "failed_ids": [str(row["id"]) for row in reparsed[system] if row["parse_failure"]],
        }
        report["common_valid_systems"][system] = {
            **metrics([per_counts[system][i] for i in valid_all]),
            "records": len(valid_all),
        }
    for offset, baseline in enumerate(BASELINES):
        report["ec_fsie_full_paired_bootstrap"][baseline] = paired_bootstrap(
            per_counts["ec_fsie_full"],
            per_counts[baseline],
            reps=args.bootstrap_reps,
            seed=20261117 + offset,
        )
        report["common_valid_ec_fsie_full_paired_bootstrap"][baseline] = paired_bootstrap(
            [per_counts["ec_fsie_full"][i] for i in valid_all],
            [per_counts[baseline][i] for i in valid_all],
            reps=args.bootstrap_reps,
            seed=20261217 + offset,
        )
    (output_dir / "audit_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

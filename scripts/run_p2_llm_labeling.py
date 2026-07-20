#!/usr/bin/env python3
"""Dry-run or execute cached Qwen2.5-14B-AWQ P2 labeling jobs."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from equipment_ie.domain_data import (  # noqa: E402
    iter_objects_jsonl,
    validate_candidate,
    write_objects_jsonl_atomic,
)
from equipment_ie.llm_labeling import (  # noqa: E402
    LabelParseError,
    build_label_prompt,
    build_llm_review_row,
    build_request_envelope,
    build_retry_prompt,
    canonical_json,
    chat_with_cache,
    merge_distant_and_llm,
    parse_model_label_output,
    select_candidates,
    sha256_text,
    validate_llm_review_row,
    write_llm_review_csv_atomic,
)
from equipment_ie.schema import (  # noqa: E402
    iter_jsonl,
    sha256_file,
    validate_record,
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


def git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def verify_file(path: Path, expected_sha256: str) -> dict[str, Any]:
    actual = sha256_file(path)
    if actual != expected_sha256:
        raise ValueError(f"{path}: expected {expected_sha256}, got {actual}")
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": actual}


def _validate_guards(config: dict[str, Any]) -> None:
    if config["prompt"].get("include_distant_supervision_in_prompt") is not False:
        raise ValueError("LLM prompt must remain independent of distant supervision")
    if config["guards"] != {
        "llm_must_not_see_distant_supervision": True,
        "human_annotation_allowed": False,
        "split_or_freeze_allowed": False,
    }:
        raise ValueError("P2 LLM guards were weakened")
    if config["outputs"].get("overwrite") is not False:
        raise ValueError("P2 LLM outputs must refuse overwrite")
    if not isinstance(config["prompt"].get("retry_suffix"), str) or not config[
        "prompt"
    ]["retry_suffix"].strip():
        raise ValueError("retry suffix is missing")


def _gpu_device_present(device_root: Path = Path("/dev")) -> bool:
    return any(
        path.name.startswith("nvidia") and path.name[len("nvidia") :].isdigit()
        for path in device_root.glob("nvidia*")
    )


def _load_context(config_path: Path) -> dict[str, Any]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if config.get("phase") != "P2" or config.get("stage") not in {
        "llm_assisted_label_sanity",
        "llm_assisted_label_full",
    }:
        raise ValueError("unexpected P2 LLM configuration")
    _validate_guards(config)

    schema_spec = config["schema"]
    schema_path = Path(schema_spec["path"])
    verify_file(schema_path, schema_spec["sha256"])
    schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    if schema.get("version") != schema_spec["version"]:
        raise ValueError("schema version mismatch")
    if schema.get("status") != schema_spec["required_status"]:
        raise ValueError("schema is not approved")

    prompt_spec = config["prompt"]
    prompt_config_path = Path(prompt_spec["definitions_path"])
    verify_file(prompt_config_path, prompt_spec["definitions_sha256"])
    prompt_config = yaml.safe_load(prompt_config_path.read_text(encoding="utf-8"))
    if prompt_config.get("prompt_version") != prompt_spec["version"]:
        raise ValueError("prompt-definition version mismatch")
    if prompt_config.get("schema_version") != schema_spec["version"]:
        raise ValueError("prompt definitions target a different schema")
    prompt_constraints = prompt_config.get("constraints", {})
    if prompt_constraints.get("include_distant_supervision_in_prompt") is not False:
        raise ValueError("prompt definitions expose distant supervision")
    if prompt_constraints.get("retry_suffix") != prompt_spec["retry_suffix"]:
        raise ValueError("prompt retry suffix mismatch")
    examples_path = Path(prompt_spec["examples_path"])
    verify_file(examples_path, prompt_spec["examples_sha256"])
    examples_by_id = {row["id"]: row for row in iter_jsonl(examples_path)}
    example_ids = list(prompt_spec["example_ids"])
    if len(example_ids) != len(set(example_ids)):
        raise ValueError("duplicate prompt example id")
    try:
        examples = [examples_by_id[record_id] for record_id in example_ids]
    except KeyError as exc:
        raise ValueError(f"missing prompt example: {exc}") from exc

    candidate_spec = config["inputs"]["candidates"]
    distant_spec = config["inputs"]["distant_supervision"]
    candidate_path = Path(candidate_spec["path"])
    distant_path = Path(distant_spec["path"])
    candidate_artifact = verify_file(candidate_path, candidate_spec["sha256"])
    distant_artifact = verify_file(distant_path, distant_spec["sha256"])
    candidates = list(iter_objects_jsonl(candidate_path))
    distant_records = list(iter_jsonl(distant_path))
    if len(candidates) != int(candidate_spec["expected_records"]):
        raise ValueError("candidate count mismatch")
    if len(distant_records) != int(distant_spec["expected_records"]):
        raise ValueError("distant-supervision count mismatch")
    for candidate in candidates:
        validate_candidate(candidate)
    selected = select_candidates(candidates, distant_records, config["selection"])
    distant_by_id = {row["id"]: row for row in distant_records}
    selected_pairs = [(row, distant_by_id[row["id"]]) for row in selected]

    model_spec = config["model"]
    model_path = Path(model_spec["path"])
    model_artifacts = {
        name: verify_file(model_path / name, digest)
        for name, digest in model_spec["required_files"].items()
    }
    manifest_spec = model_spec["p0_manifest"]
    model_artifacts["p0_manifest"] = verify_file(
        Path(manifest_spec["path"]), manifest_spec["sha256"]
    )
    return {
        "config": config,
        "config_path": config_path,
        "schema": schema,
        "schema_path": schema_path,
        "prompt_config": prompt_config,
        "prompt_config_path": prompt_config_path,
        "examples": examples,
        "examples_path": examples_path,
        "selected_pairs": selected_pairs,
        "input_artifacts": {
            "candidates": candidate_artifact,
            "distant_supervision": distant_artifact,
        },
        "model_artifacts": model_artifacts,
    }


def _prompt_and_envelope(
    context: dict[str, Any], candidate: dict[str, Any], *, retry: bool
) -> tuple[str, dict[str, Any]]:
    config = context["config"]
    prompt = build_label_prompt(
        text=candidate["text"],
        schema=context["schema"],
        prompt_config=context["prompt_config"],
        examples=context["examples"],
        prompt_version=config["prompt"]["version"],
    )
    if retry:
        prompt = build_retry_prompt(prompt, config["prompt"]["retry_suffix"])
    envelope = build_request_envelope(
        prompt=prompt,
        model=config["model"]["served_model_name"],
        generation=config["generation"],
        prompt_version=config["prompt"]["version"],
        schema_sha256=config["schema"]["sha256"],
        prompt_config_sha256=config["prompt"]["definitions_sha256"],
        examples_sha256=config["prompt"]["examples_sha256"],
    )
    return prompt, envelope


def _token_count(tokenizer: Any, envelope: dict[str, Any]) -> int:
    token_ids = tokenizer.apply_chat_template(
        envelope["payload"]["messages"],
        tokenize=True,
        add_generation_prompt=True,
    )
    return len(token_ids)


def dry_run(context: dict[str, Any]) -> dict[str, Any]:
    config = context["config"]
    execution = config["execution"]
    if execution.get("dry_run_requires_gpu_free") is not True:
        raise ValueError("dry-run GPU-free guard is missing")
    if _gpu_device_present():
        raise RuntimeError("P2 LLM dry-run must use GPU-free mode")
    destination = Path(config["outputs"]["dry_run_manifest"])
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite dry-run manifest: {destination}")
    actual_paths = [
        Path(config["outputs"][name])
        for name in (
            "llm_proposals_jsonl",
            "union_proposals_jsonl",
            "review_jsonl",
            "review_csv",
            "report",
        )
    ]
    collisions = [str(path) for path in actual_paths if path.exists()]
    if collisions:
        raise FileExistsError(f"actual output paths already exist: {collisions}")

    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        config["model"]["path"], local_files_only=True, trust_remote_code=False
    )
    prompt_rows: list[dict[str, Any]] = []
    initial_tokens: list[int] = []
    retry_tokens: list[int] = []
    source_counts: Counter[str] = Counter()
    matched_count = 0
    for candidate, distant in context["selected_pairs"]:
        initial_prompt, initial_envelope = _prompt_and_envelope(
            context, candidate, retry=False
        )
        retry_prompt, retry_envelope = _prompt_and_envelope(context, candidate, retry=True)
        initial_count = _token_count(tokenizer, initial_envelope)
        retry_count = _token_count(tokenizer, retry_envelope)
        initial_tokens.append(initial_count)
        retry_tokens.append(retry_count)
        source_counts[candidate["source_type"]] += 1
        matched_count += bool(distant["entities"])
        prompt_rows.append(
            {
                "id": candidate["id"],
                "source_type": candidate["source_type"],
                "distant_supervision_matched": bool(distant["entities"]),
                "initial_prompt_hash": sha256_text(initial_prompt),
                "initial_request_hash": sha256_text(canonical_json(initial_envelope)),
                "initial_input_tokens": initial_count,
                "retry_prompt_hash": sha256_text(retry_prompt),
                "retry_request_hash": sha256_text(canonical_json(retry_envelope)),
                "retry_input_tokens": retry_count,
            }
        )
    max_input_tokens = max(retry_tokens)
    max_tokens = int(config["generation"]["max_tokens"])
    max_model_len = int(config["model"]["max_model_len"])
    if max_input_tokens + max_tokens > max_model_len:
        raise ValueError("prompt plus output budget exceeds max_model_len")
    record_count = len(prompt_rows)
    manifest = {
        "phase": "P2",
        "stage": config["stage"],
        "run_id": config["run_id"],
        "mode": "dry_run_only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "code_commit": git_commit(),
        "config_path": str(context["config_path"]),
        "config_sha256": sha256_file(context["config_path"]),
        "execution_authorized": execution.get("authorized") is True,
        "gpu_device_present": False,
        "api_called": False,
        "model_weights_loaded": False,
        "schema": {
            "version": context["schema"]["version"],
            "sha256": config["schema"]["sha256"],
        },
        "inputs": context["input_artifacts"],
        "model_artifacts": context["model_artifacts"],
        "selection": {
            "record_count": record_count,
            "source_counts": dict(sorted(source_counts.items())),
            "distant_supervision_matched": matched_count,
            "distant_supervision_unmatched": record_count - matched_count,
            "record_ids": [row["id"] for row in prompt_rows],
        },
        "prompt": {
            "version": config["prompt"]["version"],
            "definitions_sha256": config["prompt"]["definitions_sha256"],
            "examples_sha256": config["prompt"]["examples_sha256"],
            "records": prompt_rows,
            "aggregate_sha256": sha256_text(canonical_json(prompt_rows)),
        },
        "token_budget": {
            "initial_input_tokens_total": sum(initial_tokens),
            "initial_input_tokens_min": min(initial_tokens),
            "initial_input_tokens_max": max(initial_tokens),
            "initial_input_tokens_mean": sum(initial_tokens) / record_count,
            "retry_input_tokens_total": sum(retry_tokens),
            "retry_input_tokens_max": max(retry_tokens),
            "maximum_output_tokens_per_request": max_tokens,
            "maximum_context_tokens": max_input_tokens + max_tokens,
            "max_model_len": max_model_len,
            "worst_case_request_count": 2 * record_count,
            "worst_case_input_tokens": sum(initial_tokens) + sum(retry_tokens),
            "worst_case_output_tokens": 2 * record_count * max_tokens,
        },
        "server": {
            "launch_command": config["server"]["launch_command"],
            "base_url": config["server"]["base_url"],
        },
        "budget": config["budget"],
        "guards": {
            "human_annotation_allowed": False,
            "split_or_freeze_allowed": False,
            "paid_gpu_used": False,
        },
    }
    write_json_atomic(destination, manifest)
    return manifest


def _check_server(config: dict[str, Any]) -> None:
    endpoint = f"{config['server']['base_url'].rstrip('/')}/v1/models"
    api_key = os.environ.get(config["server"]["api_key_env"], "EMPTY")
    request = Request(endpoint, headers={"Authorization": f"Bearer {api_key}"})
    with urlopen(request, timeout=int(config["server"]["request_timeout_seconds"])) as response:
        value = json.loads(response.read().decode("utf-8"))
    model_ids = {row.get("id") for row in value.get("data", []) if isinstance(row, dict)}
    if config["model"]["served_model_name"] not in model_ids:
        raise RuntimeError("vLLM server does not expose the configured model")


def _process_one(
    context: dict[str, Any], pair: tuple[dict[str, Any], dict[str, Any]], api_key: str
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    config = context["config"]
    candidate, distant = pair
    attempts: list[dict[str, Any]] = []
    llm_proposal: dict[str, Any] | None = None
    llm_error: str | None = None
    resolution_flags: list[dict[str, Any]] = []
    for attempt_number, retry in ((1, False), (2, True)):
        prompt, envelope = _prompt_and_envelope(context, candidate, retry=retry)
        chat = chat_with_cache(
            envelope=envelope,
            cache_dir=Path(config["cache"]["directory"]),
            base_url=config["server"]["base_url"],
            timeout_seconds=int(config["server"]["request_timeout_seconds"]),
            api_key=api_key,
        )
        parse_error: str | None = None
        try:
            attempt_resolution_flags: list[dict[str, Any]] = []
            llm_proposal = parse_model_label_output(
                chat.content,
                record_id=candidate["id"],
                text=candidate["text"],
                schema=context["schema"],
                resolve_overlaps=True,
                resolution_flags=attempt_resolution_flags,
            )
            resolution_flags = attempt_resolution_flags
        except LabelParseError as exc:
            parse_error = str(exc)
            llm_error = parse_error
        attempts.append(
            {
                "attempt": attempt_number,
                "prompt_hash": sha256_text(prompt),
                "request_hash": chat.request_hash,
                "raw_output_hash": chat.raw_output_hash,
                "cache_hit": chat.cache_hit,
                "latency_ms": round(chat.latency_ms, 3),
                "parse_error": parse_error,
            }
        )
        if llm_proposal is not None:
            break
    union, provenance, flags = merge_distant_and_llm(
        distant, llm_proposal, llm_error=llm_error
    )
    flags.extend(resolution_flags)
    review = build_llm_review_row(
        candidate=candidate,
        distant=distant,
        llm=llm_proposal,
        union=union,
        provenance=provenance,
        disagreement_flags=flags,
        attempts=attempts,
        prompt_version=config["prompt"]["version"],
        llm_error=llm_error,
    )
    llm_output = llm_proposal or {
        "id": candidate["id"],
        "text": candidate["text"],
        "entities": [],
        "relations": [],
    }
    return llm_output, union, review


def _staged_path(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.with_name(f".{path.name}.stage-{os.getpid()}")


def _validate_review_csv(path: Path, expected_records: int) -> None:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != expected_records:
        raise AssertionError("LLM review CSV count mismatch")
    human_fields = [name for name in rows[0] if name.startswith("annotator_") or name.startswith("adjudicat")]
    for row in rows:
        if row["human_review_status"] != "NOT_STARTED":
            raise AssertionError("LLM review CSV starts human annotation")
        if any(row[name] for name in human_fields):
            raise AssertionError("LLM review CSV contains human annotation content")


def execute(context: dict[str, Any]) -> dict[str, Any]:
    config = context["config"]
    execution = config["execution"]
    if execution.get("authorized") is not True or not execution.get("approval_record"):
        raise PermissionError("actual P2 LLM execution lacks explicit human approval")
    if execution.get("actual_run_requires_gpu") is not True or not _gpu_device_present():
        raise RuntimeError("actual P2 LLM execution requires paid GPU mode")
    _check_server(config)
    final_paths = {
        name: Path(config["outputs"][name])
        for name in (
            "llm_proposals_jsonl",
            "union_proposals_jsonl",
            "review_jsonl",
            "review_csv",
            "report",
        )
    }
    existing = [str(path) for path in final_paths.values() if path.exists()]
    if existing:
        raise FileExistsError(f"refusing to overwrite LLM outputs: {existing}")
    api_key = os.environ.get(config["server"]["api_key_env"], "EMPTY")
    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=int(config["generation"]["max_concurrency"])) as pool:
        results = list(
            pool.map(
                lambda pair: _process_one(context, pair, api_key),
                context["selected_pairs"],
            )
        )
    llm_records = [result[0] for result in results]
    union_records = [result[1] for result in results]
    reviews = [result[2] for result in results]
    for row in reviews:
        validate_llm_review_row(row)

    staged = {name: _staged_path(path) for name, path in final_paths.items()}
    try:
        write_jsonl_atomic(staged["llm_proposals_jsonl"], llm_records)
        write_jsonl_atomic(staged["union_proposals_jsonl"], union_records)
        write_objects_jsonl_atomic(staged["review_jsonl"], reviews)
        write_llm_review_csv_atomic(staged["review_csv"], reviews)
        if list(iter_jsonl(staged["llm_proposals_jsonl"])) != llm_records:
            raise AssertionError("LLM proposal round trip changed content")
        if list(iter_jsonl(staged["union_proposals_jsonl"])) != union_records:
            raise AssertionError("union proposal round trip changed content")
        reloaded_reviews = list(iter_objects_jsonl(staged["review_jsonl"]))
        if reloaded_reviews != reviews:
            raise AssertionError("LLM review round trip changed content")
        for row in reloaded_reviews:
            validate_llm_review_row(row)
        _validate_review_csv(staged["review_csv"], len(reviews))

        parse_failures = sum(row["llm_execution"]["parse_failure"] for row in reviews)
        attempts = [attempt for row in reviews for attempt in row["llm_execution"]["attempts"]]
        entity_types = Counter(
            entity["type"] for row in llm_records for entity in row["entities"]
        )
        relation_types = Counter(
            relation["type"] for row in llm_records for relation in row["relations"]
        )
        flag_types = Counter(
            flag["kind"] for row in reviews for flag in row["disagreement_flags"]
        )
        parse_failure_rate = parse_failures / len(reviews)
        gate = parse_failure_rate < float(
            config["success_gates"]["maximum_parse_failure_rate"]
        )
        output_artifacts = {
            name: {
                "path": str(final_paths[name]),
                "bytes": staged[name].stat().st_size,
                "sha256": sha256_file(staged[name]),
                "records": len(reviews),
            }
            for name in (
                "llm_proposals_jsonl",
                "union_proposals_jsonl",
                "review_jsonl",
                "review_csv",
            )
        }
        report = {
            "phase": "P2",
            "stage": config["stage"],
            "run_id": config["run_id"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "code_commit": git_commit(),
            "config_path": str(context["config_path"]),
            "config_sha256": sha256_file(context["config_path"]),
            "duration_seconds": round(time.monotonic() - started, 3),
            "input_artifacts": context["input_artifacts"],
            "selection": {
                "records": len(reviews),
                "ids": [row["review_id"] for row in reviews],
            },
            "statistics": {
                "parse_failures": parse_failures,
                "parse_failure_rate": parse_failure_rate,
                "request_attempts": len(attempts),
                "cache_hits": sum(attempt["cache_hit"] for attempt in attempts),
                "latency_ms_total": sum(float(attempt["latency_ms"]) for attempt in attempts),
                "llm_entities": sum(len(row["entities"]) for row in llm_records),
                "llm_relations": sum(len(row["relations"]) for row in llm_records),
                "entity_types": dict(sorted(entity_types.items())),
                "relation_types": dict(sorted(relation_types.items())),
                "disagreement_flags": dict(sorted(flag_types.items())),
            },
            "success_gate": {
                "passed": gate,
                "maximum_parse_failure_rate": config["success_gates"][
                    "maximum_parse_failure_rate"
                ],
            },
            "outputs": output_artifacts,
            "guards": {
                "human_annotation_started": False,
                "dataset_split_or_frozen": False,
            },
        }
        write_json_atomic(staged["report"], report)
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
    parser.add_argument("--config", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    config_path = args.config.resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    log_path = Path(config["outputs"]["log"])
    event = {
        "phase": "P2",
        "stage": config.get("stage"),
        "run_id": config.get("run_id"),
        "mode": "dry_run" if args.dry_run else "execute",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "config_sha256": sha256_file(config_path),
    }
    started = time.monotonic()
    try:
        context = _load_context(config_path)
        result = dry_run(context) if args.dry_run else execute(context)
        event.update(
            {
                "status": "ok",
                "duration_seconds": round(time.monotonic() - started, 3),
                "result": {
                    "manifest": config["outputs"]["dry_run_manifest"]
                    if args.dry_run
                    else config["outputs"]["report"]
                },
            }
        )
        append_log(log_path, event)
        summary = result["token_budget"] if args.dry_run else result["statistics"]
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
        if not args.dry_run and not result["success_gate"]["passed"]:
            return 2
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
        append_log(log_path, event)
        raise


if __name__ == "__main__":
    raise SystemExit(main())

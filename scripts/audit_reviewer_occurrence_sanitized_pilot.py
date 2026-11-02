#!/usr/bin/env python3
"""No-model paired audit for the four-condition occurrence-sanitized pilot."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path


SYSTEMS = ("zero_shot", "bm25_only", "rag_only", "ec_fsie_full")
BASELINES = SYSTEMS[:-1]
GATE = "JISE_ECFSIE_REVIEW_BASELINE_QWEN_OCCURRENCE_SANITIZED_PILOT_AUDIT_APPROVED"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def entity_set(record: dict) -> set[tuple[int, int, str]]:
    return {(int(e["start"]), int(e["end"]), str(e["type"])) for e in record["entities"]}


def counts(row: dict) -> tuple[int, int, int]:
    gold = entity_set(row["gold"])
    pred = entity_set(row["pred_raw"])
    return len(gold & pred), len(pred - gold), len(gold - pred)


def metrics(parts: list[tuple[int, int, int]]) -> dict:
    tp = sum(x[0] for x in parts)
    fp = sum(x[1] for x in parts)
    fn = sum(x[2] for x in parts)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def paired_bootstrap(
    method: list[tuple[int, int, int]],
    baseline: list[tuple[int, int, int]],
    *,
    reps: int,
    seed: int,
) -> dict:
    rng = random.Random(seed)
    n = len(method)
    deltas: list[float] = []
    for _ in range(reps):
        indices = [rng.randrange(n) for _ in range(n)]
        mf1 = metrics([method[i] for i in indices])["f1"]
        bf1 = metrics([baseline[i] for i in indices])["f1"]
        deltas.append(mf1 - bf1)
    observed = metrics(method)["f1"] - metrics(baseline)["f1"]
    return {
        "observed_f1_delta": observed,
        "ci95_percentile": [percentile(deltas, 0.025), percentile(deltas, 0.975)],
        "probability_delta_gt_zero": sum(value > 0 for value in deltas) / reps,
        "bootstrap_reps": reps,
        "bootstrap_seed": seed,
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

    rows: dict[str, list[dict]] = {}
    hashes: dict[str, str] = {}
    for system in SYSTEMS:
        path = input_root / "pilot20" / system / "per_query.jsonl"
        rows[system] = read_jsonl(path)
        hashes[system] = sha256(path)
        if len(rows[system]) != 20:
            raise ValueError(f"{system}: expected 20 rows")
        if any(row.get("dataset") != "domain_dev" for row in rows[system]):
            raise ValueError(f"{system}: non-domain_dev row found")
    ids = [[str(row["id"]) for row in rows[system]] for system in SYSTEMS]
    if any(sequence != ids[0] for sequence in ids[1:]):
        raise ValueError("query ID/order mismatch across systems")
    for index in range(20):
        golds = [rows[system][index]["gold"] for system in SYSTEMS]
        if any(gold != golds[0] for gold in golds[1:]):
            raise ValueError(f"gold mismatch at {ids[0][index]}")

    per_system_counts = {system: [counts(row) for row in rows[system]] for system in SYSTEMS}
    valid_all = [
        i for i in range(20) if all(not rows[system][i]["parse_failure"] for system in SYSTEMS)
    ]
    report = {
        "gate": GATE,
        "input_root": str(input_root),
        "input_sha256": hashes,
        "query_ids_identical_and_ordered": True,
        "gold_records_identical": True,
        "query_records": 20,
        "common_valid_records": len(valid_all),
        "common_valid_ids": [ids[0][i] for i in valid_all],
        "intention_to_treat": {},
        "common_valid_sensitivity": {},
        "ec_fsie_full_paired_bootstrap": {},
        "common_valid_ec_fsie_full_paired_bootstrap": {},
    }
    for system in SYSTEMS:
        report["intention_to_treat"][system] = {
            **metrics(per_system_counts[system]),
            "parse_failures": sum(bool(row["parse_failure"]) for row in rows[system]),
            "records": 20,
        }
        report["common_valid_sensitivity"][system] = {
            **metrics([per_system_counts[system][i] for i in valid_all]),
            "records": len(valid_all),
        }
    for offset, baseline in enumerate(BASELINES):
        report["ec_fsie_full_paired_bootstrap"][baseline] = paired_bootstrap(
            per_system_counts["ec_fsie_full"],
            per_system_counts[baseline],
            reps=args.bootstrap_reps,
            seed=20260917 + offset,
        )
        report["common_valid_ec_fsie_full_paired_bootstrap"][baseline] = paired_bootstrap(
            [per_system_counts["ec_fsie_full"][i] for i in valid_all],
            [per_system_counts[baseline][i] for i in valid_all],
            reps=args.bootstrap_reps,
            seed=20261017 + offset,
        )

    output_dir.mkdir(parents=True)
    (output_dir / "audit_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with (output_dir / "per_query_counts.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "system", "parse_failure", "tp", "fp", "fn"])
        for i, query_id in enumerate(ids[0]):
            for system in SYSTEMS:
                tp, fp, fn = per_system_counts[system][i]
                writer.writerow([query_id, system, int(rows[system][i]["parse_failure"]), tp, fp, fn])
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

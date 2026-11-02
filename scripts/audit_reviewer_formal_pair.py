#!/usr/bin/env python3
"""No-model paired bootstrap audit for one formal reviewer-baseline contrast."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path


GATE = "JISE_ECFSIE_REVIEW_BASELINE_QWEN_NEUTRAL_ENVELOPE_FORMAL_STATISTICAL_AUDIT_APPROVED"
BASELINES = {"zero_shot", "bm25_only", "rag_only"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def entities(record: dict) -> set[tuple[int, int, str]]:
    return {(int(e["start"]), int(e["end"]), str(e["type"])) for e in record["entities"]}


def row_counts(row: dict) -> tuple[int, int, int]:
    gold = entities(row["gold"])
    pred = entities(row["pred_raw"])
    return len(gold & pred), len(pred - gold), len(gold - pred)


def score(rows: list[tuple[int, int, int]]) -> dict[str, float | int]:
    tp, fp, fn = (sum(x[i] for x in rows) for i in range(3))
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f1}


def quantile(values: list[float], q: float) -> float:
    values = sorted(values)
    pos = (len(values) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(values) - 1)
    return values[lo] * (hi - pos) + values[hi] * (pos - lo)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", required=True)
    parser.add_argument("--baseline", choices=sorted(BASELINES), required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--human-gate", required=True)
    parser.add_argument("--reps", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=20260917)
    args = parser.parse_args()
    if args.human_gate != GATE:
        raise ValueError(f"exact gate required: {GATE}")
    root = Path(args.input_root).resolve()
    output = Path(args.output_dir).resolve()
    if output.exists():
        raise FileExistsError(output)
    paths = {
        "baseline": root / args.baseline / "per_query.jsonl",
        "method": root / "ec_fsie_full" / "per_query.jsonl",
    }
    raw = {name: load(path) for name, path in paths.items()}
    if any(len(rows) != 170 for rows in raw.values()):
        raise ValueError("expected 170 rows per system")
    ids = {name: [str(row["id"]) for row in rows] for name, rows in raw.items()}
    if ids["baseline"] != ids["method"]:
        raise ValueError("ID/order mismatch")
    for i in range(170):
        if raw["baseline"][i]["gold"] != raw["method"][i]["gold"]:
            raise ValueError(f"gold mismatch at {ids['method'][i]}")
    counts = {name: [row_counts(row) for row in rows] for name, rows in raw.items()}
    observed = score(counts["method"])["f1"] - score(counts["baseline"])["f1"]
    rng = random.Random(args.seed)
    deltas = []
    for _ in range(args.reps):
        sampled = [rng.randrange(170) for _ in range(170)]
        deltas.append(
            score([counts["method"][i] for i in sampled])["f1"]
            - score([counts["baseline"][i] for i in sampled])["f1"]
        )
    report = {
        "gate": GATE,
        "contrast": f"ec_fsie_full-minus-{args.baseline}",
        "records": 170,
        "ids_identical_and_ordered": True,
        "gold_records_identical": True,
        "input_sha256": {name: sha256(path) for name, path in paths.items()},
        "parser_failures": {
            name: sum(bool(row.get("parse_failure")) for row in rows) for name, rows in raw.items()
        },
        "scores": {name: score(value) for name, value in counts.items()},
        "observed_f1_delta": observed,
        "paired_bootstrap": {
            "unit": "passage",
            "replicates": args.reps,
            "seed": args.seed,
            "ci95_percentile": [quantile(deltas, 0.025), quantile(deltas, 0.975)],
            "probability_delta_gt_zero": sum(x > 0 for x in deltas) / args.reps,
        },
    }
    output.mkdir(parents=True)
    (output / "audit_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

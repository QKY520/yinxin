#!/usr/bin/env python3
"""Finalize three paired formal contrasts with randomization and Holm correction."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path


GATE = "JISE_ECFSIE_REVIEW_BASELINE_QWEN_NEUTRAL_ENVELOPE_FORMAL_STATISTICAL_AUDIT_APPROVED"
BASELINES = ("zero_shot", "bm25_only", "rag_only")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x]


def entity_set(record: dict) -> set[tuple[int, int, str]]:
    return {(int(e["start"]), int(e["end"]), str(e["type"])) for e in record["entities"]}


def counts(row: dict) -> tuple[int, int, int]:
    gold, pred = entity_set(row["gold"]), entity_set(row["pred_raw"])
    return len(gold & pred), len(pred - gold), len(gold - pred)


def f1(parts: list[tuple[int, int, int]]) -> float:
    tp = sum(x[0] for x in parts)
    fp = sum(x[1] for x in parts)
    fn = sum(x[2] for x in parts)
    return 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0


def randomization_p(method, baseline, reps: int, seed: int) -> float:
    observed = abs(f1(method) - f1(baseline))
    rng = random.Random(seed)
    extreme = 0
    for _ in range(reps):
        left, right = [], []
        for m, b in zip(method, baseline):
            if rng.getrandbits(1):
                left.append(m); right.append(b)
            else:
                left.append(b); right.append(m)
        if abs(f1(left) - f1(right)) >= observed - 1e-15:
            extreme += 1
    return (extreme + 1) / (reps + 1)


def holm(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    adjusted = [0.0] * len(values)
    running = 0.0
    n = len(values)
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (n - rank) * values[index]))
        adjusted[index] = running
    return adjusted


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--formal-root", required=True)
    p.add_argument("--pair-root", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--human-gate", required=True)
    p.add_argument("--reps", type=int, default=10_000)
    args = p.parse_args()
    if args.human_gate != GATE:
        raise ValueError("wrong gate")
    formal, pairs, output = map(lambda x: Path(x).resolve(), (args.formal_root, args.pair_root, args.output_dir))
    if output.exists():
        raise FileExistsError(output)
    method_rows = load_jsonl(formal / "ec_fsie_full" / "per_query.jsonl")
    method_counts = [counts(x) for x in method_rows]
    rows, raw_ps = [], []
    for offset, baseline in enumerate(BASELINES):
        pair_path = pairs / baseline / "audit_report.json"
        pair = load_json(pair_path)
        baseline_rows = load_jsonl(formal / baseline / "per_query.jsonl")
        if [x["id"] for x in baseline_rows] != [x["id"] for x in method_rows]:
            raise ValueError(f"ID mismatch: {baseline}")
        p_raw = randomization_p(method_counts, [counts(x) for x in baseline_rows], args.reps, 20261017 + offset)
        raw_ps.append(p_raw)
        rows.append({
            "baseline": baseline,
            "f1_delta": pair["observed_f1_delta"],
            "bootstrap_ci95": pair["paired_bootstrap"]["ci95_percentile"],
            "randomization_p_raw": p_raw,
            "pair_report_sha256": sha256(pair_path),
        })
    adjusted = holm(raw_ps)
    for row, value in zip(rows, adjusted):
        row["holm_p_three_comparisons"] = value
        row["passes_alpha_0_05"] = value < 0.05 and row["bootstrap_ci95"][0] > 0
    report = {
        "gate": GATE,
        "family": "EC-FSIE-full versus three Qwen baselines on the same 170 passages",
        "randomization": {"method": "paired passage-level label swap, two-sided", "replicates": args.reps},
        "multiplicity": "Holm correction across three primary F1 contrasts",
        "contrasts": rows,
        "all_three_pass": all(x["passes_alpha_0_05"] for x in rows),
    }
    output.mkdir(parents=True)
    target = output / "final_statistics.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

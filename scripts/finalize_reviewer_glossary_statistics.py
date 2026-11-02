#!/usr/bin/env python3
"""No-model statistical audit for the five paper-facing Qwen contrasts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path


GATE = "JISE_ECFSIE_REVIEW_GLOSSARY_ONLY_STATISTICAL_AUDIT_APPROVED"
SYSTEMS = ("zero_shot", "bm25_only", "rag_only", "glossary_only", "ec_fsie_full")
CONTRASTS = (
    ("ec_fsie_full", "zero_shot"),
    ("ec_fsie_full", "bm25_only"),
    ("ec_fsie_full", "rag_only"),
    ("ec_fsie_full", "glossary_only"),
    ("glossary_only", "zero_shot"),
)


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def entity_set(record: dict) -> set[tuple[int, int, str]]:
    return {(int(x["start"]), int(x["end"]), str(x["type"])) for x in record["entities"]}


def row_counts(row: dict) -> tuple[int, int, int]:
    gold, pred = entity_set(row["gold"]), entity_set(row["pred_raw"])
    return len(gold & pred), len(pred - gold), len(gold - pred)


def score(parts: list[tuple[int, int, int]]) -> dict[str, float | int]:
    tp, fp, fn = (sum(x[i] for x in parts) for i in range(3))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] * (hi - pos) + ordered[hi] * (pos - lo)


def bootstrap_delta(left, right, reps: int, seed: int) -> tuple[list[float], float]:
    rng = random.Random(seed)
    n = len(left)
    values = []
    for _ in range(reps):
        indices = [rng.randrange(n) for _ in range(n)]
        values.append(score([left[i] for i in indices])["f1"] - score([right[i] for i in indices])["f1"])
    return [quantile(values, 0.025), quantile(values, 0.975)], sum(x > 0 for x in values) / reps


def randomization_p(left, right, reps: int, seed: int) -> float:
    observed = abs(score(left)["f1"] - score(right)["f1"])
    rng = random.Random(seed)
    extreme = 0
    for _ in range(reps):
        a, b = [], []
        for x, y in zip(left, right):
            if rng.getrandbits(1):
                a.append(x); b.append(y)
            else:
                a.append(y); b.append(x)
        if abs(score(a)["f1"] - score(b)["f1"]) >= observed - 1e-15:
            extreme += 1
    return (extreme + 1) / (reps + 1)


def holm(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    adjusted = [0.0] * len(values)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(values) - rank) * values[index]))
        adjusted[index] = running
    return adjusted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--formal-root", required=True)
    parser.add_argument("--glossary-path", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--human-gate", required=True)
    parser.add_argument("--reps", type=int, default=10_000)
    args = parser.parse_args()
    if args.human_gate != GATE:
        raise ValueError(f"exact gate required: {GATE}")
    if args.reps < 1000:
        raise ValueError("at least 1000 replicates required")
    root, glossary, output = Path(args.formal_root).resolve(), Path(args.glossary_path).resolve(), Path(args.output_dir).resolve()
    if output.exists():
        raise FileExistsError(output)
    paths = {name: root / name / "per_query.jsonl" for name in SYSTEMS if name != "glossary_only"}
    paths["glossary_only"] = glossary
    rows = {name: load_jsonl(path) for name, path in paths.items()}
    if any(len(value) != 170 for value in rows.values()):
        raise ValueError("expected exactly 170 rows per system")
    reference_ids = [str(x["id"]) for x in rows["zero_shot"]]
    reference_gold = [x["gold"] for x in rows["zero_shot"]]
    for name in SYSTEMS:
        if [str(x["id"]) for x in rows[name]] != reference_ids:
            raise ValueError(f"ID/order mismatch: {name}")
        if [x["gold"] for x in rows[name]] != reference_gold:
            raise ValueError(f"gold mismatch: {name}")
    parts = {name: [row_counts(x) for x in rows[name]] for name in SYSTEMS}
    raw_ps, contrasts = [], []
    for index, (left_name, right_name) in enumerate(CONTRASTS):
        ci, probability = bootstrap_delta(parts[left_name], parts[right_name], args.reps, 20260918 + index)
        p_raw = randomization_p(parts[left_name], parts[right_name], args.reps, 20261918 + index)
        raw_ps.append(p_raw)
        contrasts.append({
            "contrast": f"{left_name}-minus-{right_name}",
            "f1_delta": score(parts[left_name])["f1"] - score(parts[right_name])["f1"],
            "bootstrap_ci95": ci,
            "bootstrap_probability_delta_gt_zero": probability,
            "randomization_p_raw": p_raw,
        })
    for item, adjusted in zip(contrasts, holm(raw_ps)):
        item["holm_p_five_comparisons"] = adjusted
        item["passes_alpha_0_05_positive"] = adjusted < 0.05 and item["bootstrap_ci95"][0] > 0
    report = {
        "gate": GATE,
        "records": 170,
        "ids_identical_and_ordered": True,
        "gold_records_identical": True,
        "bootstrap": {"unit": "passage", "replicates": args.reps, "ci": "percentile 95%"},
        "randomization": {"unit": "passage", "replicates": args.reps, "method": "paired label swap, two-sided"},
        "multiplicity": "Holm correction across five paper-facing F1 contrasts",
        "input_sha256": {name: sha256(paths[name]) for name in SYSTEMS},
        "parser_failures": {name: sum(bool(x.get("parse_failure")) for x in rows[name]) for name in SYSTEMS},
        "scores": {name: score(parts[name]) for name in SYSTEMS},
        "contrasts": contrasts,
    }
    output.mkdir(parents=True)
    (output / "final_statistics.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with (output / "contrasts.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(contrasts[0]))
        writer.writeheader(); writer.writerows(contrasts)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

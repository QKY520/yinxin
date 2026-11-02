"""Verify arithmetic and cross-file consistency without resampling or model calls."""
from pathlib import Path
import csv
import hashlib
import json
import math
import statistics

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8-sig"))


def close(a, b):
    assert math.isclose(a, b, rel_tol=0, abs_tol=1e-12), (a, b)


def holm(values):
    result = [0.0] * len(values)
    last = 0.0
    for rank, index in enumerate(sorted(range(len(values)), key=values.__getitem__)):
        last = max(last, min(1.0, values[index] * (len(values) - rank)))
        result[index] = last
    return result


def main():
    with (DATA / "raw_metrics_14_systems.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 14
    metrics = {r["system"]: r for r in rows}
    assert len(metrics) == 14
    for row in rows:
        tp, fp, fn = (int(row[k]) for k in ("tp", "fp", "fn"))
        assert int(row["texts"]) == 170 and tp + fn == 954
        assert int(row["predicted_entities"]) == tp + fp
        for name, value in (("precision", tp / (tp + fp)), ("recall", tp / (tp + fn)),
                            ("f1", 2 * tp / (2 * tp + fp + fn))):
            close(float(row[name]), value)
    stats = load("comparisons.json")
    protocol = load("frozen_statistics_protocol.json")
    assert len(stats["f1_family"]) == 13 and len(stats["rag_secondary_family"]) == 3
    assert [[r["left"], r["right"]] for r in stats["f1_family"]] == protocol["f1_family"]
    assert [r["metric"] for r in stats["rag_secondary_family"]] == protocol["rag_secondary_family"]
    for family, adjusted, csv_name in (("f1_family", "p_holm_13", "f1_comparisons_13.csv"),
                                      ("rag_secondary_family", "p_holm_3", "rag_secondary_3.csv")):
        with (DATA / csv_name).open(encoding="utf-8-sig", newline="") as f:
            csv_rows = list(csv.DictReader(f))
        assert len(csv_rows) == len(stats[family])
        adjusted_values = holm([r["p_two_sided"] for r in stats[family]])
        for row, adj, csv_row in zip(stats[family], adjusted_values, csv_rows):
            close(row[adjusted], adj)
            assert row["replicates"] == protocol["replicates"] == 10000
            assert row["ci95"][0] <= row["ci95"][1]
            for key in ("difference_left_minus_right", "p_two_sided", adjusted):
                close(float(csv_row[key]), row[key])
            assert json.loads(csv_row["ci95"]) == row["ci95"]
            if family == "f1_family":
                assert (csv_row["left"], csv_row["right"]) == (row["left"], row["right"])
                expected = float(metrics[row["left"]]["f1"]) - float(metrics[row["right"]]["f1"])
            else:
                assert csv_row["metric"] == row["metric"]
                expected = float(metrics["full"][row["metric"]]) - float(metrics["knn_g"][row["metric"]])
            close(row["difference_left_minus_right"], expected)
    for group, prefix in (("random", "random"), ("uie_ft", "uie_ft")):
        for metric in ("precision", "recall", "f1", "fp"):
            values = [float(metrics[prefix + str(seed)][metric]) for seed in (42, 43, 44)]
            close(statistics.mean(values), stats["seed_descriptive"][group][metric]["mean"])
            close(statistics.stdev(values), stats["seed_descriptive"][group][metric]["sample_sd"])
    calibration = load("agreement_ci.json")
    assert calibration["texts"] == 100 and calibration["labels_changed"] is False
    for row in calibration["results"].values():
        close(row["f1"], 2 * row["matched"] / (row["a"] + row["b"]))
    manifest_path = ROOT / "SHA256_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file()}
        expected = {r["path"] for r in manifest["files"]} | {"SHA256_manifest.json"}
        assert actual == expected, {"extra": sorted(actual - expected), "missing": sorted(expected - actual)}
        for row in manifest["files"]:
            blob = (ROOT / row["path"]).read_bytes()
            assert len(blob) == row["bytes"]
            assert hashlib.sha256(blob).hexdigest() == row["sha256"], row["path"]
    print(json.dumps({"status": "PASS", "metric_rows": 14, "f1_contrasts": 13,
                      "rag_endpoints": 3, "resampling_performed": False,
                      "model_calls": 0, "frozen_data_edited": False}, indent=2))


if __name__ == "__main__":
    main()

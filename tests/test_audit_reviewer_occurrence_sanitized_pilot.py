import pytest

from scripts.audit_reviewer_occurrence_sanitized_pilot import metrics, paired_bootstrap


def test_metrics_aggregate_micro_counts() -> None:
    result = metrics([(1, 2, 3), (4, 0, 1)])
    assert result == {
        "tp": 5,
        "fp": 2,
        "fn": 4,
        "precision": 5 / 7,
        "recall": 5 / 9,
        "f1": pytest.approx(0.625),
    }


def test_paired_bootstrap_is_deterministic_and_positive() -> None:
    method = [(2, 0, 0), (1, 0, 1)]
    baseline = [(0, 1, 2), (1, 1, 1)]
    first = paired_bootstrap(method, baseline, reps=1000, seed=7)
    second = paired_bootstrap(method, baseline, reps=1000, seed=7)
    assert first == second
    assert first["observed_f1_delta"] > 0
    assert first["probability_delta_gt_zero"] > 0.9


def test_paired_bootstrap_confidence_interval_is_ordered() -> None:
    result = paired_bootstrap([(1, 0, 0)], [(0, 0, 1)], reps=20, seed=1)
    assert result["ci95_percentile"][0] <= result["observed_f1_delta"]
    assert result["ci95_percentile"][1] >= result["observed_f1_delta"]

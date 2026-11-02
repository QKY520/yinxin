from scripts.finalize_reviewer_glossary_statistics import holm, quantile, score


def test_score_micro_f1():
    assert score([(2, 1, 1), (1, 0, 2)]) == {
        "tp": 3, "fp": 1, "fn": 3, "precision": 0.75, "recall": 0.5, "f1": 0.6
    }


def test_holm_is_monotone_in_sorted_order():
    assert holm([0.01, 0.04, 0.03]) == [0.03, 0.06, 0.06]


def test_quantile_interpolates():
    assert quantile([0.0, 1.0], 0.25) == 0.25

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.build_bm25_retrieval import BM25Index, CorpusRow, tokenize
from scripts.run_bert_crf_baseline import bio_to_entities, build_bio_label_vocab, build_linear_chain_crf, entities_to_bio
from scripts.run_reviewer_baselines import build_qwen_baseline_config, build_run_specs, materialize_b1_configs, validate_manifest


def manifest() -> dict:
    return {
        "gate": "JISE_ECFSIE_REVIEW_BASELINE_EXPERIMENTS_APPROVED",
        "task": "ner",
        "datasets": {
            "domain": {"support": "/data/domain_support.jsonl", "tune": "/data/domain_dev.jsonl", "evaluation": "/data/domain_test.jsonl"},
            "cluener": {"support": "/data/cluener_support.jsonl", "tune": "/data/cluener_tune.jsonl", "evaluation": "/data/cluener_dev.jsonl"},
        },
        "evaluation_policy": {"test_is_read_only": True, "tune_only_on_declared_tune_split": True},
        "seeds": [42, 43, 44], "primary_k": 5,
        "outputs": {"remote_root": "/tmp/reviewer", "no_overwrite_existing": True},
    }


def test_manifest_and_expected_matrix():
    value = manifest()
    validate_manifest(value)
    specs = build_run_specs(value)
    assert len(specs) == 54
    assert len({spec.run_id for spec in specs}) == 54
    assert all("test" not in spec.tune_path.lower() for spec in specs)


def test_manifest_rejects_test_tuning():
    value = manifest()
    value["datasets"]["domain"]["tune"] = "/data/domain_test.jsonl"
    with pytest.raises(ValueError, match="test path"):
        validate_manifest(value)


def test_bm25_prefers_exact_term_and_is_deterministic():
    index = BM25Index([CorpusRow("a", "雷达 天线"), CorpusRow("b", "发动机"), CorpusRow("c", "雷达 模块")])
    assert tokenize("雷达") == ["雷", "达"]
    first = index.retrieve("雷达", top_k=3)
    second = index.retrieve("雷达", top_k=3)
    assert first == second
    assert {first[0]["id"], first[1]["id"]} == {"a", "c"}


def test_bio_round_trip_and_overlap_rejection():
    text = "甲乙丙丁"
    entities = [{"start": 0, "end": 2, "type": "EQUIPMENT"}, {"start": 2, "end": 4, "type": "MODULE"}]
    labels = entities_to_bio(text, entities, allowed_types=("EQUIPMENT", "MODULE"))
    assert bio_to_entities(labels) == [(0, 2, "EQUIPMENT"), (2, 4, "MODULE")]
    with pytest.raises(ValueError, match="overlapping"):
        entities_to_bio(text, [{"start": 0, "end": 2, "type": "EQUIPMENT"}, {"start": 1, "end": 3, "type": "MODULE"}], allowed_types=("EQUIPMENT", "MODULE"))


def test_crf_loss_and_decode_shapes():
    torch = pytest.importorskip("torch")
    crf = build_linear_chain_crf()(3)
    emissions = torch.zeros((2, 4, 3), dtype=torch.float32)
    tags = torch.zeros((2, 4), dtype=torch.long)
    mask = torch.tensor([[True, True, True, True], [True, True, False, False]])
    loss = crf.neg_log_likelihood(emissions, tags, mask)
    assert torch.isfinite(loss)
    paths = crf.decode(emissions, mask)
    assert [len(path) for path in paths] == [4, 2]


def test_bio_label_vocab_is_deterministic():
    tags, mapping = build_bio_label_vocab(("EQUIPMENT", "MODULE"))
    assert tags == ["O", "B-EQUIPMENT", "I-EQUIPMENT", "B-MODULE", "I-MODULE"]
    assert mapping["I-MODULE"] == 4


def test_qwen_config_variants_are_locked_without_authorization(tmp_path):
    spec = build_run_specs(manifest())[0]
    config = build_qwen_baseline_config(spec)
    assert config["execution"]["authorized"] is False
    assert config["examples"] == {"mode": "none", "k": 0, "seed": 42}
    assert "glossary" not in config and "rag" not in config
    paths = materialize_b1_configs(manifest(), tmp_path)
    assert len(paths) == 24
    assert len({path.name for path in paths}) == 24
    with pytest.raises(FileExistsError):
        materialize_b1_configs(manifest(), tmp_path)


def test_bert_cli_refuses_evaluation_without_explicit_flag():
    import subprocess
    import sys
    result = subprocess.run(
        [sys.executable, "scripts/run_bert_crf_baseline.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "--allow-evaluation" in result.stdout


def test_dispatcher_bert_validates_config_before_execution(tmp_path):
    config = tmp_path / "bert.yaml"
    config.write_text("support: /x\n", encoding="utf-8")
    from scripts.dispatch_reviewer_baseline import dispatch_bert
    with pytest.raises(ValueError, match="missing keys"):
        dispatch_bert(config, allow_evaluation=False)

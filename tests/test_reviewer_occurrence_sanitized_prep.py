from __future__ import annotations

import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.prepare_reviewer_occurrence_sanitized_configs import OUT, PREP_GATE, SOURCE, build
from scripts.authorize_reviewer_occurrence_sanitized_pilot import GATE, PHASE, authorize
from scripts.run_p3_extraction import validate_execution_gate


def load_base() -> dict:
    return yaml.safe_load(SOURCE.read_text(encoding="utf-8"))


def test_sentinel_is_locked_and_uses_proven_p5_protocol() -> None:
    cfg = load_base()
    assert cfg["execution"] == {
        "phase": "REVIEWER_QWEN_OCCURRENCE_SANITIZED_PREP",
        "authorized": False,
        "human_gate": PREP_GATE,
        "model_calls_allowed": False,
        "gpu_required": True,
    }
    assert cfg["query_limit"] == 5
    assert cfg["parsing"]["output_mode"] == "occurrence"
    assert cfg["parsing"]["drop_invalid_entities"] is True
    assert cfg["parsing"]["constrained_json_schema"] is False
    assert cfg["generation"]["max_tokens"] == 768
    assert cfg["protocol"]["parser_failure_ceiling"] == 0.25


def test_pilot_configs_are_fair_locked_and_leakage_safe() -> None:
    base = load_base()
    configs = {system: build(system, base) for system in ("zero_shot", "bm25_only", "rag_only", "ec_fsie_full")}
    for system, cfg in configs.items():
        assert cfg["execution"]["authorized"] is False
        assert cfg["execution"]["model_calls_allowed"] is False
        assert cfg["query_limit"] == 20
        assert cfg["parsing"] == base["parsing"]
        assert "domain_test" not in yaml.safe_dump(cfg)
        assert cfg["protocol"]["system"] == system
        assert cfg["protocol"]["gold_or_bert_repair_forbidden"] is True
    assert "rag" not in configs["zero_shot"]
    assert configs["bm25_only"]["rag"]["mode"] == "replay_manifest"
    assert "bm25_top3" in configs["bm25_only"]["rag"]["replay_manifest_path"]
    assert "dense_repair" in configs["rag_only"]["rag"]["replay_manifest_path"]
    assert configs["ec_fsie_full"]["examples"]["mode"] == "knn_replay"
    assert "p3_domain_dev50_b_knn" in configs["ec_fsie_full"]["examples"]["source_per_query_path"]
    assert configs["ec_fsie_full"]["glossary"]["max_entries"] == 20


def test_generated_paths_remain_inside_preparation_directory() -> None:
    assert OUT == ROOT / "configs/reviewer_qwen_occurrence_sanitized_20260917"


def test_future_exact_gate_creates_runner_accepted_execution_copy() -> None:
    runtime = authorize(load_base(), GATE)
    assert runtime["execution"]["phase"] == PHASE
    assert runtime["execution"]["authorized"] is True
    assert runtime["execution"]["model_calls_allowed"] is True
    validate_execution_gate(runtime["execution"])


def test_wrong_future_gate_is_rejected() -> None:
    try:
        authorize(load_base(), "WRONG_GATE")
    except ValueError as exc:
        assert GATE in str(exc)
    else:
        raise AssertionError("wrong gate must be rejected")

from scripts.prepare_reviewer_glossary_only_preflight import build_config


def test_glossary_only_changes_only_evidence_and_identity():
    source = {
        "run_id": "reviewer-qwen-neutral-envelope-formal-zero_shot-prep",
        "config_name": "reviewer_qwen_neutral_envelope_formal_zero_shot",
        "execution": {},
        "data": {"query_path": "/root/autodl-tmp/data/domain_test.jsonl"},
        "examples": {"mode": "none", "k": 0, "seed": 42},
        "generation": {"temperature": 0.0, "top_p": 1.0, "max_tokens": 768, "seed": 42},
        "parsing": {"ner_only_envelope_policy": "entities_or_entities_relations_v2"},
        "protocol": {"system": "zero_shot", "run_order": ["zero_shot"]},
        "cache": {},
        "outputs": {},
    }
    result = build_config(source)
    assert result["examples"] == source["examples"]
    assert result["generation"] == source["generation"]
    assert "rag" not in result
    assert result["glossary"]["max_entries"] == 20
    assert result["glossary"]["match_mode"] == "substring"
    assert result["execution"]["authorized"] is False
    assert result["execution"]["model_calls_allowed"] is False

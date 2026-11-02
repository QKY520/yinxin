from scripts.authorize_reviewer_glossary_only_formal import GATE, PHASE, authorize
from scripts.run_p3_extraction import validate_execution_gate


def source_config() -> dict:
    return {
        "run_id": "prep",
        "config_name": "prep",
        "execution": {},
        "data": {"dataset": "domain_test", "query_path": "test"},
        "query_limit": 170,
        "cache": {},
        "outputs": {},
    }


def test_exact_gate_authorizes_only_formal_170() -> None:
    result = authorize(source_config(), GATE)
    validate_execution_gate(result["execution"])
    assert result["execution"]["phase"] == PHASE
    assert result["data"]["dataset"] == "domain_test"
    assert result["query_limit"] == 170


def test_wrong_gate_is_rejected() -> None:
    try:
        authorize(source_config(), "WRONG")
    except ValueError as exc:
        assert GATE in str(exc)
    else:
        raise AssertionError("wrong gate must be rejected")

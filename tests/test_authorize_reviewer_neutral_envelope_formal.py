from scripts.authorize_reviewer_neutral_envelope_formal import GATE, PHASE, authorize
from scripts.run_p3_extraction import validate_execution_gate


def test_exact_gate_authorizes_formal_config() -> None:
    config = {"run_id": "formal-prep", "execution": {}}
    result = authorize(config, GATE)
    assert result["run_id"] == "formal"
    assert result["execution"]["phase"] == PHASE
    validate_execution_gate(result["execution"])


def test_wrong_gate_is_rejected() -> None:
    try:
        authorize({"run_id": "formal-prep"}, "WRONG")
    except ValueError as exc:
        assert GATE in str(exc)
    else:
        raise AssertionError("wrong gate must be rejected")

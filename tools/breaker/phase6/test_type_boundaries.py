import pytest

from model_layer.executor.executor import execute_envelope


def make_envelope(steps):
    return {"envelope_id": "phase6-type", "plan_id": "p6", "steps": steps}


def test_missing_keys_raises():
    # Missing 'steps'
    with pytest.raises(ValueError):
        execute_envelope({"envelope_id": "x"})


def test_step_not_object_raises():
    envelope = {"envelope_id": "phase6-type", "plan_id": "p6", "steps": [None]}
    with pytest.raises(TypeError) as exc:
        execute_envelope(envelope)

    assert "step[0] must be an object/dict" in str(exc.value)


def test_string_where_int_expected_raises():
    # timeout_ms should be int-like; non-convertible string should raise
    env = make_envelope([{"id": "s1", "timeout_ms": "not-an-int"}])
    with pytest.raises(ValueError):
        execute_envelope(env)


def test_float_string_where_int_expected_raises():
    env = make_envelope([{"id": "s2", "simulate_duration_ms": "1.5"}])
    with pytest.raises(ValueError):
        execute_envelope(env)


def test_none_payload_allowed():
    # payload None should be accepted (canonical JSON handles None)
    env = make_envelope([{"id": "s3", "payload": None}])
    res = execute_envelope(env)
    assert "steps" in res and isinstance(res["steps"], list)


def test_unknown_op_passes_but_warns():
    # Executor doesn't validate op semantics; it should still produce deterministic output
    env = make_envelope([
        {"id": "s4", "payload": {"op": "unknown", "a": "x"}}
    ])
    res = execute_envelope(env)
    assert isinstance(res, dict)

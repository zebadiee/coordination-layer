import pytest
import copy

from model_layer.executor.executor import execute_envelope


def make_env(steps):
    return {"envelope_id": "phase6-schema", "plan_id": "p6-schema", "steps": steps}


def test_unexpected_deep_type_accepted_and_deterministic():
    payload = {"a": {"b": {"c": [1, "two", {"three": 3}]}}}
    env = make_env([
        {"id": "s1", "payload": payload},
        {"id": "s2", "payload": copy.deepcopy(payload)},
    ])

    t1 = execute_envelope(env)
    t2 = execute_envelope(env)
    assert t1 == t2, "Deep schema drift caused nondeterministic traces"


def test_invalid_simulate_duration_type_raises():
    env = make_env([
        {"id": "s1", "simulate_duration_ms": {"bad": "dict"}},
    ])

    with pytest.raises((TypeError, ValueError)):
        execute_envelope(env)


def test_missing_ids_and_extra_fields_handled_deterministically():
    # step without id should be accepted and produce deterministic traces
    env = make_env([
        {"payload": {"x": 1}, "extra": "field"},
        {"payload": {"x": 1}, "extra": "field"},
    ])

    t1 = execute_envelope(env)
    t2 = execute_envelope(env)
    assert t1 == t2


def test_mixed_types_in_list_are_deterministic():
    payload = {"mix": [1, 2.5, "three", {"four": 4}, [5, "six"]]}
    env = make_env([{"id": "s1", "payload": payload}])

    t1 = execute_envelope(env)
    t2 = execute_envelope(env)
    assert t1 == t2

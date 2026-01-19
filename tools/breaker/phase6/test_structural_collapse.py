import pytest

from model_layer.executor.executor import execute_envelope


def test_empty_steps_rejected():
    env = {"envelope_id": "phase6-struct", "plan_id": "p6-struct", "steps": []}
    # We expect an explicit rejection for empty plans; accept ValueError or TypeError
    with pytest.raises((ValueError, TypeError)):
        execute_envelope(env)


def test_unknown_op_deterministic():
    env = {
        "envelope_id": "phase6-struct-unknown",
        "plan_id": "p6-struct",
        "steps": [{"id": "s1", "payload": {"op": "unknown-op"}}],
    }

    t1 = execute_envelope(env)
    t2 = execute_envelope(env)
    assert t1 == t2


def test_missing_id_handled_deterministically():
    env = {"envelope_id": "phase6-struct-missingid", "plan_id": "p6-struct", "steps": [{"payload": {"x": 1}}]}

    t1 = execute_envelope(env)
    t2 = execute_envelope(env)
    assert t1 == t2


def test_many_steps_bounded_or_deterministic():
    # large number of steps to test structural collapse due to size
    n = 20000
    steps = [{"id": f"s{i}", "payload": {"i": i}} for i in range(n)]
    env = {"envelope_id": "phase6-struct-big", "plan_id": "p6-struct", "steps": steps}

    try:
        t1 = execute_envelope(env)
        t2 = execute_envelope(env)
        assert t1 == t2
    except Exception as e:
        assert isinstance(e, (MemoryError, ValueError))

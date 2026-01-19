import pytest

from model_layer.executor.executor import execute_envelope


@pytest.mark.parametrize("size", [20000, 100000, 200000])
def test_oversized_payload_modes(size):
    payload = {"big": [0] * size}
    env = {
        "envelope_id": "phase6-oversized",
        "plan_id": "p6-oversized",
        "steps": [
            {"id": "s1", "payload": payload},
            {"id": "s2", "payload": payload},
        ],
    }

    try:
        t1 = execute_envelope(env)
        t2 = execute_envelope(env)

        # Deterministic across runs
        assert t1 == t2, "Oversized payload produced nondeterministic traces"

        phs = [s["payload_hash"] for s in t1["steps"]]
        assert all(isinstance(h, str) for h in phs)
    except Exception as e:
        # Acceptable controlled failures
        assert isinstance(e, (MemoryError, ValueError)), f"Unexpected exception: {type(e)}"

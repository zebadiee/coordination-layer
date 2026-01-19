import math
import hashlib
import json

from model_layer.executor.executor import execute_envelope


def make_env_with_payload(payload):
    return {
        "envelope_id": "phase6-values",
        "plan_id": "p6-values",
        "steps": [{"id": "s", "payload": payload}],
    }


def hash_trace(trace):
    return hashlib.sha256(json.dumps(trace, sort_keys=True).encode()).hexdigest()


def test_large_integers_deterministic():
    payload = {"big1": 2**256, "big2": 2**1024}
    env = make_env_with_payload(payload)

    t1 = execute_envelope(env)
    t2 = execute_envelope(env)

    assert t1 == t2


def test_negative_and_zero_values():
    payload = {"neg": -999999999999, "zero": 0}
    env = make_env_with_payload(payload)

    t1 = execute_envelope(env)
    t2 = execute_envelope(env)
    assert t1 == t2


def test_simulate_duration_timeout_behavior():
    env = {
        "envelope_id": "phase6-timeout",
        "plan_id": "p6-timeout",
        "steps": [
            {"id": "s1", "simulate_duration_ms": 10, "timeout_ms": 5},
            {"id": "s2", "simulate_duration_ms": 0, "timeout_ms": 5},
        ],
    }

    t = execute_envelope(env)
    statuses = [s["status"] for s in t["steps"]]
    assert statuses[0] == "timed_out"
    assert statuses[1] == "ok"


def test_nan_in_payload_handling():
    payload = {"nan": float("nan")}
    env = make_env_with_payload(payload)

    try:
        t1 = execute_envelope(env)
        t2 = execute_envelope(env)
        assert t1 == t2
    except Exception as e:
        # Accept deterministic exception (ValueError) if JSON can't handle it
        assert isinstance(e, (ValueError, TypeError))

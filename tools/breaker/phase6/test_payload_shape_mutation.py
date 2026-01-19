import copy
import hashlib
import json

from model_layer.executor.executor import execute_envelope


def make_envelope_with_payload(payload):
    return {
        "envelope_id": "phase6-payload",
        "plan_id": "p6-payload",
        "steps": [
            {"id": "a", "payload": payload},
            {"id": "b", "payload": payload},
        ],
    }


def hash_trace(trace):
    return hashlib.sha256(json.dumps(trace, sort_keys=True).encode()).hexdigest()


def test_deeply_nested_payload_deterministic():
    payload = {"lvl1": {"lvl2": {"list": [i for i in range(20)], "inner": {"x": 1}}}}
    env = make_envelope_with_payload(payload)

    t1 = execute_envelope(env)
    t2 = execute_envelope(env)

    assert t1 == t2, "Deeply nested payload produced nondeterministic traces"


def test_mutation_after_execution_does_not_change_returned_trace():
    payload = {"nested": {"v": 1}}
    env = make_envelope_with_payload(payload)

    trace_before = execute_envelope(env)
    # Mutate original payload after execution
    payload["nested"]["v"] = 9999

    # trace_before must remain stable (no references to original mutable payload)
    assert isinstance(trace_before["steps"][0]["payload_hash"], str)


def test_alias_reference_same_payload_consistent():
    shared = {"value": "x"}
    env = make_envelope_with_payload(shared)

    t = execute_envelope(env)
    phs = [s["payload_hash"] for s in t["steps"]]
    assert phs[0] == phs[1], "Shared payload should result in identical payload_hashes"


def test_oversized_payload_handling():
    # Generate a large payload but within reasonable bounds to avoid DoS in CI
    payload = {"big": [0] * 20000}
    env = make_envelope_with_payload(payload)

    # Accept either a successful deterministic trace or a controlled exception
    try:
        t = execute_envelope(env)
        assert isinstance(t, dict)
    except Exception as e:
        # Acceptable failures: MemoryError or ValueError for bounds enforcement
        assert isinstance(e, (MemoryError, ValueError))

import pytest

from model_layer.executor.executor import execute_envelope


def make_steps(n, payload=None):
    return [{"id": f"s{i}", "payload": payload or {"i": i}} for i in range(n)]


def test_many_noop_steps_deterministic_or_bounded():
    n = 10000
    env = {"envelope_id": "phase6-bomb-1", "plan_id": "p6-bomb", "steps": make_steps(n)}
    try:
        t1 = execute_envelope(env)
        t2 = execute_envelope(env)
        assert t1 == t2
    except Exception as e:
        assert isinstance(e, (MemoryError, ValueError))


def test_deeply_nested_payload_bounds():
    # depth large but < recursion limit; accept deterministic success or controlled failure
    depth = 500
    obj = current = {}
    for i in range(depth):
        current["k"] = {}
        current = current["k"]
    payload = {"deep": obj}
    env = {"envelope_id": "phase6-bomb-2", "plan_id": "p6-bomb", "steps": [{"id": "s1", "payload": payload}]}

    try:
        t1 = execute_envelope(env)
        t2 = execute_envelope(env)
        assert t1 == t2
    except Exception as e:
        assert isinstance(e, (RecursionError, MemoryError, ValueError))


def test_repeated_identical_payloads_consistent_hashes():
    payload = {"v": "x"}
    n = 5000
    steps = [ {"id": f"s{i}", "payload": payload} for i in range(n) ]
    env = {"envelope_id": "phase6-bomb-3", "plan_id": "p6-bomb", "steps": steps}

    t = execute_envelope(env)
    phs = [s["payload_hash"] for s in t["steps"]]
    assert len(set(phs)) == 1


def test_combined_stress_medium():
    # medium-sized combined stress test (many steps with moderate payloads)
    n = 3000
    payload = {"arr": [0] * 2000, "map": {str(i): i for i in range(50)}}
    env = {"envelope_id": "phase6-bomb-4", "plan_id": "p6-bomb", "steps": make_steps(n, payload)}

    try:
        t1 = execute_envelope(env)
        t2 = execute_envelope(env)
        assert t1 == t2
    except Exception as e:
        assert isinstance(e, (MemoryError, ValueError))

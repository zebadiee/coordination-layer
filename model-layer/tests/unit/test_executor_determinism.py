from model_layer.executor.executor import execute_envelope


def test_determinism():
    envelope = {
        "envelope_id": "e4",
        "plan_id": "p4",
        "steps": [
            {"id": "s1", "payload": {"x": 1}},
            {"id": "s2", "payload": {"y": 2}},
        ],
    }
    t1 = execute_envelope(envelope)
    t2 = execute_envelope(envelope)
    assert t1 == t2

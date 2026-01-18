from model_layer.executor.executor import execute_envelope


def test_quorum_verification():
    # three steps in same group, two will have same result
    envelope = {
        "envelope_id": "e3",
        "plan_id": "p3",
        "steps": [
            {"id": "s1", "group": "g1", "payload": {"v": 1}},
            {"id": "s2", "group": "g1", "payload": {"v": 1}},
            {"id": "s3", "group": "g1", "payload": {"v": 2}},
        ],
    }
    trace = execute_envelope(envelope)
    assert trace["quorum"]["g1"] is True

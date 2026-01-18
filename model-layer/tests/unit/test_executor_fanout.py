from model_layer.executor.executor import execute_envelope


def test_fanout_ordering():
    envelope = {
        "envelope_id": "e2",
        "plan_id": "p2",
        "steps": [
            {"id": "s1", "node": "b"},
            {"id": "s2", "node": "a"},
            {"id": "s3", "node": "c"},
        ],
    }
    trace = execute_envelope(envelope)
    # ordering preserved from envelope
    assert [s["id"] for s in trace["steps"]] == ["s1", "s2", "s3"]

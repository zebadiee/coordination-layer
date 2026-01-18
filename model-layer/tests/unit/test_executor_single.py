from model_layer.executor.executor import execute_envelope


def test_single_step_ok():
    envelope = {
        "envelope_id": "e1",
        "plan_id": "p1",
        "steps": [
            {"id": "s1", "payload": {"x": 1}, "simulate_duration_ms": 10}
        ],
    }
    trace = execute_envelope(envelope)
    assert trace["envelope_id"] == "e1"
    assert len(trace["steps"]) == 1
    assert trace["steps"][0]["status"] == "ok"
    assert trace["steps"][0]["result"] is not None

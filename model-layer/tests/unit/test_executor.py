import json
from model_layer.executor.executor import execute_envelope, _id_for


def test_accepts_short_envelope_id():
    envelope = {"envelope_id": "e1", "plan_id": "p1", "steps": [{"id": "s1", "payload": {"x": 1}}]}
    trace = execute_envelope(envelope)
    assert trace["envelope_id"] == "e1"
    assert len(trace["steps"]) == 1


def test_accepts_correct_hash_envelope_id():
    steps = [{"id": "s1", "payload": {"x": 1}}, {"id": "s2", "payload": {"y": 2}}]
    expected = _id_for({"plan_id": "p2", "steps": [s.get("id") for s in steps]})
    envelope = {"envelope_id": expected, "plan_id": "p2", "steps": steps}
    trace = execute_envelope(envelope)
    assert trace["envelope_id"] == expected


def test_rejects_mismatched_hash_envelope_id():
    steps = [{"id": "s1"}]
    wrong = "0" * 64
    envelope = {"envelope_id": wrong, "plan_id": "p3", "steps": steps}
    try:
        execute_envelope(envelope)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "envelope_id mismatch" in str(e)

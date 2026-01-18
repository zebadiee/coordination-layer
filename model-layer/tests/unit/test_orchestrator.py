import pytest

from model_layer.orchestrator.orchestrator import build_envelope


def test_build_envelope_happy_path():
    plan = {"plan_id": "p1", "steps": [{"type": "invoke", "adapter": "a", "payload": {"x": 1}}]}
    env = build_envelope(plan)
    assert env["plan_id"] == "p1"
    assert "envelope_id" in env
    assert len(env["steps"]) == 1
    assert env["steps"][0]["adapter"] == "a"
    assert env["steps"][0]["id"]


def test_build_envelope_invalid_types():
    with pytest.raises(TypeError):
        build_envelope(None)
    with pytest.raises(ValueError):
        build_envelope({"steps": []})
    with pytest.raises(TypeError):
        build_envelope({"plan_id": "p", "steps": "notalist"})


def test_ids_are_deterministic():
    step = {"type": "invoke", "adapter": "a", "payload": {"x": 1}}
    plan1 = {"plan_id": "p1", "steps": [step]}
    plan2 = {"plan_id": "p1", "steps": [step]}
    e1 = build_envelope(plan1)
    e2 = build_envelope(plan2)
    assert e1["steps"][0]["id"] == e2["steps"][0]["id"]

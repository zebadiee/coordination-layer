import pytest

from model_layer.orchestrator.orchestrator import build_execution_envelope


def test_build_envelope_happy_path():
    plan = {"plan_id": "p1", "strategy": "single", "nodes": ["a"]}
    adapters = [{"adapter_id": "a", "capabilities": {}}]
    env = build_execution_envelope(plan, adapters)

    assert env["plan_id"] == "p1"
    assert "envelope_id" in env
    assert len(env["steps"]) == 1
    assert env["steps"][0]["adapter"] == "a"
    assert env["steps"][0]["id"]


def test_build_envelope_invalid_types():
    adapters = [{"adapter_id": "a", "capabilities": {}}]
    with pytest.raises(TypeError):
        build_execution_envelope(None, adapters)
    with pytest.raises(ValueError):
        build_execution_envelope({"nodes": []}, adapters)
    with pytest.raises(TypeError):
        build_execution_envelope({"plan_id": "p", "nodes": "notalist"}, adapters)


def test_ids_are_deterministic():
    plan1 = {"plan_id": "p1", "strategy": "single", "nodes": ["a"]}
    plan2 = {"plan_id": "p1", "strategy": "single", "nodes": ["a"]}
    adapters = [{"adapter_id": "a", "capabilities": {}}]
    e1 = build_execution_envelope(plan1, adapters)
    e2 = build_execution_envelope(plan2, adapters)
    assert e1["steps"][0]["id"] == e2["steps"][0]["id"]

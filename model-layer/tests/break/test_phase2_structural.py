import pytest
from model_layer.orchestrator.orchestrator import build_execution_envelope
from model_layer.executor.executor import execute_envelope


def test_reject_empty_nodes():
    adapters = [{"adapter_id": "a1", "capabilities": {}}]
    plan = {"strategy": "fanout", "nodes": [], "timeout_ms": 1000}
    with pytest.raises(ValueError):
        build_execution_envelope(plan, adapters)


def test_reject_duplicate_nodes():
    adapters = [{"adapter_id": "a1", "capabilities": {}}, {"adapter_id": "a2", "capabilities": {}}]
    plan = {"strategy": "fanout", "nodes": ["a1", "a1"], "timeout_ms": 1000}
    with pytest.raises(ValueError):
        build_execution_envelope(plan, adapters)


def test_missing_steps_rejected_by_executor():
    with pytest.raises(ValueError):
        execute_envelope({"envelope_id": "eX", "plan_id": "pX"})


def test_tampered_envelope_id_rejected():
    adapters = [{"adapter_id": "a1", "capabilities": {}}]
    plan = {"strategy": "single", "nodes": ["a1"], "timeout_ms": 1000}
    envelope = build_execution_envelope(plan, adapters)
    # tamper envelope_id
    envelope["envelope_id"] = "badid"
    with pytest.raises(ValueError):
        execute_envelope(envelope)


def test_reordered_steps_detected_as_tamper():
    adapters = [{"adapter_id": "a1", "capabilities": {}}, {"adapter_id": "a2", "capabilities": {}}]
    plan = {"strategy": "fanout", "nodes": ["a1", "a2"], "timeout_ms": 1000}
    envelope = build_execution_envelope(plan, adapters)
    # reorder steps in place -- this changes recomputed envelope id
    envelope["steps"].reverse()
    with pytest.raises(ValueError):
        execute_envelope(envelope)

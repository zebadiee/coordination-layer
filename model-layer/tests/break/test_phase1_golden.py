import json
from model_layer.orchestrator.orchestrator import build_execution_envelope
from model_layer.executor.executor import execute_envelope


def _hash(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def test_golden_path_repeats_identical():
    adapters = [{"adapter_id": "a1", "capabilities": {"text": True}}]
    plan = {"strategy": "single", "nodes": ["a1"], "timeout_ms": 1000}

    traces = []
    for _ in range(10):
        envelope = build_execution_envelope(plan, adapters)
        trace = execute_envelope(envelope)
        traces.append(_hash(trace))

    assert len(set(traces)) == 1

import json
import pathlib
import sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from model_layer.orchestrator.orchestrator import build_execution_envelope


def adapter(aid):
    return {"adapter_id": aid, "capabilities": {}}


def test_envelope_deterministic_same_input():
    plan = {"strategy": "fanout", "nodes": ["a1","a2"], "timeout_ms": 2000}
    adapters = [adapter('a1'), adapter('a2')]
    env1 = build_execution_envelope(plan, adapters)
    env2 = build_execution_envelope(plan, adapters)
    assert json.dumps(env1, sort_keys=True) == json.dumps(env2, sort_keys=True)


def test_reject_unknown_node():
    plan = {"strategy": "single", "nodes": ["unknown"], "timeout_ms": 1000}
    adapters = [adapter('a1')]
    try:
        build_execution_envelope(plan, adapters)
        assert False, "should have raised ValueError"
    except ValueError as e:
        assert 'unknown nodes' in str(e) or 'no adapter' in str(e)

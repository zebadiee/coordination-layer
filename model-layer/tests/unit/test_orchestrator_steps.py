import pytest
import pathlib
import sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from model_layer.orchestrator.orchestrator import build_execution_envelope


def adapter(aid):
    return {"adapter_id": aid, "capabilities": {}}


def test_steps_ordering_and_fields():
    plan = {"strategy":"fanout","nodes":["b2","a1","c3"],"timeout_ms":4000}
    adapters = [adapter('a1'), adapter('b2'), adapter('c3')]
    env = build_execution_envelope(plan, adapters)
    # nodes should be lexicographically sorted -> a1, b2, c3
    assert [s['node'] for s in env['steps']] == ['a1','b2','c3']
    for s in env['steps']:
        assert s['mode'] == 'dry-run'
        assert 'timeout_ms' in s

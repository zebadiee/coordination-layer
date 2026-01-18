import os
import sys
import pathlib
import json

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from planner.planner import build_execution_plan


def adapter(id):
    return {"adapter_id": id, "capabilities": {"supported_strategies": ["single"]}}


def test_single_strategy_for_one_adapter():
    prompt = {"input": "hello"}
    plan = build_execution_plan(prompt, [adapter('a1')])
    assert plan['strategy'] == 'single'
    assert plan['nodes'] == ['a1']
    assert 'timeout_ms' in plan


def test_deterministic_hash_stable():
    prompt = {"input": "consistent"}
    plan1 = build_execution_plan(prompt, [adapter('a1')])
    plan2 = build_execution_plan(prompt, [adapter('a1')])
    assert json.dumps(plan1, sort_keys=True) == json.dumps(plan2, sort_keys=True)

import os
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from planner.planner import build_execution_plan


def adapter(id):
    return {"adapter_id": id, "capabilities": {"supported_strategies": ["fanout"]}}


def test_fanout_two_adapters():
    prompt = {"input": "fan"}
    plan = build_execution_plan(prompt, [adapter('a1'), adapter('a2')])
    assert plan['strategy'] in ('fanout', 'verify') or len(plan['nodes']) >= 2

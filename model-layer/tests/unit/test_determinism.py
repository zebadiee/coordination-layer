import os
import sys
import pathlib
import json

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from planner.planner import build_execution_plan


def adapter(id):
    return {"adapter_id": id, "capabilities": {"supported_strategies": ["fanout","single"]}}


def test_plan_bit_identical_for_same_input():
    prompt = {"input": "stable"}
    plan1 = build_execution_plan(prompt, [adapter('a1'), adapter('a2')])
    plan2 = build_execution_plan(prompt, [adapter('a1'), adapter('a2')])
    assert json.dumps(plan1, sort_keys=True) == json.dumps(plan2, sort_keys=True)

import os
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from planner.planner import build_execution_plan


def adapter(id, supports_verify=False):
    s = ["single"]
    if supports_verify:
        s.append("verify")
    return {"adapter_id": id, "capabilities": {"supported_strategies": s}}


def test_verify_strategy_with_two_adapters():
    prompt = {"input": "verify-me"}
    plan = build_execution_plan(prompt, [adapter('a1', True), adapter('a2')])
    assert plan['strategy'] == 'verify'
    assert len(plan['nodes']) == 2

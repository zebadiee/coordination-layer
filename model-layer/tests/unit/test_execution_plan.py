import os
import sys
import pathlib
import pytest

# Ensure tests import the local validator implementation deterministically
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))

from validate_execution_plan import validate_execution_plan, ValidationError


DISCOVERED = {"hades", "atlas", "jetson"}


def base_plan(**overrides):
    p = {
        "strategy": "fanout",
        "nodes": ["hades", "atlas"],
        "timeout_ms": 5000,
        "merge_policy": "first_success",
    }
    p.update(overrides)
    return p


def test_valid_single():
    plan = base_plan(strategy="single", nodes=["hades"], merge_policy="first_success")
    validate_execution_plan(plan, DISCOVERED)


def test_valid_fanout_and_verify():
    # fanout
    plan = base_plan(strategy="fanout", nodes=["hades", "atlas"], merge_policy="rank")
    validate_execution_plan(plan, DISCOVERED)

    # verify
    plan_v = base_plan(strategy="verify", nodes=["hades", "atlas"], merge_policy="first_success")
    validate_execution_plan(plan_v, DISCOVERED)


def test_reject_unknown_strategy():
    plan = base_plan(strategy="multicast")
    with pytest.raises(ValidationError, match="unsupported strategy"):
        validate_execution_plan(plan, DISCOVERED)


def test_reject_empty_node_list():
    plan = base_plan(nodes=[])
    with pytest.raises(ValidationError, match="non-empty"):
        validate_execution_plan(plan, DISCOVERED)


def test_reject_nondeterministic_merge_with_deterministic_plan():
    plan = base_plan(merge_policy="vote", constraints={"deterministic": True})
    with pytest.raises(ValidationError, match="not allowed for deterministic"):
        validate_execution_plan(plan, DISCOVERED)


def test_reject_timeout_too_large():
    plan = base_plan(timeout_ms=120_000)
    with pytest.raises(ValidationError, match="exceeds max"):
        validate_execution_plan(plan, DISCOVERED, max_timeout_ms=100_000)


def test_reject_unknown_nodes():
    plan = base_plan(nodes=["hades", "unknown_node"])
    with pytest.raises(ValidationError, match="unknown nodes"):
        validate_execution_plan(plan, DISCOVERED)


def test_reject_single_wrong_node_count():
    plan = base_plan(strategy="single", nodes=["hades", "atlas"])
    with pytest.raises(ValidationError, match="requires exactly one node"):
        validate_execution_plan(plan, DISCOVERED)


def test_reject_verify_too_few_nodes():
    plan = base_plan(strategy="verify", nodes=["hades"])
    with pytest.raises(ValidationError, match="requires at least two nodes"):
        validate_execution_plan(plan, DISCOVERED)

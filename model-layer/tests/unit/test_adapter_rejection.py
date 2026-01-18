import os
import sys
import pathlib
import pytest

# Ensure tests import the local validator implementation deterministically
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))

from validate_adapter import check_plan_acceptance, AdapterValidationError

DISCOVERED = {"hades","atlas"}


def descriptor_with(strategies, deterministic=True, timeout_max=30000):
    return {
        "adapter_id":"a1",
        "adapter_version":"0.1.0",
        "backend_type":"cpu",
        "vendor":"acme",
        "capabilities":{
            "max_tokens":1024,
            "deterministic":deterministic,
            "supported_prompt_types":["task"],
            "supported_strategies":strategies,
            "concurrency":1
        },
        "limits":{"timeout_ms_max":timeout_max,"memory_mb_max":1024}
    }


def plan(**overrides):
    p = {
        "strategy":"single",
        "nodes":["hades"],
        "timeout_ms":2000,
        "merge_policy":"first_success",
    }
    p.update(overrides)
    return p


def test_accepts_supported_strategy():
    desc = descriptor_with(["single","fanout"])
    check_plan_acceptance(desc, plan(), DISCOVERED)


def test_rejects_unsupported_strategy():
    desc = descriptor_with(["fanout"])
    with pytest.raises(AdapterValidationError, match="unsupported_strategy"):
        check_plan_acceptance(desc, plan(), DISCOVERED)


def test_rejects_determinism():
    desc = descriptor_with(["single"], deterministic=False)
    p = plan(constraints={"deterministic": True})
    with pytest.raises(AdapterValidationError, match="determinism_unsupported"):
        check_plan_acceptance(desc, p, DISCOVERED)


def test_rejects_timeout_exceed():
    desc = descriptor_with(["single"], timeout_max=1000)
    p = plan(timeout_ms=5000)
    with pytest.raises(AdapterValidationError, match="limit_exceeded"):
        check_plan_acceptance(desc, p, DISCOVERED)


def test_rejects_unknown_nodes():
    desc = descriptor_with(["single","fanout"])
    p = plan(nodes=["hades","unknown"])
    with pytest.raises(AdapterValidationError, match="limit_exceeded"):
        check_plan_acceptance(desc, p, DISCOVERED)

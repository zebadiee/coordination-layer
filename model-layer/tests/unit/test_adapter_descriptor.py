import os
import sys
import pathlib
import pytest

# Ensure tests import the local validator implementation deterministically
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))

from validate_adapter import validate_descriptor, AdapterValidationError


def good_descriptor():
    return {
        "adapter_id": "hades-exec-1",
        "adapter_version": "1.0.0",
        "backend_type": "cpu",
        "vendor": "acme",
        "capabilities": {
            "max_tokens": 4096,
            "deterministic": True,
            "supported_prompt_types": ["task"],
            "supported_strategies": ["single","fanout"],
            "concurrency": 1
        },
        "limits": {"timeout_ms_max": 30000, "memory_mb_max": 8192}
    }


def test_validate_good_descriptor():
    validate_descriptor(good_descriptor())


def test_reject_bad_semver():
    d = good_descriptor()
    d['adapter_version'] = '1.0'
    with pytest.raises(AdapterValidationError):
        validate_descriptor(d)


def test_reject_missing_field():
    d = good_descriptor()
    del d['vendor']
    with pytest.raises(AdapterValidationError):
        validate_descriptor(d)

import os
import sys
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import json
import hashlib
import pytest

from model_layer.executor.executor import execute_envelope, _id_for


def test_envelope_tamper_detection():
    # Create envelope with proper SHA256 envelope_id then tamper a step
    steps = [{"id": "s1", "payload": {"x": 1}}, {"id": "s2", "payload": {"y": 2}}]
    envelope_id = _id_for({"plan_id": "p-tamper", "steps": [s.get("id") for s in steps]})
    envelope = {"envelope_id": envelope_id, "plan_id": "p-tamper", "steps": steps}

    # baseline: should execute ok
    trace = execute_envelope(envelope)
    assert trace["envelope_id"] == envelope_id

    # tamper: reorder steps -> recomputed id differs -> should raise
    tampered = {"envelope_id": envelope_id, "plan_id": "p-tamper", "steps": list(reversed(steps))}
    with pytest.raises(ValueError):
        execute_envelope(tampered)


def test_step_timeout_affects_quorum():
    steps = [
        {"id": "s1", "group": "g1", "payload": {"v": 1}, "simulate_duration_ms": 100, "timeout_ms": 50},
        {"id": "s2", "group": "g1", "payload": {"v": 1}},
        {"id": "s3", "group": "g1", "payload": {"v": 2}},
    ]
    envelope = {"envelope_id": "e-timeout", "plan_id": "p-timeout", "steps": steps}
    trace = execute_envelope(envelope)

    # one step timed_out -> payload_hash for that step is None; quorum should be computed from remaining
    statuses = {s["id"]: s["status"] for s in trace["steps"]}
    assert statuses["s1"] == "timed_out"
    # quorum for g1 is false because no majority of same payload hash
    assert trace["quorum"].get("g1") in (False, None)


def test_payload_hash_quorum_detection():
    # three members same payload -> quorum true
    steps = [
        {"id": "a1", "group": "gX", "payload": {"v": 1}},
        {"id": "a2", "group": "gX", "payload": {"v": 1}},
        {"id": "a3", "group": "gX", "payload": {"v": 2}},
    ]
    envelope = {"envelope_id": "e-q", "plan_id": "p-q", "steps": steps}
    trace = execute_envelope(envelope)
    assert trace["quorum"]["gX"] is True

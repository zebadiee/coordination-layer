import hashlib
import json
import time

from model_layer.executor.executor import execute_envelope


def hash_result(envelope):
    result = execute_envelope(envelope)
    blob = json.dumps(result, sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()


def test_temporal_drift_same_seed():
    envelope = {
        "envelope_id": "phase5-temporal",
        "plan_id": "p-temporal",
        "steps": [
            {"id": "t1", "payload": {"op": "add", "a": 10, "b": 20, "seed": 1337}},
            {"id": "t2", "payload": {"op": "mul", "a": 2, "b": 9, "seed": 1337}},
            {"id": "t3", "payload": {"op": "add", "a": 7, "b": 3, "seed": 1337}},
        ],
    }

    h1 = hash_result(envelope)

    # Wall-clock separation
    time.sleep(2)

    h2 = hash_result(envelope)

    assert h1 == h2, f"Temporal drift detected: {h1} != {h2}"

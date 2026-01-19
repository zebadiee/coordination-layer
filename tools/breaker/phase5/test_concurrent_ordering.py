import concurrent.futures
import hashlib
import json

from model_layer.executor.executor import execute_envelope


def run_once(seed: int):
    envelope = {
        "envelope_id": "phase5-concurrency",
        "plan_id": "p-concurrency",
        "steps": [
            {"id": "s1", "payload": {"op": "add", "a": 1, "b": 2, "seed": seed}},
            {"id": "s2", "payload": {"op": "mul", "a": 3, "b": 4, "seed": seed}},
            {"id": "s3", "payload": {"op": "add", "a": 5, "b": 6, "seed": seed}},
            {"id": "s4", "payload": {"op": "mul", "a": 7, "b": 8, "seed": seed}},
        ],
    }
    result = execute_envelope(envelope)
    blob = json.dumps(result, sort_keys=True).encode()
    return hashlib.sha256(blob).hexdigest()


def test_parallel_execution_ordering():
    seed = 42

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        hashes = list(ex.map(run_once, [seed] * 8))

    # All hashes MUST match if ordering is deterministic
    assert len(set(hashes)) == 1, f"Concurrency drift detected: {set(hashes)}"

import random
from model_layer.executor import execute_envelope

def test_nondeterministic_seed_detection():
    random.seed()  # intentionally NOT fixed

    def make_envelope():
        return {
            "envelope_id": "e1",
            "plan_id": "p1",
            "steps": [
                {"id": "alpha", "payload": {"r": random.random()}},
                {"id": "beta", "payload": {"r": random.random()}},
                {"id": "gamma", "payload": {"r": random.random()}}
            ]
        }

    r1 = execute_envelope(make_envelope())
    r2 = execute_envelope(make_envelope())

    assert r1 == r2, "Determinism violated: executor output drift detected"

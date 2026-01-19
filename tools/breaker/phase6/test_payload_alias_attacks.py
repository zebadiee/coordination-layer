import hashlib
import json

from model_layer.executor.executor import execute_envelope


class MutatingDict(dict):
    """Dictionary that mutates a target dict when iterated/serialized."""

    def __init__(self, data, target):
        super().__init__(data)
        self._target = target

    def items(self):
        # Side-effect: mutate the target when items are requested
        self._target["poisoned"] = True
        return super().items()


def make_env_with_shared(payload):
    return {
        "envelope_id": "phase6-alias",
        "plan_id": "p6-alias",
        "steps": [
            {"id": "s1", "payload": payload},
            {"id": "s2", "payload": payload},
        ],
    }


def test_mutation_during_serialization_is_detected():
    shared = {}
    payload = MutatingDict({"value": 1}, shared)
    env = make_env_with_shared(payload)

    trace = execute_envelope(env)
    phs = [s["payload_hash"] for s in trace["steps"]]

    # If mutation during serialization occurs, payload hashes may differ
    assert phs[0] == phs[1], f"Alias poisoning detected: {phs} (shared mutated: {shared})"


def test_mutation_after_first_access_affects_later_steps():
    # More explicit: ensure that if payload mutates during first step serialization,
    # the second step sees the mutation (this is a detection test, not a security fix).
    mutated = {}
    payload = MutatingDict({"value": 2}, mutated)
    env = make_env_with_shared(payload)

    trace = execute_envelope(env)
    phs = [s["payload_hash"] for s in trace["steps"]]

    # If executor copies payload internally this will be stable; otherwise second hash reflects mutation.
    assert phs[0] == phs[1], "Cross-step mutation detected (executor retained shared reference)"

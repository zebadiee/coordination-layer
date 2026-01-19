from model_layer.executor.executor import execute_envelope


class MutatingDict(dict):
    def __init__(self, data, target):
        super().__init__(data)
        self._target = target

    def items(self):
        # Mutate target payload when items are requested (during serialization)
        self._target["poisoned"] = True
        return super().items()


def make_env(p1, p2):
    return {
        "envelope_id": "phase6-mutation",
        "plan_id": "p6-mutation",
        "steps": [
            {"id": "first", "payload": p1},
            {"id": "second", "payload": p2},
        ],
    }


def test_mutation_during_first_step_does_not_change_second_payload_hash():
    shared = {"value": 1}
    p1 = MutatingDict({"value": 1}, shared)
    p2 = shared

    env = make_env(p1, p2)

    trace = execute_envelope(env)
    phs = [s["payload_hash"] for s in trace["steps"]]

    assert phs[0] == phs[1], f"Mutation during execution leaked: {phs}, mutated target: {shared}"

from mad_os.adapters import readiness_adapter
from mad_os.runtime.manifest import RUNTIME_COMPONENTS


def run():
    state = readiness_adapter.readiness_state()
    activated = []

    for name, modes in RUNTIME_COMPONENTS.items():
        fn = modes.get(state)
        if fn:
            result = fn()
            activated.append((name, result))

    return {
        "state": state,
        "activated": activated,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2))

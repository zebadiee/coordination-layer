from mad_os.adapters import readiness_adapter
from mad_os.telemetry.telemetry_loop import start_full, start_limited


def start_telemetry():
    """Start telemetry according to current readiness state.

    - READY -> start_full()
    - DEGRADED -> start_limited()
    - HALT/other -> return None
    """
    state = readiness_adapter.readiness_state()
    if state == "READY":
        return start_full()
    if state == "DEGRADED":
        return start_limited()
    return None

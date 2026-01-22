from mad_os.telemetry.runner import start_telemetry
from mad_os.queue.consumer import start_full as start_queue_full, start_limited as start_queue_limited

RUNTIME_COMPONENTS = {
    "telemetry": {
        "READY": start_telemetry,
        "DEGRADED": start_telemetry,
        "HALT": None,
    },
    "queue_consumer": {
        "READY": start_queue_full,
        "DEGRADED": start_queue_limited,
        "HALT": None,
    },
}

from mad_os.telemetry.runner import start_telemetry

RUNTIME_COMPONENTS = {
    "telemetry": {
        "READY": start_telemetry,
        "DEGRADED": start_telemetry,
        "HALT": None,
    },
}

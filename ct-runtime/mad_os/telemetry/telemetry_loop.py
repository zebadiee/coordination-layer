# Minimal telemetry loop placeholders (read-only)

def start_full():
    """Start full telemetry path (placeholder).

    Returns a string marker for testing and validation.
    """
    # Real telemetry would start loops / exporters etc.
    return "telemetry:full"


def start_limited():
    """Start limited telemetry path (DEGRADED mode placeholder).

    Returns a string marker for testing and validation.
    """
    # Reduced cadence or sampling-only telemetry
    return "telemetry:limited"

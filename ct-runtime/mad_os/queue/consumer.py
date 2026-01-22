# Minimal read-only queue consumer placeholders

def start_full():
    """Start normal queue consumer (placeholder).

    Returns a string marker for testing and validation.
    """
    return "queue:full"


def start_limited():
    """Start limited/read-only queue consumer (DEGRADED placeholder).

    Returns a string marker for testing and validation.
    """
    return "queue:limited"

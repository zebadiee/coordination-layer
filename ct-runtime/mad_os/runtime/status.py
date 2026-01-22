from mad_os.runtime.orchestrator import run


def runtime_status():
    """Return the current runtime orchestrator status (read-only)."""
    return run()

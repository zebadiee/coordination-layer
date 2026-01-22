#!/usr/bin/env python3
"""CT Boot Observer — orchestrates readiness emission and auditing.

This module is intentionally small and focused:
- Call determine_state() to compute one of READY|DEGRADED|HALT
- Call emit_readiness(state=...) to atomically write the readiness file
- Append a boot.sweep audit event containing state, checks, and timestamp
- Exit non-zero on HALT so systemd can gate

No MAD-OS imports, no policy logic duplication.
"""

from datetime import datetime
import json
import sys

from ct_runtime.ops import readiness_emitter as readiness
from ct_runtime.ops.readiness_emitter import determine_state, emit_readiness
from ct_runtime.ops.monitoring import lock_presence
from ct_runtime.core.ct_root import write_audit_event


def _gather_checks() -> dict:
    """Return a small dict of probe results for auditing."""
    return {
        "network": readiness._network_ok(),
        "docker": readiness._docker_ok(),
        "disk": readiness._disk_writable(),
        "lock": lock_presence().get("exists", False),
    }


def main() -> int:
    """Run one probe-and-emit cycle and audit the result.

    Returns 0 on non-HALT. Raises SystemExit with non-zero code on HALT.
    """
    state = determine_state()

    # Emit readiness file (atomic write)
    emit_readiness(state=state)

    # Gather checks for audit detail
    checks = _gather_checks()

    # Audit the sweep (best-effort, canonical write path)
    event = {
        "state": state,
        "checks": checks,
        "ts": datetime.utcnow().isoformat() + "Z",
    }

    write_audit_event(
        actor="NODE:BOOT_OBSERVER",
        action="boot.sweep",
        target="",
        result=json.dumps(event, sort_keys=True),
    )

    if state == "HALT":
        # Indicate failure to systemd / caller
        raise SystemExit(1)

    return 0


if __name__ == "__main__":
    main()

"""Emit readiness signals (READ/DEGRADED/HALT) from CT side.

This module implements a conservative, reversible mechanism to compute a
local readiness verdict and optionally write a read-only JSON file to
`/run/dam-os/READY` with `{ "status": "DEGRADED" }` etc. This is
intentionally small and test-covered.
"""
from datetime import datetime
import json
import os
import socket
import shutil
import tempfile
from typing import Dict

try:
    from ct_runtime.ops.monitoring import lock_presence
except Exception:
    # Fallback stub for environments where monitoring is not available
    def lock_presence(lock_file: str = '/srv/ct/ct_lock.json') -> Dict[str, object]:
        return {'exists': False}



def _network_ok(timeout: float = 0.5) -> bool:
    try:
        # connect UDP to 1.1.1.1:53 to test routing (no bytes sent)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        sock.connect(("1.1.1.1", 53))
        sock.close()
        return True
    except Exception:
        return False


def _docker_ok() -> bool:
    # Accept docker socket presence or docker CLI
    if os.path.exists("/var/run/docker.sock"):
        return True
    if shutil.which("docker"):
        return True
    return False


def _disk_writable(path: str = "/run") -> bool:
    try:
        os.makedirs(path, exist_ok=True)
        f = tempfile.NamedTemporaryFile(dir=path, delete=True)
        f.write(b"x")
        f.flush()
        f.close()
        return True
    except Exception:
        return False


def determine_state(lock_file: str = "/srv/ct/ct_lock.json") -> str:
    """Return one of 'READY', 'DEGRADED', 'HALT'.

    Rules (conservative):
      - If any critical invariant fails -> HALT
      - If lock exists (authority present) and invariants OK -> READY
      - If lock missing (no authority) and invariants OK -> DEGRADED
    """
    inv_network = _network_ok()
    inv_docker = _docker_ok()
    inv_disk = _disk_writable()
    invariants_ok = inv_network and inv_docker and inv_disk

    if not invariants_ok:
        return "HALT"

    lp = lock_presence(lock_file)
    authority_present = bool(lp.get("exists"))

    if authority_present:
        return "READY"
    return "DEGRADED"


def emit_readiness(path: str = "/run/dam-os/READY", state: str = "DEGRADED") -> None:
    """Atomically write a small JSON readiness file containing status and timestamp."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {"status": state, "ts": datetime.utcnow().isoformat() + "Z"}
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


if __name__ == "__main__":
    s = determine_state()
    print("Determined state:", s)
    emit_readiness(state=s)

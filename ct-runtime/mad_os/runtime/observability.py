"""MAD-OS runtime observability

Expose minimal read-only runtime signals for CT consumption.
Writes an atomic JSON artifact (path configurable via MAD_OS_OBSERVABILITY_PATH)
and returns the payload for CLI output.
"""
from datetime import datetime, timedelta
import json
import os
from typing import Dict, Any, Optional

from mad_os.runtime import lifecycle
from mad_os.runtime.manifest import RUNTIME_COMPONENTS
from mad_os.adapters import readiness_adapter

DEFAULT_OBS_PATH = os.environ.get("MAD_OS_OBSERVABILITY_PATH", "/run/mad-os/RUNTIME_OBSERVABILITY.json")
DEFAULT_STALE_SECONDS = 300


def _now_ts() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _resolve_path(path: Optional[str]) -> str:
    return path or os.environ.get("MAD_OS_OBSERVABILITY_PATH", DEFAULT_OBS_PATH)


def gather_observability(state_path: Optional[str] = None, observability_path: Optional[str] = None, stale_threshold_seconds: int = DEFAULT_STALE_SECONDS) -> Dict[str, Any]:
    """Produce and persist a read-only observability payload.

    Returns the payload dict.
    """
    state = lifecycle.all_status(state_path)
    readiness = readiness_adapter.readiness_state()

    components: Dict[str, Any] = {}
    issues = []

    for name, modes in RUNTIME_COMPONENTS.items():
        expected_fn = modes.get(readiness)
        expected_running = bool(expected_fn)

        entry = state.get(name, {})
        actual_running = bool(entry.get("running", False))
        last_result = entry.get("last_result")
        ts = entry.get("ts")

        stale = False
        if actual_running and ts:
            try:
                t = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                if datetime.utcnow() - t > timedelta(seconds=stale_threshold_seconds):
                    stale = True
            except Exception:
                stale = True
        elif actual_running and not ts:
            stale = True

        drift = expected_running != actual_running

        components[name] = {
            "expected_running": expected_running,
            "actual_running": actual_running,
            "last_result": last_result,
            "ts": ts,
            "stale": stale,
            "drift": drift,
        }

        if drift:
            issues.append({"component": name, "issue": "DRIFT", "expected": expected_running, "observed": actual_running})
        if stale:
            issues.append({"component": name, "issue": "STALE", "ts": ts})

    payload = {
        "readiness": readiness,
        "components": components,
        "issues": issues,
        "drift_count": len(issues),
        "ts": _now_ts(),
    }

    # Persist atomically to observability path (best-effort)
    obs_path = _resolve_path(observability_path)
    try:
        os.makedirs(os.path.dirname(obs_path), exist_ok=True)
        tmp = f"{obs_path}.{os.getpid()}.tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, obs_path)
    except Exception:
        # Best effort only — avoid failing callers
        pass

    return payload


if __name__ == "__main__":
    import json
    print(json.dumps(gather_observability(), indent=2))

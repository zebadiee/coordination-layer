"""CT runtime observer — read-only consumption of MAD-OS observability.

Reads the MAD-OS observability artifact (drift/stale signals) and
emits a concise CT-side observation payload plus an audit event.

This module is intentionally read-only with respect to MAD-OS; CT is
responsible for deciding and acting under governance.
"""
from datetime import datetime
import json
import os
from typing import Dict, Any, Optional


DEFAULT_OBSERVABILITY_PATH = os.environ.get(
    "MAD_OS_OBSERVABILITY_PATH", "/run/mad-os/RUNTIME_OBSERVABILITY.json"
)
DEFAULT_OUTPUT_PATH = os.environ.get("CT_RUNTIME_OBSERVE", "/run/ct/RUNTIME_OBSERVE.json")


def _now_ts() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _read_json(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def _atomic_write(path: str, payload: Dict[str, Any]) -> None:
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def observe_runtime(observability_path: Optional[str] = None, output_path: Optional[str] = None) -> Dict[str, Any]:
    """Read MAD-OS observability artifact, summarize issues, write CT artifact, and emit audit.

    Returns the CT observation payload.
    """
    obs_path = observability_path or DEFAULT_OBSERVABILITY_PATH
    out_path = output_path or DEFAULT_OUTPUT_PATH

    observability = _read_json(obs_path)

    if observability is None:
        payload = {
            "ts": _now_ts(),
            "status": "unavailable",
            "observability_path": obs_path,
            "issues": [],
            "note": "observability artifact missing or unreadable",
        }
    else:
        issues = observability.get("issues", [])
        payload = {
            "ts": _now_ts(),
            "status": "observed",
            "observability_path": obs_path,
            "drift_count": len(issues),
            "issues": issues,
            "components": observability.get("components", {}),
            "readiness": observability.get("readiness"),
        }

    # Persist CT-observe artifact (best-effort)
    try:
        _atomic_write(out_path, payload)
    except Exception:
        # avoid failing caller
        pass

    # Emit audit event (best-effort). Use write_audit_event if available.
    try:
        from ct_runtime.core.ct_root import write_audit_event

        write_audit_event(
            actor="CT:OBSERVER",
            action="runtime.observe",
            target="",
            result=json.dumps(payload, sort_keys=True),
        )
    except Exception:
        # best-effort: ignore audit failures at runtime
        pass

    return payload


if __name__ == "__main__":
    import json

    print(json.dumps(observe_runtime(), indent=2))

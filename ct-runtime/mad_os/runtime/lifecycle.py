"""MAD-OS runtime lifecycle manager (Phase 1).

Provides idempotent in-process lifecycle control for runtime components.
State is persisted atomically to a JSON file (path configurable by
`MAD_OS_RUNTIME_STATE` env var for tests).
"""
from datetime import datetime
import json
import os
import tempfile
from typing import Dict, Optional, Any

from mad_os.runtime.manifest import RUNTIME_COMPONENTS
from mad_os.adapters import readiness_adapter



def _resolve_state_path(path: Optional[str]) -> str:
    if path:
        return path
    return os.environ.get("MAD_OS_RUNTIME_STATE", "/run/mad-os/RUNTIME_STATE.json")


def _read_state(path: Optional[str] = None) -> Dict[str, Any]:
    path = _resolve_state_path(path)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {"components": {}}


def _write_state(state: Dict[str, Any], path: Optional[str] = None) -> None:
    path = _resolve_state_path(path)
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def _now_ts() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _get_component_entry(state: Dict[str, Any], name: str) -> Dict[str, Any]:
    return state.setdefault("components", {}).setdefault(name, {"running": False, "last_result": None, "ts": None})


def start(name: str, mode: Optional[str] = None, state_path: Optional[str] = None) -> Dict[str, Any]:
    """Start a component in the given mode (None -> current readiness).

    Returns the component state dict.
    """
    if name not in RUNTIME_COMPONENTS:
        raise ValueError(f"Unknown component: {name}")

    if mode is None:
        mode = readiness_adapter.readiness_state()

    modes = RUNTIME_COMPONENTS[name]
    fn = modes.get(mode)

    state = _read_state(state_path)
    entry = _get_component_entry(state, name)

    # Idempotent: if already running, return current entry
    if entry.get("running"):
        return entry

    if not fn:
        # No-op: component not active under this mode
        entry["running"] = False
        entry["last_result"] = None
        entry["ts"] = _now_ts()
        _write_state(state, state_path)
        return entry

    # Call component start function and record result
    result = fn()
    entry["running"] = True
    entry["last_result"] = result
    entry["ts"] = _now_ts()

    _write_state(state, state_path)
    return entry


def stop(name: str, state_path: Optional[str] = None) -> Dict[str, Any]:
    """Stop a component (idempotent)."""
    if name not in RUNTIME_COMPONENTS:
        raise ValueError(f"Unknown component: {name}")

    state = _read_state(state_path)
    entry = _get_component_entry(state, name)

    if not entry.get("running"):
        return entry

    # Best-effort: if a stop handler exists on the manifest, call it
    modes = RUNTIME_COMPONENTS[name]
    stop_fn = modes.get("stop")
    result = None
    if stop_fn:
        try:
            result = stop_fn()
        except Exception:
            result = None

    entry["running"] = False
    entry["last_result"] = result or "stopped"
    entry["ts"] = _now_ts()

    _write_state(state, state_path)
    return entry


def restart(name: str, mode: Optional[str] = None, state_path: Optional[str] = None) -> Dict[str, Any]:
    stop(name, state_path=state_path)
    return start(name, mode=mode, state_path=state_path)


def status(name: str, state_path: Optional[str] = None) -> Dict[str, Any]:
    state = _read_state(state_path)
    return _get_component_entry(state, name)


def all_status(state_path: Optional[str] = None) -> Dict[str, Any]:
    state = _read_state(state_path)
    return state.get("components", {})

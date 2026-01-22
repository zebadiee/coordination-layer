import os
from datetime import datetime
from typing import Dict, Any

READY_PATH_DEFAULT = "/run/dam-os/READY"


def read_readiness(path: str = READY_PATH_DEFAULT) -> Dict[str, Any]:
    """Return readiness info read-only.

    Returns a dict with:
      - state: 'READY' | 'DEGRADED' | 'HALT'
      - exists: bool
      - mtime: ISO timestamp if exists else None
      - content: stripped file content if exists else None
    """
    info = {
        "state": "HALT",
        "exists": False,
        "mtime": None,
        "content": None,
    }
    try:
        if os.path.exists(path):
            info["exists"] = True
            st = os.stat(path)
            info["mtime"] = datetime.utcfromtimestamp(st.st_mtime).isoformat() + "Z"
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    info["content"] = fh.read().strip()
            except Exception:
                info["content"] = None

            # Derive state from content if present
            content = info["content"]
            if content:
                # If content is JSON with a 'status' key, respect it
                try:
                    import json as _json
                    parsed = _json.loads(content)
                    if isinstance(parsed, dict) and parsed.get("status"):
                        s = str(parsed.get("status")).strip().upper()
                    else:
                        s = str(content).strip().upper()
                except Exception:
                    s = str(content).strip().upper()

                if s in ("READY", "DEGRADED", "HALT"):
                    info["state"] = s
                else:
                    # Default to READY when file exists but content is opaque
                    info["state"] = "READY"
            else:
                info["state"] = "READY"
    except Exception:
        # Be conservative — on error, report HALT without raising
        pass

    return info


def readiness_state(path: str = READY_PATH_DEFAULT) -> str:
    """Return normalized readiness state string (HALT|READY|DEGRADED)."""
    info = read_readiness(path)
    return info.get("state", "HALT")

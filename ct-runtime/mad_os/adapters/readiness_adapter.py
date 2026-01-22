import os
from datetime import datetime
from typing import Dict, Any

READY_PATH_DEFAULT = "/run/dam-os/READY"


def read_readiness(path: str = READY_PATH_DEFAULT) -> Dict[str, Any]:
    """Return readiness info read-only.

    Returns a dict with:
      - state: 'READY' or 'HALT'
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
            info["state"] = "READY"
    except Exception:
        # Be conservative — on error, report HALT without raising
        pass

    return info

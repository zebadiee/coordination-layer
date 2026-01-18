"""C12 orchestrator implementation (packaged)

This file mirrors `model-layer/orchestrator/orchestrator.py` but is placed
under the `model_layer` package so tests and imports work consistently.
"""
from __future__ import annotations

import json
import hashlib
from typing import Any, Dict


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _id_for(obj: Any) -> str:
    s = canonical_json(obj)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def build_envelope(plan: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(plan, dict):
        raise TypeError("plan must be an object")
    if "plan_id" not in plan or "steps" not in plan:
        raise ValueError("plan must contain plan_id and steps")
    if not isinstance(plan["steps"], list):
        raise TypeError("steps must be a list")

    steps_out = []
    for step in plan["steps"]:
        if not isinstance(step, dict):
            raise TypeError("each step must be an object")
        sid = _id_for(step)
        step_copy = dict(step)
        step_copy["id"] = sid
        steps_out.append(step_copy)

    envelope = {
        "plan_id": plan["plan_id"],
        "envelope_id": _id_for({"plan_id": plan["plan_id"], "steps": [s["id"] for s in steps_out]}),
        "steps": steps_out,
    }
    return envelope

"""C12 orchestrator implementation

Provides build_execution_envelope(plan, adapters) which returns a deterministic
execution envelope (dry-run). This is a self-contained, pure function with no
I/O or network access.
"""
from __future__ import annotations

import json
import hashlib
from typing import Any, Dict, List


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _id_for(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def _adapter_map(adapters: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {a["adapter_id"]: a for a in adapters}


def build_execution_envelope(plan: Dict[str, Any], adapters: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(plan, dict):
        raise TypeError("plan must be an object")
    if "strategy" not in plan or "nodes" not in plan:
        raise ValueError("plan must contain strategy and nodes")
    if not isinstance(plan["nodes"], list):
        raise TypeError("nodes must be a list")

    # Structural validations
    if len(plan["nodes"]) == 0:
        raise ValueError("plan.nodes must not be empty")
    if len(set(plan["nodes"])) != len(plan["nodes"]):
        raise ValueError("duplicate node ids in plan.nodes")

    amap = _adapter_map(adapters)

    # Validate nodes
    for n in plan["nodes"]:
        if n not in amap:
            raise ValueError(f"unknown nodes or no adapter for: {n}")

    # Determine node ordering: deterministic sorted order
    nodes_sorted = sorted(plan["nodes"])

    steps = []
    timeout_ms = plan.get("timeout_ms")
    for node in nodes_sorted:
        step = {
            "node": node,
            "adapter": amap[node]["adapter_id"],
            "mode": "dry-run",
        }
        if timeout_ms is not None:
            step["timeout_ms"] = timeout_ms
        steps.append(step)

    plan_id = plan.get("plan_id") or _id_for(plan)
    envelope = {
        "plan_id": plan_id,
        "steps": steps,
        "envelope_id": _id_for({"plan_id": plan_id, "steps": [s["node"] for s in steps]}),
    }
    return envelope


# Backwards-compatible alias (if other modules expect a different name)
build_envelope = build_execution_envelope

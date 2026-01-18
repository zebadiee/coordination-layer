"""C13 Executor (pure deterministic stub)

Function `execute_envelope(envelope)` consumes an execution envelope and
returns a deterministic execution trace describing each step's outcome.
"""
from __future__ import annotations

import json
import hashlib
from typing import Any, Dict, List


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _id_for(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def _simulate_step(step: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate executing a single step in a deterministic way.

    Expected step fields:
      - id (string)
      - payload (object) optional
      - timeout_ms (int) optional
      - simulate_duration_ms (int) optional (used to trigger timeout)
      - group (string) optional (for verification/quorum)

    Returns a dict with: id, status, duration_ms, result
    """
    sid = step.get("id") or _id_for(step)
    duration = int(step.get("simulate_duration_ms", 0))
    timeout = step.get("timeout_ms")

    if timeout is not None and duration > int(timeout):
        status = "timed_out"
        result = None
    else:
        status = "ok"
        # deterministic result: hash of payload (or empty) and step id
        result = _id_for({"id": sid, "payload": step.get("payload")})

    return {
        "id": sid,
        "status": status,
        "duration_ms": duration,
        "result": result,
        "group": step.get("group"),
    }


def _compute_quorum(groups: Dict[str, List[Dict[str, Any]]]) -> Dict[str, bool]:
    """For each group of step results, compute whether a majority agreed."""
    quorum = {}
    for gid, members in groups.items():
        counts = {}
        for m in members:
            r = m.get("result")
            counts[r] = counts.get(r, 0) + 1
        # majority exists if any count > len(members)//2
        majority = any(c > (len(members) // 2) for c in counts.values())
        quorum[gid] = majority
    return quorum


def execute_envelope(envelope: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the envelope deterministically and return an execution trace.

    Trace schema (informal):
      {
        "envelope_id": str,
        "plan_id": str,
        "steps": [ {id,status,duration_ms,result,group}, ... ],
        "quorum": { group_id: boolean }
      }
    """
    if not isinstance(envelope, dict):
        raise TypeError("envelope must be an object")
    if "envelope_id" not in envelope or "steps" not in envelope:
        raise ValueError("envelope must contain envelope_id and steps")

    steps = envelope["steps"]
    if not isinstance(steps, list):
        raise TypeError("envelope.steps must be a list")

    trace_steps = []
    groups: Dict[str, List[Dict[str, Any]]] = {}

    # Execute steps in order
    for step in steps:
        if not isinstance(step, dict):
            raise TypeError("each step must be an object")
        s = _simulate_step(step)
        trace_steps.append(s)
        gid = s.get("group")
        if gid:
            groups.setdefault(gid, []).append(s)

    quorum = _compute_quorum(groups) if groups else {}

    trace = {
        "envelope_id": envelope.get("envelope_id"),
        "plan_id": envelope.get("plan_id"),
        "steps": trace_steps,
        "quorum": quorum,
    }
    return trace

# Backwards-compatible alias
run = execute_envelope

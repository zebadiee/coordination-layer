"""Adversarial harness for break-testing Phases 1–4.

Usage:
  python tools/break/harness.py phase1 --repeat 10
  python tools/break/harness.py phase2 --case invalid_missing_steps
  python tools/break/harness.py tag-baseline
"""
from __future__ import annotations

import argparse
import json
import hashlib
import subprocess
from typing import Any, Dict, List


def _hash(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def tag_baseline(name: str = "pre-break") -> None:
    # annotate origin/main as the baseline commit
    subprocess.run(["git", "fetch", "origin"], check=True)
    commit = subprocess.check_output(["git", "rev-parse", "origin/main"]).decode().strip()
    subprocess.run(["git", "tag", "-a", name, commit, "-m", f"Baseline before break-testing: {name}"], check=True)
    subprocess.run(["git", "push", "origin", name], check=True)
    print(f"Tagged baseline {name} -> {commit}")


def phase1_golden(repeat: int = 10) -> None:
    from model_layer.orchestrator.orchestrator import build_execution_envelope
    from model_layer.executor.executor import execute_envelope

    adapters = [{"adapter_id": "a1", "capabilities": {"text": True}}]
    plan = {"strategy": "single", "nodes": ["a1"], "timeout_ms": 1000}

    hashes = []
    traces = []
    for i in range(repeat):
        envelope = build_execution_envelope(plan, adapters)
        trace = execute_envelope(envelope)
        h = _hash(trace)
        print(f"run {i+1}: envelope_id={envelope.get('envelope_id')} trace_hash={h}")
        hashes.append(h)
        traces.append(trace)

    unique_hashes = set(hashes)
    if len(unique_hashes) == 1:
        print("PHASE1: PASS — deterministic across runs")
    else:
        print("PHASE1: FAIL — nondeterministic traces detected")
        for idx, h in enumerate(hashes):
            print(f"run {idx+1}: {h}")
        raise SystemExit(2)


def phase2_invalid(case: str) -> None:
    from model_layer.orchestrator.orchestrator import build_execution_envelope
    from model_layer.executor.executor import execute_envelope

    adapters = [{"adapter_id": "a1", "capabilities": {}}]

    if case == "missing_steps":
        try:
            envelope = {"envelope_id": "eX", "plan_id": "pX"}
            execute_envelope(envelope)
            print("FAIL: should have rejected missing steps")
            raise SystemExit(2)
        except Exception as e:
            print("PASS: rejected missing steps —", str(e))

    elif case == "empty_nodes":
        try:
            plan = {"strategy": "fanout", "nodes": [], "timeout_ms": 1000}
            envelope = build_execution_envelope(plan, adapters)
            execute_envelope(envelope)
            print("FAIL: should have rejected empty nodes")
            raise SystemExit(2)
        except Exception as e:
            print("PASS: rejected empty nodes —", str(e))

    else:
        print("Unknown case", case)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["tag-baseline", "phase1", "phase2"])
    p.add_argument("--repeat", type=int, default=10)
    p.add_argument("--case", type=str, default="missing_steps")
    args = p.parse_args()

    if args.cmd == "tag-baseline":
        tag_baseline()
    elif args.cmd == "phase1":
        phase1_golden(args.repeat)
    elif args.cmd == "phase2":
        phase2_invalid(args.case)


if __name__ == "__main__":
    main()

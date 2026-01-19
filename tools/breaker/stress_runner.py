"""Phase 3 deterministic stress runner (moved under tools.breaker)
"""
from __future__ import annotations

import argparse
import json
import hashlib
import time
import traceback
import resource
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Tuple

from model_layer.planner.planner import build_execution_plan
from model_layer.orchestrator.orchestrator import build_execution_envelope
from model_layer.executor.executor import execute_envelope


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _hash(obj: Any) -> str:
    return hashlib.sha256(_canonical(obj).encode("utf-8")).hexdigest()


def _run_one(run_id: int, seed: int, prompt: str, adapters: List[Dict[str, Any]], strategy: str, fanout: int, quorum: int) -> Tuple[int, Dict[str, str], str]:
    try:
        plan = build_execution_plan(prompt, adapters, strategy=strategy, fanout=fanout if fanout else None, quorum=quorum if quorum else None, seed=seed)
        envelope = build_execution_envelope(plan, adapters)
        trace = execute_envelope(envelope)
        meta = {"plan_id": plan.get("plan_id"), "envelope_id": envelope.get("envelope_id")}
        th = _hash(trace)
        return (run_id, meta, th)
    except Exception as e:
        return (run_id, {"error": repr(e)}, traceback.format_exc())


def run_stress(runs: int, workers: int, seed: int, prompt: str, adapters: List[Dict[str, Any]], strategy: str, fanout: int, quorum: int, fail_on_violation: bool = True) -> Dict[str, Any]:
    start = time.perf_counter()
    start_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    results = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(_run_one, i, seed, prompt, adapters, strategy, fanout, quorum): i for i in range(runs)}
        for fut in as_completed(futures):
            try:
                res = fut.result()
                results.append(res)
            except Exception as e:
                results.append((-1, {"error": repr(e)}, traceback.format_exc()))

    end = time.perf_counter()
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    hashes = [r[2] for r in results if isinstance(r[2], str) and not r[2].startswith("Traceback")]
    error_runs = [r for r in results if isinstance(r[1], dict) and "error" in r[1]]

    unique_hashes = set(hashes)

    ok = True
    reasons: List[str] = []
    if error_runs:
        ok = False
        reasons.append(f"{len(error_runs)} runs failed with errors")
    if len(unique_hashes) > 1:
        ok = False
        reasons.append("trace hashes diverged")

    summary = {
        "runs": runs,
        "workers": workers,
        "seed": seed,
        "ok": ok,
        "reasons": reasons,
        "unique_trace_hashes": list(unique_hashes)[:10],
        "failure_count": len(error_runs),
        "wall_time_sec": end - start,
        "start_rss": start_rss,
        "peak_rss": peak_rss,
    }

    if fail_on_violation and not ok:
        raise RuntimeError(f"Phase3 invariants violated: {reasons}")

    return summary


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--runs", type=int, default=1000)
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--prompt", type=str, default="stress test")
    p.add_argument("--strategy", type=str, default="single")
    p.add_argument("--fanout", type=int, default=1)
    p.add_argument("--quorum", type=int, default=0)
    p.add_argument("--smoke", action="store_true", help="run a small smoke workload and exit")
    p.add_argument("--output", type=str, default=None, help="file path to write summary JSON")
    args = p.parse_args()

    if args.smoke:
        args.runs = min(args.runs, 50)
        args.workers = min(args.workers, 4)

    adapters = [{"adapter_id": f"a{i}", "capabilities": {}} for i in range(5)]

    print(f"Phase3: runs={args.runs} workers={args.workers} seed={args.seed} strategy={args.strategy} fanout={args.fanout} quorum={args.quorum}")

    summary = run_stress(args.runs, args.workers, args.seed, args.prompt, adapters, args.strategy, args.fanout, args.quorum)

    print("Summary:", json.dumps(summary, indent=2))

    # persist telemetry if requested
    if args.output:
        import os
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"Wrote telemetry to {args.output}")

    if not summary["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

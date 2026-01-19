"""C11 Planner (deterministic) — adversarial-ready minimal planner

Provides `build_execution_plan(prompt, adapters, strategy, fanout, quorum, seed)`
for testing and break harnesses. This is intentionally conservative and
validates inputs strictly.
"""
from __future__ import annotations

import hashlib
import json
import random
from typing import Any, Dict, List, Optional

MAX_FANOUT = 1000


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _id_for(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def build_execution_plan(prompt: str, adapters: List[Dict[str, Any]], *, strategy: str = "single", fanout: Optional[int] = None, quorum: Optional[int] = None, seed: Optional[int] = None) -> Dict[str, Any]:
    """Builds a deterministic execution plan from inputs.

    Validations / invariants:
    - fanout must be >= 1 if provided; 0 is rejected
    - fanout <= MAX_FANOUT
    - quorum must be positive and <= node count if provided
    - strategy must be one of 'single', 'fanout', 'verify'
    - seed if provided must be an int >= 0

    Returns dict with keys: plan_id, strategy, nodes (list of adapter ids), seed
    """
    if not isinstance(prompt, str):
        raise TypeError("prompt must be a string")
    if not isinstance(adapters, list) or len(adapters) == 0:
        raise ValueError("adapters must be a non-empty list")

    if seed is not None:
        if not isinstance(seed, int) or seed < 0:
            raise ValueError("seed must be a non-negative integer")
    else:
        seed = 0

    if strategy not in ("single", "fanout", "verify"):
        raise ValueError("unsupported strategy")

    if fanout is not None:
        if not isinstance(fanout, int) or fanout < 1:
            raise ValueError("fanout must be an integer >= 1")
        if fanout > MAX_FANOUT:
            raise ValueError("fanout exceeds maximum allowed")

    num_adapters = len(adapters)

    if strategy == "single":
        if quorum is not None:
            raise ValueError("quorum provided for single strategy is invalid")
        nodes = [adapters[seed % num_adapters]["adapter_id"]]
    elif strategy == "fanout":
        if quorum is not None:
            raise ValueError("quorum provided for fanout strategy is invalid")
        n = fanout if fanout is not None else num_adapters
        if n < 1:
            raise ValueError("fanout must be >= 1")
        if n > num_adapters:
            # we allow repeat selection but deterministic selection only
            n = min(n, MAX_FANOUT)
        rng = random.Random(seed)
        # deterministic selection without repetition unless n <= num_adapters
        nodes = []
        pool = [a["adapter_id"] for a in adapters]
        for i in range(n):
            nodes.append(pool[rng.randrange(len(pool))])
    elif strategy == "verify":
        # verify requires quorum
        if quorum is None:
            raise ValueError("verify strategy requires quorum")
        if not isinstance(quorum, int) or quorum < 1:
            raise ValueError("quorum must be a positive integer")
        if quorum > num_adapters:
            raise ValueError("quorum cannot exceed number of adapters")
        # deterministic selection of adapters for verification
        pool = [a["adapter_id"] for a in adapters]
        rng = random.Random(seed)
        nodes = [pool[i % len(pool)] for i in range(quorum)]

    plan = {
        "plan_id": _id_for({"prompt": prompt, "strategy": strategy, "seed": seed}),
        "strategy": strategy,
        "nodes": nodes,
        "seed": seed,
    }
    if quorum is not None:
        plan["quorum"] = quorum
    return plan

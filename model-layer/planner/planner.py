"""Execution plan builder (C11).

Builds deterministic execution plans from a validated prompt and a set of adapter descriptors.
"""
from typing import Dict, Iterable, Optional
import json
import hashlib

from .strategies import single_strategy, fanout_strategy, verify_strategy, quorum_strategy


def _canonical_request_hash(validated_prompt: Dict) -> str:
    # Canonical JSON representation for determinism
    data = json.dumps(validated_prompt, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def build_execution_plan(validated_prompt: Dict, adapters: Iterable[Dict], *, strategy_hint: Optional[str] = None, fanout: Optional[int] = None, quorum_size: Optional[int] = None, timeout_ms: int = 5000) -> Dict:
    """Return a deterministic execution plan dict.

    Args:
        validated_prompt: already-validated prompt payload
        adapters: iterable of adapter descriptors (dicts)
        strategy_hint: optional preferred strategy
    """
    adapters = list(adapters)
    if not adapters:
        raise ValueError("no adapters available")

    # simple capability filtering: ensure adapters are capable of any strategy
    # (C11 only maps to strategies; adapters declare supported_strategies)

    # Choose strategy deterministically
    if strategy_hint is None:
        # deterministic rule: if only one adapter -> single; if >=2 and one supports 'verify' -> verify;
        # else if >=3 -> quorum; else fanout
        if len(adapters) == 1:
            strategy = 'single'
        elif any('verify' in a.get('capabilities', {}).get('supported_strategies', []) for a in adapters):
            strategy = 'verify'
        elif len(adapters) >= 3:
            strategy = 'quorum'
        else:
            strategy = 'fanout'
    else:
        strategy = strategy_hint

    # Strategy dispatch
    if strategy == 'single':
        plan_meta = single_strategy(adapters)
    elif strategy == 'fanout':
        plan_meta = fanout_strategy(adapters, fanout=fanout)
    elif strategy == 'verify':
        plan_meta = verify_strategy(adapters)
    elif strategy == 'quorum':
        plan_meta = quorum_strategy(adapters, size=quorum_size)
    else:
        raise ValueError(f"unsupported strategy: {strategy}")

    # Build full plan
    plan = {
        "strategy": plan_meta['strategy'],
        "nodes": plan_meta['nodes'],
        "timeout_ms": timeout_ms,
        "merge_policy": plan_meta['merge_policy'],
        "constraints": validated_prompt.get('constraints', {}),
        "_explain": {
            "request_hash": _canonical_request_hash(validated_prompt),
            "reason": f"selected strategy {plan_meta['strategy']} deterministically"
        }
    }

    return plan

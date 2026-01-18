"""Deterministic strategy helpers for C11 planner.

These functions are pure and avoid side effects. They select node lists and assemble
minimal execution plan fragments; they do not perform execution.
"""
from typing import Dict, Iterable, List


def _pick_nodes_sorted(adapters: Iterable[Dict], n: int) -> List[str]:
    # Stable selection: sort by adapter_id and take first n
    ids = sorted([a['adapter_id'] for a in adapters])
    return ids[:n]


def single_strategy(adapters: Iterable[Dict], *, constraints: Dict = None) -> Dict:
    # Single chooses the first eligible adapter
    nodes = _pick_nodes_sorted(adapters, 1)
    return {"strategy": "single", "nodes": nodes, "merge_policy": "first_success"}


def fanout_strategy(adapters: Iterable[Dict], *, fanout: int = None, constraints: Dict = None) -> Dict:
    ids = sorted([a['adapter_id'] for a in adapters])
    if fanout is None or fanout > len(ids):
        fanout = len(ids)
    nodes = ids[:fanout]
    return {"strategy": "fanout", "nodes": nodes, "merge_policy": "rank"}


def verify_strategy(adapters: Iterable[Dict], *, constraints: Dict = None) -> Dict:
    # Deterministic primary + verifier pairing: pick first two adapters
    ids = sorted([a['adapter_id'] for a in adapters])
    if len(ids) < 2:
        raise ValueError("verify requires at least two adapters")
    nodes = ids[:2]
    return {"strategy": "verify", "nodes": nodes, "merge_policy": "first_success"}


def quorum_strategy(adapters: Iterable[Dict], *, size: int = None, constraints: Dict = None) -> Dict:
    ids = sorted([a['adapter_id'] for a in adapters])
    if size is None:
        # default odd size: smallest odd >=1 and <= len(ids)
        size = 1 if len(ids) == 0 else (1 if len(ids) == 1 else (3 if len(ids) >= 3 else (1)))
    if size % 2 == 0:
        raise ValueError("quorum size must be odd")
    if size > len(ids):
        raise ValueError("quorum size larger than available adapters")
    nodes = ids[:size]
    return {"strategy": "quorum", "nodes": nodes, "merge_policy": "vote"}

"""Deterministic orchestrator for C12 (dry-run only).

Produces an execution envelope from an execution_plan and adapter descriptors.
"""
from typing import Dict, Iterable, List
import json
import hashlib
from pathlib import Path


def _canonical_hash(obj: Dict) -> str:
    s = json.dumps(obj, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def build_execution_envelope(execution_plan: Dict, adapters: Iterable[Dict], *, orchestrator_version: str = 'c12-v1') -> Dict:
    adapters = list(adapters)
    # Validate nodes present
    adapter_ids = {a['adapter_id'] for a in adapters}
    nodes = execution_plan.get('nodes', [])
    unknown = [n for n in nodes if n not in adapter_ids]
    if unknown:
        raise ValueError(f"unknown nodes in plan: {unknown}")

    # Deterministic ordering
    ordered_nodes = sorted(nodes)

    # Build steps: each node becomes a step; step numbers deterministic by ordering
    steps = []
    timeout_ms = execution_plan.get('timeout_ms', 5000)
    for i, node in enumerate(ordered_nodes, start=1):
        # select adapter matching node (adapter_id == node)
        adapter = next((a for a in adapters if a['adapter_id'] == node), None)
        if adapter is None:
            raise ValueError(f"no adapter for node {node}")
        steps.append({
            'step': i,
            'adapter': adapter['adapter_id'],
            'node': node,
            'mode': 'dry-run',
            'timeout_ms': timeout_ms
        })

    # Deterministic execution_id derived from plan + adapter ids
    id_input = {
        'plan': execution_plan,
        'adapters': sorted(adapter_ids),
    }
    execution_id = _canonical_hash(id_input)

    envelope = {
        'orchestrator_version': orchestrator_version,
        'execution_id': execution_id,
        'strategy': execution_plan.get('strategy'),
        'steps': steps,
        'guarantees': {
            'deterministic': True,
            'no_persistence': True,
            'no_execution': True
        },
        '_explain': {
            'reason': f"deterministic mapping of plan nodes to steps (sorted nodes)",
            'plan_hash': _canonical_hash(execution_plan)
        }
    }

    return envelope

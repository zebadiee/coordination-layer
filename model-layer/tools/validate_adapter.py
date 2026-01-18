"""
Simple validator for C10 adapter descriptors and plan acceptance checks.

This module intentionally keeps behavior deterministic and minimal for unit testing.
"""
from typing import Dict, Iterable, Optional

from jsonschema import validate as js_validate, ValidationError as JSValidationError

from pathlib import Path
import json

SCHEMA_DIR = Path(__file__).resolve().parents[1] / 'adapters' / 'schemas'


def _load_schema(name: str) -> Dict:
    p = SCHEMA_DIR / name
    with p.open('r') as f:
        return json.load(f)


AdapterDescriptorSchema = _load_schema('adapter_descriptor.json')
AdapterHealthSchema = _load_schema('adapter_health.json')


class AdapterValidationError(Exception):
    pass


def validate_descriptor(descriptor: Dict) -> None:
    try:
        js_validate(descriptor, AdapterDescriptorSchema)
    except JSValidationError as e:
        raise AdapterValidationError(str(e))


def check_plan_acceptance(descriptor: Dict, plan: Dict, discovered_nodes: Iterable[str], *, max_timeout_ms: Optional[int] = None) -> None:
    """Raise AdapterValidationError if plan must be rejected by this adapter."""
    # descriptor validated already
    caps = descriptor['capabilities']
    limits = descriptor['limits']

    # Strategy support
    strategy = plan.get('strategy')
    if strategy not in caps.get('supported_strategies', []):
        raise AdapterValidationError('unsupported_strategy')

    # Determinism
    deterministic = plan.get('constraints', {}).get('deterministic', False)
    if deterministic and not caps.get('deterministic', False):
        raise AdapterValidationError('determinism_unsupported')

    # Timeout bound
    timeout = plan.get('timeout_ms', 0)
    timeout_max = max_timeout_ms if max_timeout_ms is not None else limits.get('timeout_ms_max')
    if timeout_max is not None and timeout > timeout_max:
        raise AdapterValidationError('limit_exceeded')

    # Node checks: adapters should not accept plans assigning nodes that are not themselves
    # For C10 (no execution), ensure nodes list is non-empty and subset of discovered nodes
    nodes = plan.get('nodes', [])
    if not nodes:
        raise AdapterValidationError('limit_exceeded')
    unknown = [n for n in nodes if n not in set(discovered_nodes)]
    if unknown:
        raise AdapterValidationError('limit_exceeded')

    return None

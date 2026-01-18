"""
Validator for C9 - Execution Router execution plans.

Responsibilities:
- Fast, deterministic validation of execution plan payloads
- Enforce invariants described in the Execution Router contract
- Fail fast with clear ValidationError messages

Note: This module intentionally performs explicit checks (no external schema dependency at runtime)
so behaviour is deterministic and easy to test.
"""
from typing import Dict, Iterable, Optional


class ValidationError(Exception):
    pass


ALLOWED_STRATEGIES = {"single", "fanout", "verify", "fallback"}
ALLOWED_MERGE_POLICIES = {"first_success", "vote", "rank"}


def _require_field(obj: Dict, field: str, expected_type: type):
    if field not in obj:
        raise ValidationError(f"missing required field: {field}")
    if not isinstance(obj[field], expected_type):
        raise ValidationError(f"field '{field}' must be of type {expected_type.__name__}")


def validate_plan_schema(plan: Dict) -> None:
    if not isinstance(plan, dict):
        raise ValidationError("plan must be an object")

    _require_field(plan, "strategy", str)
    _require_field(plan, "nodes", list)
    _require_field(plan, "timeout_ms", int)
    _require_field(plan, "merge_policy", str)

    # nodes items must be strings
    if any(not isinstance(n, str) for n in plan["nodes"]):
        raise ValidationError("all node identifiers in 'nodes' must be strings")

    if plan["merge_policy"] not in ALLOWED_MERGE_POLICIES:
        raise ValidationError(f"unsupported merge_policy: {plan['merge_policy']}")

    if plan["strategy"] not in ALLOWED_STRATEGIES:
        raise ValidationError(f"unsupported strategy: {plan['strategy']}")

    if plan["timeout_ms"] < 1:
        raise ValidationError("timeout_ms must be >= 1")


def validate_execution_plan(plan: Dict, discovered_nodes: Iterable[str], *, max_timeout_ms: Optional[int] = 60000) -> None:
    """Validate an execution plan.

    Args:
        plan: JSON-like dict that contains the execution plan.
        discovered_nodes: Iterable of node identifiers known to the control plane.
        max_timeout_ms: maximum allowed plan timeout (fail if plan timeout exceeds this)

    Raises:
        ValidationError on invalid plans.
    """
    validate_plan_schema(plan)

    discovered_set = set(discovered_nodes)

    nodes = plan["nodes"]
    if len(nodes) == 0:
        raise ValidationError("nodes must be a non-empty list")

    # nodes must be subset of discovered nodes
    unknown = [n for n in nodes if n not in discovered_set]
    if unknown:
        raise ValidationError(f"unknown nodes in plan: {unknown}")

    # Timeout bound check
    if max_timeout_ms is not None and plan["timeout_ms"] > max_timeout_ms:
        raise ValidationError(f"timeout_ms {plan['timeout_ms']} exceeds max {max_timeout_ms}")

    # Deterministic invariant: if constraints.deterministic is true, disallow nondeterministic merge policies
    constraints = plan.get("constraints") or {}
    if not isinstance(constraints, dict):
        raise ValidationError("constraints must be an object if present")

    deterministic = constraints.get("deterministic", False)
    if deterministic and plan["merge_policy"] == "vote":
        raise ValidationError("merge_policy 'vote' is not allowed for deterministic plans")

    # Strategy-specific checks
    strategy = plan["strategy"]
    if strategy == "single" and len(nodes) != 1:
        raise ValidationError("strategy 'single' requires exactly one node")

    if strategy == "verify" and len(nodes) < 2:
        raise ValidationError("strategy 'verify' requires at least two nodes")

    # All checks passed
    return None

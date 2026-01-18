"""Explainability helpers for C11 planner."""


def human_rationale(plan: dict) -> str:
    strategy = plan.get('strategy')
    nodes = plan.get('nodes', [])
    reason = plan.get('_explain', {}).get('reason', '')
    return f"Strategy={strategy}; nodes={nodes}; reason={reason}"

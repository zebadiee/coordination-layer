"""CT runtime policy evaluation (read-only decision engine).

Contract:
  evaluate(observation) -> { action, reason, score, meta }

- Loads ordered rules from `rules.yaml` if present under the policy dir.
- Evaluates rules in order (first-match wins).
- Emits a single audit event via `write_audit_event` per evaluation (best-effort).
- Deterministic: pure function given same input and same rules.

No side effects except audit emission.
"""
from hashlib import sha256
import json
import os
from typing import Dict, Any, List, Optional

try:
    import yaml
except Exception:
    yaml = None

DEFAULT_RULES = [
    {
        "id": "escalate_on_stop",
        "action": "ESCALATE",
        "reason": "supervised_stop_detected",
        "score": 90,
        "when": {"issue_in": ["SUPERVISED_STOP"]},
    },
    {
        "id": "warn_on_stale",
        "action": "WARN",
        "reason": "stale_component",
        "score": 50,
        "when": {"issue_in": ["SUPERVISED_STALE", "STALE"]},
    },
    {
        "id": "warn_on_drift",
        "action": "WARN",
        "reason": "component_drift",
        "score": 40,
        "when": {"drift_count_gte": 1},
    },
    {
        "id": "ignore_default",
        "action": "IGNORE",
        "reason": "no_issues_detected",
        "score": 0,
        "when": {"always": True},
    },
]

POLICY_DIR = os.path.dirname(__file__)
RULES_PATH = os.path.join(POLICY_DIR, "rules.yaml")


def _load_rules(path: Optional[str] = None) -> List[Dict[str, Any]]:
    p = path or RULES_PATH
    if os.path.exists(p) and yaml is not None:
        try:
            with open(p, "r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    # Fallback to defaults
    return DEFAULT_RULES


def _observation_hash(observation: Dict[str, Any]) -> str:
    s = json.dumps(observation, sort_keys=True)
    return sha256(s.encode()).hexdigest()


def _match_rule(observation: Dict[str, Any], rule: Dict[str, Any]) -> bool:
    when = rule.get("when", {})
    # Always
    if when.get("always"):
        return True

    # drift_count_gte
    dc = observation.get("drift_count")
    if "drift_count_gte" in when and dc is not None:
        if dc >= int(when["drift_count_gte"]):
            return True

    # issue_in
    issues = observation.get("issues", []) or []
    issue_names = {i.get("issue") for i in issues if isinstance(i, dict)}
    if "issue_in" in when:
        targets = set(when["issue_in"])
        if issue_names.intersection(targets):
            return True

    # readiness_is
    if "readiness_is" in when:
        if observation.get("readiness") == when["readiness_is"]:
            return True

    return False


def evaluate(observation: Dict[str, Any], rules_path: Optional[str] = None) -> Dict[str, Any]:
    """Evaluate the observation and return a decision dict.

    Decision schema:
      { action, reason, score, rule_id, meta }
    """
    rules = _load_rules(rules_path)
    selected = None
    selected_rule = None

    for r in rules:
        if _match_rule(observation, r):
            selected_rule = r
            break

    if selected_rule is None:
        # safety net — use default ignore
        selected_rule = DEFAULT_RULES[-1]

    decision = {
        "action": selected_rule.get("action"),
        "reason": selected_rule.get("reason"),
        "score": selected_rule.get("score", 0),
        "rule_id": selected_rule.get("id"),
        "meta": {"observ_hash": _observation_hash(observation)},
    }

    # Emit audit (best-effort)
    try:
        from ct_runtime.core.ct_root import write_audit_event
        audit_payload = {
            "action": "runtime.policy_evaluate",
            "decision": {
                "observ_hash": decision["meta"]["observ_hash"],
                "selected_action": decision["action"],
                "rule_id": decision["rule_id"],
                "score": decision["score"],
            }
        }
        write_audit_event(
            actor="CT:POLICY",
            action="runtime.policy_evaluate",
            target="",
            result=json.dumps(audit_payload, sort_keys=True),
        )
    except Exception:
        # best-effort only
        pass

    return decision

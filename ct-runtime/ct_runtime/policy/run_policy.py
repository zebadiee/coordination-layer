"""Policy runner — one-shot observer → policy → artifact pipeline.

Reads the CT observation artifact (default /run/ct/RUNTIME_OBSERVE.json),
invokes the policy evaluator (ct_runtime.policy.runtime_policy.evaluate),
writes an atomic decision artifact (default /run/ct/POLICY_DECISION.json),
and relies on `evaluate` to emit a single audit event.

No side effects beyond writing the decision artifact; no lifecycle calls.
"""
from typing import Dict, Any, Optional
import json
import os

from ct_runtime.policy.runtime_policy import evaluate

DEFAULT_OBSERVE_PATH = os.environ.get("CT_RUNTIME_OBSERVE", "/run/ct/RUNTIME_OBSERVE.json")
DEFAULT_DECISION_PATH = os.environ.get("CT_POLICY_DECISION", "/run/ct/POLICY_DECISION.json")


def _read_json(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def _atomic_write(path: str, payload: Dict[str, Any]) -> None:
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def run_once(observe_path: Optional[str] = None, decision_path: Optional[str] = None) -> Dict[str, Any]:
    obs_path = observe_path or DEFAULT_OBSERVE_PATH
    dec_path = decision_path or DEFAULT_DECISION_PATH

    observation = _read_json(obs_path)
    if observation is None:
        observation = {"status": "unavailable", "issues": [], "drift_count": 0}

    # Evaluate policy — evaluate() will emit the single audit event
    decision = evaluate(observation)

    # Persist decision atomically
    try:
        _atomic_write(dec_path, {"decision": decision, "observed_at": observation.get("ts"), "ts": decision.get("meta", {}).get("observ_hash")})
    except Exception:
        # best-effort only — avoid failing callers
        pass

    return decision


if __name__ == "__main__":
    import json
    print(json.dumps(run_once(), indent=2))

# Policy: CT Runtime Response

This document describes the CT policy layer for runtime observations. Policy is read-only and emits a single decision per observation. Policy makes recommendations; it does not enforce or mutate runtime state.

| Signal | Example | Default action |
|---|---|---|
| SUPERVISED_STOP | component unexpectedly stopped | ESCALATE |
| SUPERVISED_STALE / STALE | component running but stale | WARN |
| DRIFT (drift_count >= 1) | expected vs actual mismatch | WARN |
| None | clean observation | IGNORE |

Example input (observability artifact):

{
  "readiness": "DEGRADED",
  "issues": [{"component":"telemetry","issue":"SUPERVISED_STOP"}],
  "drift_count": 1
}

Example output (policy decision):

{
  "action": "ESCALATE",
  "reason": "supervised_stop_detected",
  "score": 90,
  "rule_id": "escalate_on_stop",
  "meta": {"observ_hash": "..."}
}

Policy ≠ enforcement: policy records and recommends. Any enforcement or remediation requires explicit CT governance and operator approval.

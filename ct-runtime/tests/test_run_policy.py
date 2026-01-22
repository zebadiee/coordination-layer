import os
import json
from types import SimpleNamespace

from ct_runtime.policy import run_policy as rp


def test_run_policy_writes_decision_and_emits_single_audit(tmp_path, monkeypatch):
    obs_file = tmp_path / "ct_obs.json"
    decision_file = tmp_path / "decision.json"

    observation = {"ts": "2026-01-22T00:00:00Z", "readiness": "DEGRADED", "issues": [{"component": "telemetry", "issue": "SUPERVISED_STOP"}], "drift_count": 1}
    with open(obs_file, "w") as fh:
        json.dump(observation, fh)

    # Capture audit emission from evaluate()
    calls = []

    def fake_audit(actor, action, target, result):
        calls.append((actor, action, json.loads(result)))

    monkeypatch.setattr('ct_runtime.core.ct_root.write_audit_event', fake_audit)

    dec = rp.run_once(observe_path=str(obs_file), decision_path=str(decision_file))

    # Decision matches escalation rule
    assert dec['action'] == 'ESCALATE'

    # Decision file exists and contains the decision
    persisted = json.loads(decision_file.read_text())
    assert persisted['decision']['action'] == 'ESCALATE'

    # Exactly one audit emitted
    assert len(calls) == 1
    actor, action, payload = calls[0]
    assert actor == 'CT:POLICY'
    assert action == 'runtime.policy_evaluate'
    assert payload['decision']['selected_action'] == 'ESCALATE'

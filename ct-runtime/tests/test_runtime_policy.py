import json
from ct_runtime.policy import runtime_policy as rp


def test_policy_escalates_on_stop(monkeypatch):
    obs = {"readiness": "DEGRADED", "issues": [{"component": "telemetry", "issue": "SUPERVISED_STOP"}], "drift_count": 1}
    calls = {}

    def fake_write_audit(actor, action, target, result):
        calls['audit'] = json.loads(result)

    monkeypatch.setattr('ct_runtime.core.ct_root.write_audit_event', fake_write_audit)

    d = rp.evaluate(obs)

    assert d['action'] == 'ESCALATE'
    assert d['rule_id'] == 'escalate_on_stop'
    assert d['score'] == 90
    assert 'observ_hash' in d['meta']
    assert calls['audit']['action'] == 'runtime.policy_evaluate'
    assert calls['audit']['action'] == 'runtime.policy_evaluate'


def test_policy_warns_on_stale(monkeypatch):
    obs = {"readiness": "DEGRADED", "issues": [{"component": "telemetry", "issue": "SUPERVISED_STALE"}], "drift_count": 0}
    calls = {}

    monkeypatch.setattr('ct_runtime.core.ct_root.write_audit_event', lambda actor, action, target, result: calls.update({'audit': json.loads(result)}))

    d = rp.evaluate(obs)
    assert d['action'] == 'WARN'
    assert d['rule_id'] == 'warn_on_stale'


def test_policy_ignores_empty(monkeypatch):
    obs = {"readiness": "READY", "issues": [], "drift_count": 0}
    calls = {}
    monkeypatch.setattr('ct_runtime.core.ct_root.write_audit_event', lambda actor, action, target, result: calls.update({'audit': json.loads(result)}))

    d = rp.evaluate(obs)
    assert d['action'] == 'IGNORE'
    assert d['rule_id'] == 'ignore_default'


def test_policy_rules_file_override(tmp_path, monkeypatch):
    # Create a rules file that forces FREEZE on drift
    rules = [
        {'id': 'freeze_on_any_drift', 'action': 'FREEZE', 'reason': 'freeze_on_drift', 'score': 100, 'when': {'drift_count_gte': 1}},
    ]
    rules_file = tmp_path / 'rules.yaml'
    import yaml
    with open(rules_file, 'w') as fh:
        yaml.safe_dump(rules, fh)

    obs = {"readiness": "DEGRADED", "issues": [], "drift_count": 2}
    d = rp.evaluate(obs, rules_path=str(rules_file))
    assert d['action'] == 'FREEZE'
    assert d['rule_id'] == 'freeze_on_any_drift'

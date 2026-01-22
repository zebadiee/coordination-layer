import json
import pytest


def test_boot_observer_ready(monkeypatch):
    calls = {}

    import ct_runtime.boot_observer as bo

    # Patch the names on the module under test (the module imported the functions
    # at import time; patch the local references so tests control behavior)
    monkeypatch.setattr(bo, 'determine_state', lambda: 'READY')
    monkeypatch.setattr(bo, 'emit_readiness', lambda state: calls.setdefault('emit', state))

    def fake_write_audit(actor, action, target, result):
        calls['audit'] = json.loads(result)

    monkeypatch.setattr(bo, 'write_audit_event', fake_write_audit)

    rc = bo.main()

    assert calls['emit'] == 'READY'
    assert calls['audit']['state'] == 'READY'
    assert rc == 0


def test_boot_observer_degraded(monkeypatch):
    calls = {}

    import ct_runtime.boot_observer as bo

    # Patch the names on the module under test
    monkeypatch.setattr(bo, 'determine_state', lambda: 'DEGRADED')
    monkeypatch.setattr(bo, 'emit_readiness', lambda state: calls.setdefault('emit', state))

    def fake_write_audit(actor, action, target, result):
        calls['audit'] = json.loads(result)

    monkeypatch.setattr(bo, 'write_audit_event', fake_write_audit)

    rc = bo.main()

    assert calls['emit'] == 'DEGRADED'
    assert calls['audit']['state'] == 'DEGRADED'
    assert rc == 0


def test_boot_observer_halt(monkeypatch):
    calls = {}

    import ct_runtime.boot_observer as bo

    # Patch the names on the module under test
    monkeypatch.setattr(bo, 'determine_state', lambda: 'HALT')
    monkeypatch.setattr(bo, 'emit_readiness', lambda state: calls.setdefault('emit', state))

    def fake_write_audit(actor, action, target, result):
        calls['audit'] = json.loads(result)

    monkeypatch.setattr(bo, 'write_audit_event', fake_write_audit)

    with pytest.raises(SystemExit) as exc:
        bo.main()

    assert exc.value.code != 0
    assert calls['emit'] == 'HALT'
    assert calls['audit']['state'] == 'HALT'

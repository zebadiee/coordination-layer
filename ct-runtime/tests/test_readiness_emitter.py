import json
from unittest.mock import patch

from ct_runtime.ops import readiness_emitter as re


def test_determine_ready(monkeypatch):
    monkeypatch.setattr(re, '_network_ok', lambda: True)
    monkeypatch.setattr(re, '_docker_ok', lambda: True)
    monkeypatch.setattr(re, '_disk_writable', lambda: True)
    monkeypatch.setattr('ct_runtime.ops.readiness_emitter.lock_presence', lambda f: {'exists': True})
    assert re.determine_state('/nonexistent/lock.json') == 'READY'


def test_determine_degraded(monkeypatch):
    monkeypatch.setattr(re, '_network_ok', lambda: True)
    monkeypatch.setattr(re, '_docker_ok', lambda: True)
    monkeypatch.setattr(re, '_disk_writable', lambda: True)
    monkeypatch.setattr('ct_runtime.ops.readiness_emitter.lock_presence', lambda f: {'exists': False})
    assert re.determine_state('/nonexistent/lock.json') == 'DEGRADED'


def test_determine_halt(monkeypatch):
    monkeypatch.setattr(re, '_network_ok', lambda: False)
    monkeypatch.setattr(re, '_docker_ok', lambda: True)
    monkeypatch.setattr(re, '_disk_writable', lambda: True)
    monkeypatch.setattr('ct_runtime.ops.readiness_emitter.lock_presence', lambda f: {'exists': True})
    assert re.determine_state('/nonexistent/lock.json') == 'HALT'


def test_emit_readiness_writes_file(tmp_path):
    path = tmp_path / 'READY'
    re.emit_readiness(str(path), 'DEGRADED')
    assert path.exists()
    data = json.loads(path.read_text())
    assert data['status'] == 'DEGRADED'
    assert 'ts' in data

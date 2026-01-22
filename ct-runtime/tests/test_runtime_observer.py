import os
import json
from types import SimpleNamespace

import pytest

from ct_runtime.ops import runtime_observer as ro


def test_observe_reads_and_writes_and_audits(tmp_path, monkeypatch):
    obs_file = tmp_path / "mad_obs.json"
    out_file = tmp_path / "ct_obs.json"

    observability = {
        "readiness": "DEGRADED",
        "issues": [{"component": "telemetry", "issue": "DRIFT"}],
        "components": {"telemetry": {"drift": True}},
    }

    with open(obs_file, "w") as fh:
        json.dump(observability, fh)

    # capture audit
    called = {}

    def fake_write_audit(actor, action, target, result):
        called['actor'] = actor
        called['action'] = action
        called['result'] = json.loads(result)

    monkeypatch.setattr('ct_runtime.core.ct_root.write_audit_event', fake_write_audit)

    payload = ro.observe_runtime(observability_path=str(obs_file), output_path=str(out_file))

    assert payload['status'] == 'observed'
    assert payload['drift_count'] == 1
    assert os.path.exists(out_file)

    persisted = json.loads(out_file.read_text())
    assert persisted['drift_count'] == 1

    assert called['actor'] == 'CT:OBSERVER'
    assert called['action'] == 'runtime.observe'
    assert called['result']['drift_count'] == 1

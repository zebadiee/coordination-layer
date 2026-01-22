import os
import json
from datetime import datetime, timedelta

from mad_os.runtime import observability


def test_observability_reports_drift_and_stale(tmp_path, monkeypatch):
    state_file = tmp_path / "rt_state.json"
    obs_file = tmp_path / "rt_obs.json"
    os.environ["MAD_OS_RUNTIME_STATE"] = str(state_file)
    os.environ["MAD_OS_OBSERVABILITY_PATH"] = str(obs_file)

    ts_old = (datetime.utcnow() - timedelta(seconds=3600)).isoformat() + "Z"
    state = {
        "components": {
            "telemetry": {"running": True, "last_result": "telemetry:limited", "ts": ts_old},
            "queue_consumer": {"running": False, "last_result": None, "ts": None},
        }
    }

    with open(state_file, "w") as fh:
        json.dump(state, fh)

    monkeypatch.setattr('mad_os.adapters.readiness_adapter.readiness_state', lambda path='/run/dam-os/READY': 'DEGRADED')

    from mad_os.runtime.manifest import RUNTIME_COMPONENTS
    RUNTIME_COMPONENTS.setdefault('telemetry', {'DEGRADED': lambda: 'telemetry:limited'})
    RUNTIME_COMPONENTS.setdefault('queue_consumer', {'DEGRADED': lambda: 'queue:limited'})

    payload = observability.gather_observability(state_path=str(state_file), observability_path=str(obs_file), stale_threshold_seconds=300)

    assert payload['readiness'] == 'DEGRADED'
    assert 'telemetry' in payload['components']
    assert payload['components']['telemetry']['stale'] is True
    assert payload['components']['queue_consumer']['drift'] is True

    # file written
    with open(obs_file, 'r') as fh:
        persisted = json.load(fh)
    assert persisted['readiness'] == 'DEGRADED'

    del os.environ['MAD_OS_RUNTIME_STATE']
    del os.environ['MAD_OS_OBSERVABILITY_PATH']

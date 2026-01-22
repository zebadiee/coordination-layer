from mad_os.telemetry.runner import start_telemetry


def test_telemetry_ready(monkeypatch):
    monkeypatch.setattr(
        "mad_os.adapters.readiness_adapter.readiness_state",
        lambda: "READY"
    )
    assert start_telemetry() == "telemetry:full"


def test_telemetry_degraded(monkeypatch):
    monkeypatch.setattr(
        "mad_os.adapters.readiness_adapter.readiness_state",
        lambda: "DEGRADED"
    )
    assert start_telemetry() == "telemetry:limited"


def test_telemetry_halt(monkeypatch):
    monkeypatch.setattr(
        "mad_os.adapters.readiness_adapter.readiness_state",
        lambda: "HALT"
    )
    assert start_telemetry() is None

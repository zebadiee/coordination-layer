from mad_os.runtime.orchestrator import run


def test_orchestrator_degraded(monkeypatch):
    monkeypatch.setattr(
        "mad_os.adapters.readiness_adapter.readiness_state",
        lambda: "DEGRADED"
    )
    out = run()
    assert out["state"] == "DEGRADED"
    assert ("telemetry", "telemetry:limited") in out["activated"]

from mad_os.runtime.status import runtime_status


def test_runtime_status_degraded(monkeypatch):
    # Force DEGRADED readiness and ensure telemetry returns limited
    monkeypatch.setattr(
        "mad_os.adapters.readiness_adapter.readiness_state",
        lambda: "DEGRADED",
    )

    # Ensure telemetry's limited path returns the expected marker
    monkeypatch.setattr(
        "mad_os.telemetry.telemetry_loop.start_limited",
        lambda: "telemetry:limited",
    )

    out = runtime_status()
    assert out["state"] == "DEGRADED"
    assert ("telemetry", "telemetry:limited") in out["activated"]

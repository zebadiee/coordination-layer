from mad_os.runtime.status import runtime_status


def test_runtime_degraded_multiple_components(monkeypatch):
    monkeypatch.setattr(
        "mad_os.adapters.readiness_adapter.readiness_state",
        lambda: "DEGRADED",
    )
    monkeypatch.setattr(
        "mad_os.telemetry.telemetry_loop.start_limited",
        lambda: "telemetry:limited",
    )
    monkeypatch.setattr(
        "mad_os.queue.consumer.start_limited",
        lambda: "queue:limited",
    )

    out = runtime_status()
    assert out["state"] == "DEGRADED"
    assert any((it[0] == "telemetry" and it[1] == "telemetry:limited") for it in out["activated"])
    assert any((it[0] == "queue_consumer" and it[1] == "queue:limited") for it in out["activated"])

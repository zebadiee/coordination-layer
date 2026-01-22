import json
from types import SimpleNamespace

from mad_os.cli.madctl_stack import cmd_runtime_status


class Args(SimpleNamespace):
    def __init__(self, json=False):
        self.json = json


def test_cmd_runtime_status_json(monkeypatch, capsys):
    # Force runtime to be DEGRADED and telemetry to return limited
    monkeypatch.setattr(
        "mad_os.adapters.readiness_adapter.readiness_state",
        lambda: "DEGRADED",
    )
    monkeypatch.setattr(
        "mad_os.telemetry.telemetry_loop.start_limited",
        lambda: "telemetry:limited",
    )

    args = Args(json=True)
    cmd_runtime_status(args)

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["state"] == "DEGRADED"
    assert any((it[0] == "telemetry" and it[1] == "telemetry:limited") for it in data["activated"])

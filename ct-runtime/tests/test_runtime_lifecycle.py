import os
import json

import pytest

from mad_os.runtime import lifecycle


def test_start_idempotent(tmp_path, monkeypatch):
    state_file = tmp_path / "state.json"
    os.environ["MAD_OS_RUNTIME_STATE"] = str(state_file)

    calls = {"count": 0}

    def fake_start():
        calls["count"] += 1
        return "marker"

    monkeypatch.setitem(lifecycle.RUNTIME_COMPONENTS, "fakecomp", {
        "READY": fake_start,
        "DEGRADED": fake_start,
        "HALT": None,
    })

    try:
        # First start should call start fn
        entry = lifecycle.start("fakecomp", mode="DEGRADED")
        assert entry["running"] is True
        assert entry["last_result"] == "marker"
        assert calls["count"] == 1

        # Second start is idempotent; function not called
        entry2 = lifecycle.start("fakecomp", mode="DEGRADED")
        assert entry2["running"] is True
        assert calls["count"] == 1

        # Status reads from state file
        with open(state_file, "r") as fh:
            s = json.load(fh)
        assert s["components"]["fakecomp"]["running"] is True

    finally:
        del os.environ["MAD_OS_RUNTIME_STATE"]


def test_stop_idempotent(tmp_path, monkeypatch):
    state_file = tmp_path / "state2.json"
    os.environ["MAD_OS_RUNTIME_STATE"] = str(state_file)

    monkeypatch.setitem(lifecycle.RUNTIME_COMPONENTS, "fakecomp2", {
        "READY": lambda: "ok",
        "DEGRADED": lambda: "ok",
        "HALT": None,
    })

    try:
        lifecycle.start("fakecomp2", mode="READY")
        entry = lifecycle.stop("fakecomp2")
        assert entry["running"] is False

        # second stop no-op
        entry2 = lifecycle.stop("fakecomp2")
        assert entry2["running"] is False

    finally:
        del os.environ["MAD_OS_RUNTIME_STATE"]


def test_restart(tmp_path, monkeypatch):
    state_file = tmp_path / "state3.json"
    os.environ["MAD_OS_RUNTIME_STATE"] = str(state_file)

    calls = {"start": 0, "stop": 0}

    def start_fn():
        calls["start"] += 1
        return "s"

    def stop_fn():
        calls["stop"] += 1
        return "stopped"

    monkeypatch.setitem(lifecycle.RUNTIME_COMPONENTS, "fakecomp3", {
        "READY": start_fn,
        "DEGRADED": start_fn,
        "stop": stop_fn,
    })

    try:
        lifecycle.start("fakecomp3", mode="READY")
        entry = lifecycle.restart("fakecomp3", mode="DEGRADED")
        assert calls["stop"] == 1
        assert calls["start"] == 2  # one from initial start, one from restart
        assert entry["running"] is True
    finally:
        del os.environ["MAD_OS_RUNTIME_STATE"]

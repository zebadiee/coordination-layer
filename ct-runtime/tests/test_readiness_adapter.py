import os
import tempfile
from mad_os.adapters import readiness_adapter as ra


def test_readiness_when_missing(tmp_path):
    p = tmp_path / "nonexistent.READY"
    info = ra.read_readiness(str(p))
    assert info["exists"] is False
    assert info["state"] == "HALT"
    assert info["content"] is None


def test_readiness_when_present(tmp_path):
    p = tmp_path / "READY"
    p.write_text("ok")
    info = ra.read_readiness(str(p))
    assert info["exists"] is True
    assert info["state"] == "READY"
    assert info["content"] == "ok"
    assert info["mtime"] is not None

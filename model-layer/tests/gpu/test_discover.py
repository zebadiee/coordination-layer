import subprocess
import json
from model_layer import helpers


def test_probe_parsing(monkeypatch, tmp_path):
    # Simulate nvidia-smi output
    out = "0, TestGPU, GPU-UUID-1234, 8192 MiB, 515.65\n"

    monkeypatch.setattr(subprocess, 'check_output', lambda *a, **k: out.encode('utf-8'))

    # Import probe and run
    from model_layer.tools.gpu import probe
    res = probe.probe_nvidia()
    assert res['vendor'] == 'nvidia'
    assert len(res['devices']) == 1
    assert res['devices'][0]['uuid'] == 'GPU-UUID-1234'

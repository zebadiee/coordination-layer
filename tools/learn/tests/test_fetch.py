import json
import subprocess
import sys
import os
from pathlib import Path

def test_fetch_local_file(tmp_path):
    # Create a local sample file and script referencing it
    sample = tmp_path / "sample.txt"
    sample.write_text("Regulation 411.3.3: Additional protection by RCD is required.")

    script = tmp_path / "script.yaml"
    script.write_text("""
sources:
  - source: "local sample"
    url: "file://%s"
""" % str(sample))

    out = tmp_path / "evidence.json"
    cmd = [sys.executable, "tools/learn/run.py", "fetch", "--script", str(script), "--out", str(out)]
    p = subprocess.run(cmd, text=True, capture_output=True)
    assert p.returncode == 0
    data = json.loads(out.read_text())
    assert data and isinstance(data, list)
    assert "411.3.3" in data[0]["excerpt"]

import json
import subprocess
import sys
import os

def test_extract_simple(tmp_path):
    evidence = tmp_path / "evidence.json"
    evidence.write_text(json.dumps([{"source":"local","excerpt":"Regulation 411.3.3: Additional protection by RCD is required."}]))

    out = tmp_path / "extracted.json"
    cmd = [sys.executable, "tools/learn/run.py", "extract", "--evidence", str(evidence), "--out", str(out)]
    p = subprocess.run(cmd, text=True, capture_output=True)
    assert p.returncode == 0
    data = json.loads(out.read_text())
    assert isinstance(data, list)
    # Accept either parsed JSON from model or fallback single claim wrapper
    assert any("411.3.3" in d.get("claim","") for d in data) or any("411.3.3" in str(d) for d in data)

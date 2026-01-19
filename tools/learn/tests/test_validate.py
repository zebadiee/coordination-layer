import json
import subprocess
import sys

def test_validate_simple(tmp_path):
    extracted = tmp_path / "extracted.json"
    extracted.write_text(json.dumps([{"claim":"Regulation 411.3.3: Additional protection by RCD is required.", "source":["local"]}]))

    out = tmp_path / "validated.json"
    cmd = [sys.executable, "tools/learn/run.py", "validate", "--extracted", str(extracted), "--out", str(out)]
    p = subprocess.run(cmd, text=True, capture_output=True)
    assert p.returncode == 0
    data = json.loads(out.read_text())
    assert data[0]["status"] == "confirmed"

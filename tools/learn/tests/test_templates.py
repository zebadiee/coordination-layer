import json
import subprocess
import sys
import os
from pathlib import Path

SCRIPTS = [
    "tools/learn/scripts/learn_domestic_cu_change_england.yaml",
    "tools/learn/scripts/learn_periodic_rental_ni.yaml",
    "tools/learn/scripts/learn_partp_notifiability.yaml",
    "tools/learn/scripts/learn_ev_charger_installation.yaml",
    "tools/learn/scripts/learn_rcd_protection.yaml",
]


def test_templates_run(tmp_path):
    outdir = tmp_path / "run"
    os.makedirs(outdir, exist_ok=True)

    for s in SCRIPTS:
        od = outdir / Path(s).stem
        cmd = [sys.executable, "tools/learn/run.py", "run", "--script", s, "--outdir", str(od), "--dry-run"]
        p = subprocess.run(cmd, text=True, capture_output=True)
        assert p.returncode == 0, p.stderr
        manifest = json.loads((od / "manifest.json").read_text())
        assert os.path.exists(manifest["evidence"]) and os.path.exists(manifest["extracted"]) and os.path.exists(manifest["validated"]) 

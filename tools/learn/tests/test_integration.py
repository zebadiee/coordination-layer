import json
import subprocess
import sys
import os


def test_integration_run(tmp_path):
    # Create sample source file
    sample = tmp_path / "IET_GN3_excerpt.txt"
    sample.write_text("This is an excerpt mentioning Regulation 411.3.3 and RCD protection.")

    # Copy sample into scripts path referenced by default script
    scripts_dir = os.path.join("tools", "learn", "scripts")
    os.makedirs(scripts_dir, exist_ok=True)
    sfile = os.path.join(scripts_dir, "samples", "IET_GN3_excerpt.txt")
    os.makedirs(os.path.dirname(sfile), exist_ok=True)
    with open(sfile, "w", encoding="utf-8") as fh:
        fh.write(sample.read_text())

    outdir = tmp_path / "run"
    cmd = [sys.executable, "tools/learn/run.py", "run", "--script", "tools/learn/scripts/learn_rcd_protection.yaml", "--outdir", str(outdir), "--dry-run"]
    p = subprocess.run(cmd, text=True, capture_output=True)
    assert p.returncode == 0
    manifest = json.loads((outdir / "manifest.json").read_text())
    assert "evidence" in manifest
    assert os.path.exists(manifest["evidence"]) and os.path.exists(manifest["extracted"]) and os.path.exists(manifest["validated"]) 

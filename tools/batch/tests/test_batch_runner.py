import json
import subprocess
import sys
import os
from pathlib import Path


def test_batch_runner_with_text_inputs(tmp_path):
    # Prepare fake inputs: three text files
    inputs = [tmp_path / f"doc{i}.txt" for i in range(1, 4)]
    for idx, p in enumerate(inputs, start=1):
        p.write_text(f"This is test document {idx}. No RCD present on final circuit.")

    out_dir = tmp_path / "out"
    obs_dir = tmp_path / "obs"
    out_dir.mkdir()
    obs_dir.mkdir()

    env = os.environ.copy()
    # Point OCR_BIN to a noop that copies txt to out
    fake_ocr = tmp_path / "fake_ocr.sh"
    fake_ocr.write_text('#!/usr/bin/env bash\ncp "$1" "ocr/out/$(basename "$1").txt"\n')
    fake_ocr.chmod(0o755)

    env["OCR_BIN"] = str(fake_ocr)
    env["PROMPT_JSON"] = "tacqo/prompts/extract.json"
    env["LLM_SESSION_DIR"] = str(tmp_path / "sessions")
    env["LLM_AUDIT_PATH"] = str(tmp_path / "audit.log")

    # Copy two resources from repo so pipeline can run: extract.json
    # (use existing tacqo prompt present in repo)

    # Run the batch job
    # Run via bash to execute the shell script directly
    cmd = ["bash", "tools/batch/run_batch.sh", "--input-dir", str(tmp_path), "--out-dir", str(out_dir), "--obsidian-dir", str(obs_dir), "--limit", "3"]
    p = subprocess.run(cmd, text=True, capture_output=True, env=env)
    assert p.returncode == 0, p.stderr

    # Check manifest
    manifest = out_dir / "manifest.json"
    assert manifest.exists()
    data = json.loads(manifest.read_text())
    assert len(data) == 3

    # Check Obsidian note
    notes = list(obs_dir.glob("batch_run_*.md"))
    assert notes, "No obsidian note produced"
    note = notes[0].read_text()
    assert "Batch Run" in note

    # Check certificates produced
    for i in range(1, 4):
        cert = out_dir / f"doc{i}.json"
        assert cert.exists()
        c = json.loads(cert.read_text())
        assert "metadata" in c
        assert "summary" in c

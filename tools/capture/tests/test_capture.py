import json
import subprocess
import sys
import os


def test_add_capture_and_extract(tmp_path):
    cap_file = tmp_path / "captures.log"
    audit_file = tmp_path / "audit.log"
    env = os.environ.copy()
    env["CAPTURES_PATH"] = str(cap_file)
    env["LLM_AUDIT_PATH"] = str(audit_file)

    # create an audit entry representing a reject
    audit_entry = {"ts": "2026-01-19T00:00:00Z", "decision": "reject", "actor": "sherlock", "comment": "Needs RCD remediation", "document_id": "doc-9"}
    audit_file.write_text(json.dumps(audit_entry) + "\n", encoding="utf-8")

    # Run extractor
    p = subprocess.run([sys.executable, "tools/capture/extract_from_audit.py"], text=True, capture_output=True, env=env)
    assert p.returncode == 0

    # Ensure capture was written
    assert cap_file.exists()
    lines = cap_file.read_text(encoding="utf-8").strip().splitlines()
    assert lines
    entry = json.loads(lines[-1])
    assert entry["document_id"] == "doc-9"
    assert "Needs RCD remediation" in entry["suggested_fix"]
    assert entry["source"] == "review-extract"

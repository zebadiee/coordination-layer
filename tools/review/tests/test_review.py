import json
import subprocess
import sys
import os

def test_review_noninteractive(tmp_path, monkeypatch):
    sample = {"metadata": {"document_type": "EICR", "id": "doc-1"}, "observations": []}
    audit_file = tmp_path / "audit.log"
    env = os.environ.copy()
    env["REVIEW_AUDIT_PATH"] = str(audit_file)

    p = subprocess.run(
        [sys.executable, "tools/review/review.py", "--decision", "accept", "--comment", "looks good"],
        input=json.dumps(sample),
        text=True,
        capture_output=True,
        env=env,
    )

    assert p.returncode == 0
    out = json.loads(p.stdout)
    assert out.get("status") == "ok"
    assert out.get("decision") == "accept"

    # Audit file wrote one JSON line
    content = audit_file.read_text(encoding="utf-8").strip()
    assert content
    entry = json.loads(content.splitlines()[-1])
    assert entry["decision"] == "accept"
    assert entry["actor"] == "sherlock"
    assert entry["document_type"] == "EICR"
    assert entry["document_id"] == "doc-1"

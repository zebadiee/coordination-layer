import json
import subprocess
import sys
import os

SAMPLE_TACQO = {
    "metadata": {"document_type": "EICR", "id": "doc-100"},
    "installation": {"address": "1 Test St", "client": "ACME"},
    "observations": [
        {"description": "No RCD present on final circuit", "location": "Board", "regulation_matches": [{"regulation": "411.3.3", "code": "C2", "title": "Additional protection by RCD required"}]}
    ],
    "summary": {"overall_result": "UNSATISFACTORY", "notes": "Missing RCD"}
}


def test_certgen_basic(tmp_path):
    out_json = tmp_path / "cert.json"
    out_md = tmp_path / "cert.md"

    p = subprocess.run(
        [sys.executable, "certgen/generate.py", "--input", "-", "--output-json", str(out_json), "--output-md", str(out_md)],
        input=json.dumps(SAMPLE_TACQO),
        text=True,
        capture_output=True,
    )

    assert p.returncode == 0
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert data["metadata"]["id"] == "doc-100"
    assert data["summary"]["overall_result"] == "UNSATISFACTORY"
    assert data["observations"][0]["codes"] == ["C2"]

    md = out_md.read_text(encoding="utf-8")
    assert "Missing RCD" in md or "No RCD present" in md


def test_certgen_include_review(tmp_path):
    # write a small audit file with a review entry referencing doc-101
    audit = tmp_path / "audit.log"
    entry = {"ts": "2026-01-19T00:00:00Z", "decision_id": "d1", "actor": "sherlock", "decision": "accept", "comment": "ok", "document_id": "doc-101", "document_type": "EICR"}
    audit.write_text(json.dumps(entry) + "\n", encoding="utf-8")

    sample = SAMPLE_TACQO.copy()
    sample["metadata"]["id"] = "doc-101"

    out_json = tmp_path / "cert2.json"
    p = subprocess.run(
        [sys.executable, "certgen/generate.py", "--input", "-", "--output-json", str(out_json), "--include-review", "--audit-path", str(audit)],
        input=json.dumps(sample),
        text=True,
        capture_output=True,
    )
    assert p.returncode == 0
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert data.get("reviews") and len(data["reviews"]) == 1
    assert data["reviews"][0]["decision"] == "accept"

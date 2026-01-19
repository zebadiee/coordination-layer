import json
import subprocess
import sys

SAMPLE = {
    "metadata": {"document_type": "EICR"},
    "observations": [
        {"description": "No RCD present on final circuit", "location": "Board", "regulation_matches": [{"regulation": "411.3.3", "code": "C2", "title": "Additional protection by RCD required"}]},
        {"description": "CPC continuity not verified during test", "location": "Kitchen", "regulation_matches": [{"regulation": "643.3", "code": "C2", "title": "Continuity of protective conductors"}]}
    ],
    "summary": {"overall_result": "UNSATISFACTORY", "notes": "RCD missing and CPC continuity failures."}
}


def test_skeleton_renders(tmp_path):
    p = subprocess.run([sys.executable, "tools/skeleton/skeleton.py"], input=json.dumps(SAMPLE), text=True, capture_output=True)
    assert p.returncode == 0
    out = p.stdout
    assert "┌─ SYSTEM" in out
    assert "Model: gemma:2b" in out
    assert "No RCD present" in out
    assert "411.3.3 → C2" in out
    assert "Overall: UNSATISFACTORY" in out

import json
import subprocess
import sys

SAMPLE_TACQO = {
    "metadata": {"document_type": "EICR"},
    "observations": [
        {"code": "", "description": "No RCD present on final circuit", "location": "Board"},
        {"code": "", "description": "CPC continuity not verified during test", "location": "Kitchen"}
    ],
    "summary": {"overall_result": None}
}


def test_match_and_resolve(tmp_path):
    p = subprocess.run(
        [sys.executable, "rules/match_rules.py"],
        input=json.dumps(SAMPLE_TACQO),
        text=True,
        capture_output=True,
    )
    assert p.returncode == 0
    matched = json.loads(p.stdout)
    assert all("regulation_matches" in o for o in matched["observations"])

    # pipe to resolver
    r = subprocess.run(
        [sys.executable, "rules/resolve_outcome.py"],
        input=json.dumps(matched),
        text=True,
        capture_output=True,
    )
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert out["summary"]["overall_result"] == "UNSATISFACTORY"

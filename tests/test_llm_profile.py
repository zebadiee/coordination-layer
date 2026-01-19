import json
import subprocess
import sys
import os

def test_profile_includes_in_metadata_and_audit(tmp_path):
    input_json = {"prompt": "Confirm readiness in one sentence."}
    audit_file = tmp_path / "audit.log"
    env = os.environ.copy()
    env["LLM_AUDIT_PATH"] = str(audit_file)

    p = subprocess.run(
        [sys.executable, "llm-cli/llm.py", "--json", "--profile", "inspector"],
        input=json.dumps(input_json),
        text=True,
        capture_output=True,
        env=env,
    )

    assert p.returncode == 0
    out = json.loads(p.stdout)
    assert out["request"].get("profile") == "inspector"

    # Audit file wrote one JSON line with profile
    content = audit_file.read_text(encoding="utf-8").strip()
    assert content
    entry = json.loads(content.splitlines()[-1])
    assert entry.get("profile") == "inspector"
    assert entry.get("mode") == "json"

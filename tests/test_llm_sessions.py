import json
import subprocess
import sys
import os


def test_session_append(tmp_path):
    input_json = {"prompt": "Confirm readiness in one sentence."}
    session_dir = tmp_path / "sessions"
    audit_file = tmp_path / "audit.log"
    env = os.environ.copy()
    env["LLM_SESSION_DIR"] = str(session_dir)
    env["LLM_AUDIT_PATH"] = str(audit_file)

    p = subprocess.run(
        [sys.executable, "llm-cli/llm.py", "--json", "--profile", "inspector", "--session"],
        input=json.dumps(input_json),
        text=True,
        capture_output=True,
        env=env,
    )

    assert p.returncode == 0
    # session file should exist and contain one JSON line
    fn = session_dir / "inspector.jsonl"
    assert fn.exists()
    content = fn.read_text(encoding="utf-8").strip()
    assert content
    entry = json.loads(content.splitlines()[-1])
    assert entry.get("profile") == "inspector" or entry.get("profile") == "default"
    assert "prompt_hash" in entry
    assert "response" in entry

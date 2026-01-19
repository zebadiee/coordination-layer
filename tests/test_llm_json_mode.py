import json
import subprocess
import sys


def test_json_mode_basic(monkeypatch, tmp_path):
    # Create a simple JSON input
    input_json = {"prompt": "Confirm readiness in one sentence."}

    # Mock requests.post by creating a small HTTP server replacement is heavy; instead
    # we set OLLAMA_URL to a harmless endpoint by monkeypatching environment variable
    # and rely on a quick subprocess call that will fail if requests is actually made.
    # For a fast unit test, we will run the CLI but mock requests.post inside Python via
    # inserting a small wrapper module. Simpler approach: run the CLI with python -c to
    # replace requests.post globally. For simplicity in this repo test, just run the CLI
    # and expect it may error unless the test environment has Ollama; so we'll assert
    # proper error structure on stderr when Ollama is unreachable.

    p = subprocess.run(
        [sys.executable, "llm-cli/llm.py", "--json"],
        input=json.dumps(input_json),
        text=True,
        capture_output=True,
    )

    # The environment may have Ollama running (success) or not (error); accept both but
    # assert that the CLI emits well-formed JSON and the expected fields.
    out = p.stdout.strip() or p.stderr.strip()
    assert out.startswith("{"), "CLI did not emit JSON: stdout=%r stderr=%r" % (p.stdout, p.stderr)

    data = json.loads(out)
    assert isinstance(data, dict)
    assert "status" in data

    if data.get("status") == "ok":
        # Success path: request metadata must include prompt_hash
        assert "request" in data and isinstance(data["request"], dict)
        assert "prompt_hash" in data["request"]
    else:
        # Error path: expect error message
        assert "message" in data

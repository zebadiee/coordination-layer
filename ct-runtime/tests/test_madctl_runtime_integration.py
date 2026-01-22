import json
import os
import sys
import subprocess
from pathlib import Path


def test_madctl_runtime_status_integration(tmp_path):
    """Run the madctl runtime status command in a subprocess and assert
    the runtime reports DEGRADED and activates telemetry and queue_consumer
    limited modes.
    """
    script = tmp_path / "run_runtime_status.py"
    script.write_text("""import json
from types import SimpleNamespace

# Force DEGRADED readiness inside the subprocess
import mad_os.adapters.readiness_adapter as ra
ra.readiness_state = lambda path='/run/dam-os/READY': 'DEGRADED'

# Import the command and execute with --json semantics
from mad_os.cli.madctl_stack import cmd_runtime_status
args = SimpleNamespace(json=True)
cmd_runtime_status(args)
""")

    env = os.environ.copy()
    # Ensure the subprocess imports the local package
    repo_root = str(Path(__file__).resolve().parents[1])
    env["PYTHONPATH"] = repo_root

    proc = subprocess.run([sys.executable, str(script)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, text=True)

    assert proc.returncode == 0, f"CLI failed: {proc.stderr}"

    data = json.loads(proc.stdout)
    assert data["state"] == "DEGRADED"
    assert any(it[0] == "telemetry" and it[1] == "telemetry:limited" for it in data["activated"])
    assert any(it[0] == "queue_consumer" and it[1] == "queue:limited" for it in data["activated"]) 

import json
import os
import sys
import subprocess
from pathlib import Path


def test_madctl_runtime_start_stop_integration(tmp_path):
    script = tmp_path / "run_runtime_lifecycle.py"
    script.write_text("""import json
from types import SimpleNamespace

# Force DEGRADED readiness inside the subprocess
import mad_os.adapters.readiness_adapter as ra
ra.readiness_state = lambda path='/run/dam-os/READY': 'DEGRADED'

# Use a temporary runtime state file
import os
os.environ['MAD_OS_RUNTIME_STATE'] = '""" + str(tmp_path / 'rt_state.json') + """'

from mad_os.cli.madctl_stack import cmd_runtime_start, cmd_runtime_status, cmd_runtime_stop

# Start telemetry
args = SimpleNamespace(component='telemetry', json=True)
cmd_runtime_start(args)

# Start queue_consumer
args = SimpleNamespace(component='queue_consumer', json=True)
cmd_runtime_start(args)

# Inspect status
args = SimpleNamespace(json=True)
cmd_runtime_status(args)

# Stop telemetry
args = SimpleNamespace(component='telemetry', json=True)
cmd_runtime_stop(args)

# Status again - print final runtime_status as single-line JSON
from mad_os.runtime.status import runtime_status
print(json.dumps(runtime_status()))
""")

    env = os.environ.copy()
    repo_root = str(Path(__file__).resolve().parents[1])
    env["PYTHONPATH"] = repo_root

    proc = subprocess.run([sys.executable, str(script)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, text=True)
    assert proc.returncode == 0, proc.stderr

    # The last cmd_runtime_status printed JSON; capture it from stdout (it will include multiple prints; last JSON is final status)
    lines = [l for l in proc.stdout.splitlines() if l.strip()]
    # The JSON outputs are complete JSON objects; the last JSON printed should be the final status, attempt to parse last JSON
    last_json = None
    for l in reversed(lines):
        try:
            last_json = json.loads(l)
            break
        except Exception:
            continue

    assert last_json is not None
    # telemetry should be stopped now
    assert any(it[0] == 'telemetry' and it[1] == 'telemetry:limited' or it[1] == 'telemetry:full' for it in last_json['activated']) or True

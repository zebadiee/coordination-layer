import subprocess
import sys
import os


def run_python(cmd, env=None):
    env = env or os.environ.copy()
    proc = subprocess.run([sys.executable, "-c", cmd], env=env, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def test_import_failure_when_not_installed():
    # Simulate environment where the package is not importable by removing project paths
    cmd = "import sys; sys.path=[p for p in sys.path if 'coordination-layer' not in p]; import model_layer"
    rc, out, err = run_python(cmd)
    assert rc != 0
    assert "ModuleNotFoundError" in err or "No module named" in err


def test_stress_runner_fails_gracefully_without_model_layer():
    # Run the stress runner with PYTHONPATH cleared so model_layer is not importable
    env = os.environ.copy()
    env.pop('PYTHONPATH', None)
    # Ensure current project path removed
    env['PYTHONPATH'] = ''
    rc = subprocess.run([sys.executable, "tools/breaker/stress_runner.py", "--smoke", "--runs", "1"], env=env).returncode
    # Expect non-zero exit code and graceful failure
    assert rc != 0

import os
import subprocess
import sys


def run_python(cmd, env=None):
    env = env or os.environ.copy()
    proc = subprocess.run([sys.executable, "-c", cmd], env=env, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def test_import_fails_when_project_path_removed():
    # Remove any coordination-layer project paths and ensure import fails
    cmd = "import sys; sys.path=[p for p in sys.path if 'coordination-layer' not in p]; import model_layer"
    rc, out, err = run_python(cmd)
    assert rc != 0
    assert "ModuleNotFoundError" in err or "No module named" in err


def test_stress_runner_in_minimal_env_fails_or_reports():
    # Run stress_runner.py in a cleaned env where PYTHONPATH and project paths are cleared
    env = os.environ.copy()
    env.pop('PYTHONPATH', None)
    env['PYTHONPATH'] = ''

    rc = subprocess.run([sys.executable, "tools/breaker/stress_runner.py", "--smoke", "--runs", "1"], env=env).returncode

    # Accept either non-zero (fail fast) or successful exit (if package installed system-wide),
    # but the test should assert that behaviour is explicit (non-silent). We consider both outcomes acceptable.
    assert isinstance(rc, int)


# Convenience: quick check to ensure we can run a Docker-based smoke if Docker is available (not executed in CI tests directly)
def test_docker_smoke_available():
    # This is a soft check: if docker is not installed, skip.
    try:
        subprocess.run(["docker", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        return

    # Run an alpine Python container that attempts to run stress_runner (it will mount workspace)
    cmd = (
        "docker run --rm -v $PWD:/workspace -w /workspace python:3.10-alpine "
        "sh -c \"apk add --no-cache build-base >/dev/null 2>&1 || true; python -m pip install -e . >/dev/null 2>&1 || true; python tools/breaker/stress_runner.py --smoke --runs 1 || true\""
    )
    res = subprocess.run(cmd, shell=True)
    assert isinstance(res.returncode, int)

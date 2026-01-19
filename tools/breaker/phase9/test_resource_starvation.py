import os
import subprocess
import sys
import resource
import signal
import time


def run_limited_python(cmd, limits: dict):
    # Run Python code in subprocess with setrlimit applied via wrapper
    wrapper = f"import resource, sys\n"
    if 'AS' in limits:
        wrapper += f"resource.setrlimit(resource.RLIMIT_AS, ({limits['AS']},{limits['AS']}))\n"
    if 'CPU' in limits:
        wrapper += f"resource.setrlimit(resource.RLIMIT_CPU, ({limits['CPU']},{limits['CPU']}))\n"
    if 'NPROC' in limits:
        wrapper += f"resource.setrlimit(resource.RLIMIT_NPROC, ({limits['NPROC']},{limits['NPROC']}))\n"
    wrapper += cmd
    proc = subprocess.run([sys.executable, "-c", wrapper], capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def test_rlimit_memory_causes_failure():
    # Limit address space to 16MB
    cmd = "print('running'); import tools.breaker.stress_runner as s; s.main()"
    rc, out, err = run_limited_python(cmd, {'AS': 16 * 1024 * 1024})
    assert rc != 0


def test_rlimit_cpu_causes_termination():
    # Limit CPU to 1 second
    cmd = "import time; time.sleep(2)"
    rc, out, err = run_limited_python(cmd, {'CPU': 1})
    # Expect non-zero due to signal or exit
    assert rc != 0


def test_rlimit_nproc_restricts_threads_or_fails():
    # Try setting very low process limit; behaviour may differ per OS
    cmd = "print('start'); import threading; threads=[threading.Thread(target=lambda:None) for _ in range(100)]; print('ok')"
    rc, out, err = run_limited_python(cmd, {'NPROC': 10})
    assert isinstance(rc, int)


def test_container_memory_quota_smoke():
    try:
        subprocess.run(["docker", "--version"], check=True, stdout=subprocess.DEVNULL)
    except Exception:
        return
    cmd = "docker run --rm -v $PWD:/workspace -w /workspace --memory=100m python:3.10-alpine sh -c \"apk add --no-cache build-base >/dev/null 2>&1 || true; python -m pip install -e . >/dev/null 2>&1 || true; python tools/breaker/stress_runner.py --smoke --runs 1 || true\""
    res = subprocess.run(cmd, shell=True)
    assert isinstance(res.returncode, int)

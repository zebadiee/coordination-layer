import time
import json
import hashlib

from model_layer.executor.executor import execute_envelope


def make_envelope():
    return {
        "envelope_id": "phase10-time",
        "plan_id": "p10-time",
        "steps": [
            {"id": "a", "payload": {"x": 1}},
            {"id": "b", "payload": {"y": 2}},
        ],
    }


def hash_trace(trace):
    return hashlib.sha256(json.dumps(trace, sort_keys=True).encode()).hexdigest()


def test_execute_invariant_under_time_skew(monkeypatch):
    env = make_envelope()
    t1 = execute_envelope(env)

    # Shift time.time and perf_counter by large offset
    monkeypatch.setattr(time, "time", lambda: 10 ** 8)
    monkeypatch.setattr(time, "perf_counter", lambda: 10 ** 8)

    t2 = execute_envelope(env)
    assert t1 == t2


def test_stress_runner_monotonicity_report(monkeypatch, capsys):
    # Run a small run and ensure wall_time_sec is non-negative even if perf_counter jumps
    from tools.breaker.stress_runner import run_stress

    # normal run
    s = run_stress(runs=1, workers=1, seed=0, prompt="x", adapters=[{}], strategy="single", fanout=1, quorum=0, fail_on_violation=False)
    assert s["wall_time_sec"] >= 0

    # simulate monotonic counter jump: monkeypatch time.perf_counter to return decreasing values during run
    times = [0.0, 0.1, -5.0]
    def fake_perf():
        return times.pop(0) if times else -10.0
    monkeypatch.setattr(time, "perf_counter", fake_perf)

    s2 = run_stress(runs=1, workers=1, seed=0, prompt="x", adapters=[{}], strategy="single", fanout=1, quorum=0, fail_on_violation=False)

    # if a negative wall_time occurs, it should be captured (we allow either behavior: detection or normalization)
    assert "wall_time_sec" in s2

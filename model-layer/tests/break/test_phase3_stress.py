from tools.breaker.stress_runner import run_stress


def test_phase3_small_stress():
    # small smoke test for CI: 50 runs, 4 workers, deterministic seed
    summary = run_stress(runs=50, workers=4, seed=0, prompt="smoke", adapters=[{"adapter_id": "a0", "capabilities": {}}], strategy="single", fanout=1, quorum=0, fail_on_violation=True)
    assert summary["ok"]
    assert summary["failure_count"] == 0
    assert len(summary["unique_trace_hashes"]) == 1

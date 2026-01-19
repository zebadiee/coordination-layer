# Phase 10 — Time Skew & Monotonicity

Summary
-------
Tests and governance for time-based adversarial attacks (clock skew, rollback, and monotonicity violations). The goal is to ensure determinism is not influenced by wall-clock time and that the system detects and reports anomalous timing behavior.

Initial Test Coverage
---------------------
- `tools/breaker/phase10/test_time_skew.py`: unit tests that monkeypatch `time.time` and `time.perf_counter` and check `execute_envelope` invariants and stress_runner telemetry monotonicity.

Governance
----------
- Tag findings with `phase10-time-drift-drift` for observed anomalies.
- Record remediation steps and tags in governance files.

# Phase 4 — Controlled Chaos (C12/C13 hardening)

Purpose
- Validate resilience of the deterministic orchestrator (C12) and executor (C13) under adversarial conditions.

Scope
- Fault injection targeted at the executor/orchestrator boundary only: timeouts, step failures, partial network-like drops (simulated), envelope tampering, and quorum degradation.
- Local and CI smoke only; no production traffic or live node changes.

Acceptance criteria
- Determinism preserved for unaffected runs (single trace hash for identical seed/runs).
- No silent fail-throughs: tampering detection must be explicit (rejected) and quorum decisions must reflect timeouts/failures deterministically.
- Canary (1,000 runs, seed=0) completes with zero invariant violations for the baseline scenario; all failures are recorded and analyzed.

Artifacts & telemetry
- Telemetry output for canaries will be placed under `governance/telemetry/` with clear names like `C13_phase4_canary_v1.json`.
- Reports summarizing unique trace hashes, failure counts, wall_time_sec, and peak RSS placed under `governance/` and `docs/`.

Initial suite (minimal, copyable)
- Envelope tamper detection (mismatched SHA-256 envelope_id must raise ValueError).
- Step timeout simulation (simulate_duration_ms > timeout_ms) and quorum result behavior.
- Payload mismatch/quorum resolution deterministic checks.

Runbook (quickstart)
1. Run unit-level fault injection tests locally:
   $ pytest -q model-layer/tests/break/test_phase4_fault_injection.py

2. Run canary stress (1000 runs):
   $ python3 tools/breaker/stress_runner.py --runs 1000 --workers 8 --seed 0 --output governance/telemetry/C13_phase4_canary_v1.json

3. Collect and publish the report.

Next actions (this PR)
- Add CI gated smoke job that runs a small canary (e.g., 100 runs) on merges to `main`.
- Expand fault injection tests to include adapter failure modes and quorum degradation scenarios.

Owners
- Lead: @zebadiee
- SRE: TBD

Notes
- This phase must be purely simulated and deterministic; avoid any live adapter orchestration or hardware-specific tests in CI.

# Phase 5 Breakability Matrix

Purpose
-------
Define the classes of experiments, acceptance/exit criteria, and measurement policies for Phase 5 (controlled breakability).

Test Categories (one at a time)
-------------------------------
1. Dependency failures
   - Missing optional modules
   - Partial installs
   - Simulated pip / package resolution failures

2. Timing & Ordering
   - Artificial delays in orchestration requests
   - Out-of-order event delivery
   - Network partition simulations (local)

3. Invalid Inputs
   - Malformed execution envelopes
   - Partial schemas / missing fields
   - Unexpected field types

4. Environment Stress
   - No virtualenv / different Python versions
   - Minimal runner images (alpine, old libc)
   - Resource constraints (CPU, memory)

Metrics & Observables
---------------------
- **Graceful failure:** Did the system fail-safe without cascading effects?
- **Error clarity:** Were error messages actionable and localized?
- **Containment:** Did the failure remain isolated to the experiment scope?
- **Telemetry:** All runs must produce telemetry with `ok` boolean, failure counters, and `unique_trace_hashes` where applicable.

Exit Criteria (for marking an experiment valid)
----------------------------------------------
- The experiment has clear, reproducible failure modes documented.
- No authoritative invariant (C13, phase4-smoke) is broken.
- Observed failures meet the defined acceptable failure range.
- Post-experiment remediation plan documented (if needed).

Severity Levels and Actions
---------------------------
- **Informational:** No service impact; document and move on.
- **Manageable:** Requires minor remediation; schedule follow-up.
- **Critical:** Violates invariants; abort phase and create a hotfix/policy change.

Experiment Process
------------------
1. Create a `phase5/*` branch with a clear description.
2. Add a small workflow (or use `ci/phase5-breakability.yml`) that triggers only on that branch.
3. Run experiment with telemetry enabled and artifact upload.
4. Review logs and telemetry; apply exit criteria.
5. If criteria met, merge into `phase5-breakability` and tag accordingly.

Recording Results
-----------------
- Place telemetry files in `governance/telemetry/`.
- Record run IDs and artifact SHA256 in `governance/PHASE5_LOG.md` with a short summary.


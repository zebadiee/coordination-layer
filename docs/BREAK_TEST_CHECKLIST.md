# Break-Test Checklist (Phases 1–4)

This checklist codifies the break-testing plan for C6–C13. Run each item and mark outcome.

Phase 1 — Lock the Baseline
- [ ] Tag baseline commit: `pre-break` (immutable snapshot)
- [ ] Single golden path: Prompt → Planner → Orchestrator → Executor run 10× identical

Phase 2 — Structural Break Tests
Invalid Execution Plans:
- [ ] Missing steps → reject
- [ ] Cycles → reject
- [ ] Impossible quorum → reject
- [ ] Conflicting timeouts → reject
- [ ] Empty node sets → reject

Adversarial Planner Inputs:
- [ ] Extremely large fanout → accept or reject deterministically
- [ ] Mixed contradictory strategies → reject
- [ ] Edge-case seeds (0, max-int, negative) → deterministic or reject

Orchestrator Abuse:
- [ ] Node failure mid-envelope → deterministic state
- [ ] Duplicate node IDs → reject or canonicalize deterministically
- [ ] Reordered execution steps → processed in order with correct outcome
- [ ] Delayed responses → timeouts honored

Phase 3 — Execution Stress (Safe Mode)
- [ ] Deterministic payload bombing (parallel runs)
- [ ] Measure determinism, latency, memory, failure classification

Phase 4 — Controlled Chaos
- [ ] Force quorum mismatch and verify detection
- [ ] Fake node reports and ensure detection
- [ ] Alter payload hashes and ensure rejects or detection
- [ ] Replay envelopes and ensure idempotency or detection

Acceptance criteria
- Deterministic failures with classified reasons
- No undefined behavior or hidden state
- Reproducible inputs and artifact logs for all failures

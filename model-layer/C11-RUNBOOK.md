# C11 Runbook — Execution Planning Strategies

Purpose
- Document operational guidance for the Execution Planner (C11). This runbook describes acceptance, testing, and manual verification steps for planning strategies (single, fanout, verify, quorum).

Scope
- Control-plane only: no execution, no network calls, no persistence, and no model interaction.
- Deterministic plan construction from validated prompts and adapter descriptors.

Quick checks (pre-merge)
- Unit tests: `make test-c11` passes locally (tests cover single, fanout, verify, determinism).
- CI: `c11-tests` job runs and is green on the PR branch.
- No runtime imports of models or adapter-side effects.

Acceptance tests
- Determinism: identical inputs produce bit-identical plans.
- Strategy coverage: tests for single, fanout, verify, quorum.
- Edge cases: no adapters (reject), insufficient adapters for strategy (reject with deterministic message).

Manual verification
- Use the `planner.build_execution_plan` with example inputs and adapters to inspect `_explain` content.
- Confirm `explain.human_rationale(plan)` returns a short human-friendly explanation.

Rollback guidance
- No runtime change required; if a planner bug is discovered, revert PR and publish a follow-up with the new C-number when behaviour changes are required.

Notes
- This runbook is intentionally short: C11 is conservative and exists to make downstream C12 simpler and safer.

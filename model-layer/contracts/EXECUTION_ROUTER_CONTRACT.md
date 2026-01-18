EXECUTION ROUTER CONTRACT — C9

Purpose
- Define a strict, testable contract for the Execution Router (C9): a control-plane layer that decides where validated prompts (from C8) should execute. C9 must produce an execution plan (strategy + node list + constraints) and must not run models or touch coordination-layer state.

Responsibilities (allowed)
- Ingest C8-validated prompt metadata and node capability summaries (C7 output).
- Produce an execution plan: strategy, nodes, timeout, merge policy, and constraints.
- Enforce deterministic constraints and policy (e.g., reject system prompts routed externally per C8 policy).
- Provide auditable decision metadata (request_hash, decision_hash) without persisting raw prompts.

Forbidden actions
- No model loading or inference.
- No persistence of raw prompts or raw responses.
- No modification of `coordination-v1/` or coordination behavior.
- No implicit identity enforcement or external auth decisions.

Execution Plan (example JSON)
- strategy: single | fanout | verify | fallback
- nodes: list of node identifiers (e.g., ["hades","atlas"]).
- timeout_ms: integer
- merge_policy: first_success | vote | rank
- constraints: {deterministic: boolean, max_parallel: integer}

Deterministic invariants
- If request metadata requests deterministic: true, router must set deterministic constraint and avoid strategies that break determinism (e.g., uncontrolled voting without tie-break rules).

Failure modes (explicit)
- `invalid_input` — input schema failure
- `no_eligible_nodes` — no node meets constraints
- `unsupported_strategy` — strategy not recognized
- `policy_refusal` — policy disallows planned execution

Auditing
- Router must compute `decision_hash` (SHA256 over canonical plan) and return it in the response; raw prompt is not persisted.

Governance
- Changes to this contract require PR + governance sign-off. The router is a control-plane arbitrator and must be conservative.

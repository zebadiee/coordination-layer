# C12 — Execution Orchestrator Contract (Draft)

Status: Draft (pre-freeze)
Layer: Model-Layer → Execution Boundary (orchestration only)
Depends on: C9 (Execution Plan), C10 (Adapter Descriptor), C11 (Planner)

Purpose
- Produce a deterministic, auditable execution envelope from a validated execution plan and adapter descriptors.
- The orchestrator is a dry-run: it does not execute anything.

Inputs
- A validated `execution_plan` (C9 schema)
- Adapter descriptors (C10)
- Planner output (C11) — optional strategy hints
- Resource constraints and policy hints

Output: execution_envelope.json
- `orchestrator_version`: string
- `execution_id`: deterministic id (sha256 over canonical inputs)
- `strategy`: mirrors plan.strategy
- `steps`: ordered list of steps {step, adapter, node, mode: "dry-run", timeout_ms}
- `guarantees`: {deterministic: true, no_persistence: true, no_execution: true}
- `_explain`: deterministic rationale for step ordering and selections

Invariants
- Determinism: identical inputs produce bit-identical envelopes
- No network calls, no side-effects
- Nodes assigned must be present in adapters
- Envelope only describes what would be executed

Repo placement
- `model-layer/orchestrator/CONTRACT.md` (this file)
- `model-layer/orchestrator/orchestrator.py` (pure functions)
- `model-layer/orchestrator/schemas/execution_envelope.json`
- `model-layer/tests/unit/test_orchestrator_*.py`
- `model-layer/.make_c12`, `.github/workflows/c12-tests.yml`

Acceptance criteria
- Unit tests check deterministic outputs, rejection behavior, and explainability
- CI job `c12-tests` added
- Runbook and governance checklist drafted before freeze

Notes
- This is the last control-plane layer before execution. Keep it conservative and test-first.

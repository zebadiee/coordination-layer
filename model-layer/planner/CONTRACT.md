# C11 — Execution Planning Strategies (Draft)

Status: Draft (pre-freeze)
Layer: Model-Layer → Execution Boundary (planning only)
Depends on: C8 (Prompt Contract), C9 (Execution Router Contract), C10 (Adapter Descriptor)

## Purpose & Boundary

C11 defines deterministic planning strategies that map a validated request and a set of adapters
into an execution plan (an `execution_plan.json` instance as defined by C9). This is control-plane
only: no execution, no network calls, no persistence, and no model loading.

Allowed
- Strategy selection (single, fanout, verify, quorum)
- Deterministic plan construction
- Capability matching (adapter descriptors only)
- Simple static cost/latency heuristics
- Explainable plans (human-readable rationale)

Forbidden
- Any execution or network calls
- Mutating coordination or adapters
- Persisting raw prompts or plans

## Strategies (v1)
- `single`: choose a single adapter/node (lowest latency candidate)
- `fanout`: replicate to N adapters
- `verify`: primary + verifier (deterministic pairing)
- `quorum`: odd N, majority declared (no voting here)

## Determinism rules
- Strategy choice must be reproducible from:
  - request hash (canonical JSON representation)
  - adapter descriptors
  - static policy
- Node ordering is stable (lexicographic adapter_id)
- Tie-breaks use request-hash modulo deterministic methods

## Acceptance criteria
- Given identical inputs → bit-identical execution plan
- Invalid adapter capabilities → deterministic rejection
- Strategy selection explainable via `explain()`
- Unit tests for all strategies and determinism

## Repo placement
```
model-layer/
  planner/
    CONTRACT.md
    planner.py
    strategies.py
    explain.py
  tests/unit/
    test_planner_single.py
    test_planner_fanout.py
    test_planner_verify.py
    test_determinism.py
  .make_c11
  .github/workflows/c11-tests.yml
```

Notes
- This contract intentionally leaves merging/verification and execution to later components (C12+).
- All plan outputs must conform to `model-layer/contracts/schemas/execution_plan.json` (C9 schema).

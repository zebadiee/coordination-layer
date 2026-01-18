# C10 — Execution Adapter Interface Contract (Draft)

Status: Draft (pre-freeze)
Layer: Model-Layer → Execution Boundary
Depends on: C8 (Prompt Contract), C9 (Execution Router Contract)
Does NOT depend on: Coordination semantics, GPUs, model binaries

## 1. Purpose & Boundary

Define a strict, testable interface between the model-layer control plane (C8/C9) and any future execution backend (CPU, GPU, remote, mock, etc.).
Adapters are pluggable executors — not decision makers.

Adapter responsibilities (allowed)
- Declare capabilities (what it can execute).
- Accept a validated execution plan.
- Perform execution attempt (future versions only).
- Return structured execution results or failures.
- Enforce adapter-local limits (timeouts, memory ceilings).

Explicitly forbidden
- Routing or strategy decisions (belongs to C9).
- Loading models implicitly.
- Persisting raw prompts or raw outputs.
- Mutating coordination or governance state.
- Performing retries, voting, or quorum logic.

## 2. Adapter Lifecycle

Adapters follow a pure functional lifecycle:

```
discover() → describe() → prepare(plan) → execute(plan) → teardown()
```

Only `discover()` and `describe()` are allowed in C10.

| Method    | Allowed | Notes                          |
|-----------|---------|--------------------------------|
| discover()| ✅      | Static availability & health   |
| describe()| ✅      | Capabilities + limits          |
| prepare() | ❌      | Future                         |
| execute() | ❌      | Future                         |
| teardown()| ❌      | Future                         |

## 3. Adapter Identity & Capabilities

Adapter Descriptor (required output)

```json
{
  "adapter_id": "string (unique, stable)",
  "adapter_version": "semver string",
  "backend_type": "cpu|gpu|remote|mock",
  "vendor": "string",
  "capabilities": {
    "max_tokens": 4096,
    "deterministic": true,
    "supported_prompt_types": ["task", "verification"],
    "supported_strategies": ["single", "fanout"],
    "concurrency": 1
  },
  "limits": {
    "timeout_ms_max": 30000,
    "memory_mb_max": 8192
  }
}
```

**Invariants**
- Capabilities must be static for adapter lifetime.
- Capabilities are declarative, not aspirational.
- Any plan exceeding declared limits must be rejected.

## 4. Execution Adapter Contract (Interface)

Conceptual interface:

```py
class ExecutionAdapter:
    def discover(self) -> AdapterHealth: ...
    def describe(self) -> AdapterDescriptor: ...
```

No side effects allowed.

## 5. Execution Plan Acceptance (Read-Only)

Adapters receive an already-validated execution plan (C9).

An adapter must reject a plan if:
- strategy not supported
- plan exceeds adapter limits
- determinism requested but unsupported
- timeout exceeds adapter maximum

Rejection response (standardized):

```json
{
  "status": "rejected",
  "code": "unsupported_strategy|limit_exceeded|determinism_unsupported",
  "reason": "short deterministic explanation"
}
```

## 6. Adapter Health & Discovery

Health schema:

```json
{
  "status": "ok|degraded|unavailable",
  "details": {"latency_ms": 12, "last_error": null}
}
```

Rules:
- No probing workloads.
- No GPU allocation in C10.
- Health must be fast (<100ms).

## 7. Error Taxonomy (Adapter-Scoped)

- `adapter_unavailable` — Backend unreachable
- `unsupported_strategy` — Strategy mismatch
- `limit_exceeded` — Plan violates limits
- `determinism_unsupported` — Deterministic requested
- `internal_error` — Adapter bug

All errors must be deterministic, single-line, and non-leaking.

## 8. Repo Placement (Proposed)

```
model-layer/
  adapters/
    CONTRACT.md
    schemas/
      adapter_descriptor.json
      adapter_health.json
    README.md
  tests/
    unit/
      test_adapter_descriptor.py
      test_adapter_rejection.py
```

No executable adapter code in C10.

## 9. Acceptance Criteria (for C10 freeze)
- Adapter descriptor schema exists and validates.
- Unit tests: reject unsupported strategies, reject limit violations, accept valid plans (no execution).
- No execution code present and no model imports.
- Governance sign-off recorded.

## 10. Explicit Non-Goals
- No batching, retries, multi-adapter orchestration, speculative execution, or inference.

## 11. Next Steps
1. Convert into `model-layer/adapters/CONTRACT.md` (this file).
2. Add JSON schemas + unit tests.
3. Open PR `model-layer/c10-adapters` and request governance review.
4. Freeze as `model-layer-adapter-contract-v1` after sign-off.

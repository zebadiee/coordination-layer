# Phase 7 — Runtime & Environment Fault Injection Plan

Purpose
-------
Validate system behavior under realistic runtime/environment faults (containers, missing deps, minimal images, mixed Python runtimes). Ensure failures are explicit, deterministic where possible, and do not lead to silent corruption.

Scope
-----
- Missing package availability
- Minimal runtime images (alpine, slim)
- Older Python runtimes (3.9)
- Missing venv conventions
- Resource-constrained scenarios (CI-level)

Test strategy
-------------
- Add a Phase 7 workflow that runs on `phase7/**` branches and supports manual dispatch.
- Combine matrix runs of Python versions and a lightweight Docker-based Alpine run.
- Tests live in `tools/breaker/phase7/` and are designed to:
  - Simulate missing dependencies by clearing `PYTHONPATH` or running in a fresh container
  - Assert that failures are non-silent (non-zero exit code and explicit errors)

Acceptance criteria
-------------------
- Failed runs must show predictable failure modes (ModuleNotFoundError, ValueError, MemoryError)
- No silent acceptance of missing resilience (e.g., tests should not pass incorrectly)
- All Phase 7 experiments run on dedicated branches and are allowed to fail without blocking `main`

Governance
----------
- Tag findings as `phase7-<short-desc>-drift` for expected failures and `phase7-<short-desc>-stable` when hardened.
- Record all Phase 7 results in `governance/Phase_4_to_6_Validation_Log.md` or a new Phase 7 log as appropriate.

Finding: `stress_runner.py` imported `model_layer` at module import time and therefore did not fail when `PYTHONPATH` was cleared in an environment where `model_layer` was installed system-wide. This masked an operational boundary.

Resolution: `stress_runner.py` now performs an explicit runtime dependency check and exits with a clear error message when `model_layer` is not importable. This enforces fail-fast behavior and makes the Phase 7 tests meaningful across environments.

Status: Fix implemented and testable; tag: `phase7-runtime-dependency-stable` planned upon validation.

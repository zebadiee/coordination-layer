# Phase 9 — Resource Starvation & Scheduler Abuse

Summary
-------
This plan outlines tests and governance for resource starvation experiments: memory, CPU, and process/thread limits. All tests are isolated to `phase9/*` branches and must not block `main`.

Initial Tests Added
-------------------
- `tools/breaker/phase9/test_resource_starvation.py`: RLIMIT-based memory/CPU/process limits and a containerized memory quota smoke.

Governance Actions
------------------
- Findings must be tagged and logged with the `phase9-` prefix.
- All Phase 9 experiments should be documented and recorded in the governance directory with run IDs and artifact hashes.

Status: Plan created; tests and workflow scaffold to be added on branch `phase9/resource-starvation`.

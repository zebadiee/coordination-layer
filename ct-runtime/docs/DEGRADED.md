# DEGRADED Readiness Pattern (MAD-OS)

Status: canonical, read-only documentation of the DEGRADED pattern established in the codebase.

Purpose
- Capture the minimal, conservative semantics for the `DEGRADED` readiness state so future contributors do not accidentally expand authority or behavior.

Readiness states
- HALT
  - Meaning: CT does not permit the node to perform MAD-OS behaviour.
  - Effect: MAD-OS must not start any authoritative or mutating behavior.
- DEGRADED
  - Meaning: CT indicates the node may provide limited, non-authoritative utility.
  - Effect: MAD-OS may run read-only, non-authoritative features (telemetry, queue consumers, read-only dashboards), but must never mutate state, promote the node, or perform authority actions.
- READY
  - Meaning: CT authoritatively allows full MAD-OS operation.
  - Effect: Full features available.

Rules (must be followed)
1. MAD-OS never writes readiness files (read-only adapter only).
2. MAD-OS never promotes DEGRADED -> READY (only CT/authority may change readiness).
3. Feature gate pattern: one gate per feature, single decision point (readiness_state()).
4. Tests: every gated feature must have a three-case unit test (READY, DEGRADED, HALT).
5. Systemd and boot logic remain unchanged; gating is implemented at MAD-OS feature level, not at boot or CT.

Pattern (how to implement features)
1. Add an adapter/helper that returns normalized readiness: `readiness_adapter.readiness_state()` → one of `HALT|DEGRADED|READY`.
2. Implement feature run logic as:

```py
state = readiness_adapter.readiness_state()
if state == 'READY':
    start_full()
elif state == 'DEGRADED':
    start_limited()
else:
    # HALT: do nothing
    pass
```

3. Feature implementations must be read-only in DEGRADED mode and testable via monkeypatching `readiness_adapter.readiness_state`.

Tests
- Add one unit test per feature that asserts behavior for the three readiness states.
- Keep tests fast, isolated, and deterministic (no systemd calls).

Operational notes
- CT is the source of truth for readiness status. Any plan to have CT emit `DEGRADED` should be accompanied by an explicit, conservative ruleset and tests.
- HUD and CLI should only *display* readiness info (no policy changes on display).

Next steps (recommended)
1. Pause and copy this file into release notes / governance docs.
2. When ready, add conservative `DEGRADED` emission rules in CT (separate change, tested, and reviewed).
3. Incrementally add more DEGRADED-only features (one at a time) following the pattern.

Acceptance
- This document is intentionally short and prescriptive. Add detail only when a real need is found (avoid over-specifying edge cases prematurely).

---

Document created: 2026-01-22 (automated note)

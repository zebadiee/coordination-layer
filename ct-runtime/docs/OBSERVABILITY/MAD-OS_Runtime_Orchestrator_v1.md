# MAD-OS Runtime Orchestrator v1 — sealed

MAD-OS Runtime Orchestrator v1 sealed. This release formalizes a small, declarative, read-only runtime orchestrator that activates runtime components based on the canonical readiness state (READY | DEGRADED | HALT). Version 1 includes the following DEGRADED-safe components: `telemetry` (limited mode) and `queue_consumer` (limited/read-only mode). The orchestrator is observable via the HUD and `madctl runtime status --json`, and is protected by unit, component, and integration tests.

This is a freeze: no changes to the orchestrator subsystem will be made without explicit governance and corresponding tests. Future work (service lifecycle, scheduling, HUD controls) should be undertaken only after this milestone has been reviewed and unblocked by maintainers.

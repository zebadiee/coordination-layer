# MAD-OS Lifecycle v1 — sealed

MAD-OS Lifecycle v1 is sealed. This release documents the Phase 1 lifecycle primitives for runtime components: `start`, `stop`, `restart`, and `status`. The implementation is intentionally small, idempotent, and non-authoritative; state persistence is atomic and test-scoped. Visibility is provided via the `madctl` CLI and the HUD (read-only). Tests include unit coverage for idempotence and integration tests for CLI start/stop/status flows.

This is a freeze: further changes to lifecycle semantics (supervision, automated restarts, or policy escalation) must be proposed and reviewed with accompanying tests.

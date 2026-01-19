# Phase 5 Branch Policy

Purpose
-------
Provide a controlled, auditable place for destructive / breakability experiments (Phase 5) without contaminating `main` or authoritative checks.

Branch Naming
------------
- Primary branch: `phase5-breakability`
- Experimental branches: `phase5/*` (example: `phase5/dep-failure-2026-01-19`)

Policy Rules
------------
- **No destructive tests or experiments should land on `main`.**
- `phase5-breakability` is the canonical Phase 5 branch (merge point for validated experiments).
- All experimental work should be developed on child `phase5/*` branches and merged into `phase5-breakability` only after passing Phase 5 criteria.

Protection & Required Checks
----------------------------
- Protect `main` with required checks: **`c13-tests`**, **`phase4-smoke`**.
- Mark `C7` and `C8` workflows as informational (non-required). Do not require them on `main`.
- `phase5-breakability` may have looser protections (allow force-push for controlled experiments) but retain audit logging and require at least one maintainer approval before merging into `phase5-breakability`.

Merge & Release Rules
---------------------
- No automatic merges from `phase5-breakability` into `main`.
- A Phase 5 experiment becomes authoritative only when it has a `phase5-validated` tag created after documented exit criteria are met.
- Tagging format: `phase5-validated-v<MAJOR>` (e.g., `phase5-validated-v1`). Tagging must reference the run IDs and artifact hashes that proved the experiment.

Governance
----------
- Owners: repository maintainers and listed approvers (CODEOWNERS can be used for this purpose).
- All Phase 5 experiments must include:
  - a brief description of intent
  - test plan and risk assessment
  - exit criteria (see `phase5_breakability_matrix.md`)
  - telemetry artifact references

Auditability
------------
- Store Phase 5 telemetry artifacts in `governance/telemetry/` with a standard naming convention:
  `C13_phase5_<short-desc>_<runid>.json` and include SHA256 of artifact in governance notes.
- Append a governance entry recording tag, commit SHA, run IDs, artifact hashes, and a short summary in `governance/RELEASES.md` or a dedicated `governance/PHASE5_LOG.md` for long-term record.

Notes
-----
- This policy intentionally preserves `main` as conservative and authoritative while enabling rapid, isolated experimentation in Phase 5.
- Follow the breakability matrix before expanding experiments.

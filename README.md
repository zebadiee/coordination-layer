coordination-layer — coordination infra (frozen v1) and upstack work

Purpose
- Host the frozen coordination layer snapshot (coordination-v1/) as immutable infrastructure and provide an isolated workspace for semantic upgrades (coord-v2/).

Repository layout
- coordination-v1/  — Imported snapshot (read-only by policy). Contains manifest, checksums, and C1–C5 PASS notes.
- coord-v2/         — C6 work and later: design, prototypes, and contract for `/coord/v2`.
- GOVERNANCE.md    — Rules that keep `coordination-v1` immutable.
- docs/            — Rationale, links to artifacts, and design notes.

Policy
- Do NOT modify files under `coordination-v1/`. Treat it as a sealed artifact. All development and commits must occur in branches and directories outside `coordination-v1/`.

Contact
- Governance owner: TBD
- Epic / issue: C6 — Semantic Upgrade

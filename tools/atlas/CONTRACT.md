Atlas CONTRACT — write-side constraints

Purpose
-------
Small, auditable helper scripts and templates for appending authoritative records to the ATLAS Obsidian vault.

Rules
-----
- Only append operations are allowed. No replace or delete.
- Writes must be done from a trusted node (Hermes) or via an authenticated operator.
- All writes must include an ISO timestamp and actor metadata.
- Scripts must be idempotent for dry-run and must not create arbitrary directories outside the vault mount.

Usage
-----
- `tools/atlas/write_topology.py --vault /mnt/atlas-vault --actor hermes --action "note"` will append a topology entry.

Audit
-----
- Every append must also emit an audit line to the local audit log (if configured) and to Hermes for cross-checking.

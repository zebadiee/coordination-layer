# Topology truth record — ATLAS

## {{iso_timestamp}} — Storage & Role Topology

- **ATLAS**
  - Role: Memory spine
  - Storage: 2TB internal + 10TB LaCie
  - Owns: Obsidian vault (authoritative)

- **HERMES**
  - Role: Authority / governance
  - Storage: 4TB NVMe
  - Owns: CT authority plane, allowlists, audits
  - Access: RW to Obsidian via ATLAS

- **HADES**
  - Role: Compute / worker
  - Storage: 1TB
  - Owns: Nothing authoritative
  - Access: RO to Obsidian via ATLAS

**Invariant:** Authority ≠ Memory ≠ Compute.

---

Notes:
- Mount point: /mnt/atlas-vault (example)
- Vault path: /mnt/lacie-10tb/obsidian-vault
- Owner & ACLs: governed by operations

Actions taken: `{{action_summary}}`

Signed-off-by: {{actor}}

---

(append only)

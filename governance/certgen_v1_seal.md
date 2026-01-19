# CERTGEN v1 — Governance Seal

Status: SEALED

Scope:
- Deterministic certificate generation (JSON + Markdown)
- Inputs: RULES output (+ optional REVIEW audit)
- No LLM usage
- No rule mutation
- No outcome mutation

Dependencies:
- rules-v1-sealed
- llm-cli-audit-sealed (optional)
- review CLI (non-authoritative)

Guarantees:
- Idempotent output for identical inputs
- Append-only audit usage
- Environment-independent formatting

Approved for operational use.

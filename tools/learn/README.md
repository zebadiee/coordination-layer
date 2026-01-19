# Learning CLI (tools/learn)

This small CLI runs a controlled learning loop for a specified script. It is intentionally conservative and enforces safety rules:

- Retrieval is whitelist-only and supports local `file://` URIs for v0.
- The extractor prompt is fixed and read-only.
- Validation is deterministic and data-driven.
- Promotion is gated and produces proposal artifacts only.

Subcommands:
- fetch --script <script> --out <evidence.json>
- extract --evidence <evidence.json> --out <extracted.json>
- validate --extracted <extracted.json> --out <validated.json>
- promote --validated <validated.json> --target rules|prompts --reviewer <name> --outdir <dir>
- run --script <script> --outdir <rundir> [--dry-run]

This is designed for humans-in-the-loop learning; no automatic edits are performed.

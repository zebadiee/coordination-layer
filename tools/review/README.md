# Sherlock Review CLI (tools/review)

A minimal human-in-the-loop (HIL) review CLI for TACQO outputs.

Features:
- Read TACQO JSON from a file or stdin
- Accept or reject observations (non-authoritative)
- Append decisions to the audit log (env REVIEW_AUDIT_PATH overrides default)
- Meant to be removable without affecting other modules

Usage examples:
- Non-interactive:
  ./tools/review/review.py --input tacqo/final.json --decision accept --comment "OK"

- Interactive:
  ./tools/review/review.py --input tacqo/final.json

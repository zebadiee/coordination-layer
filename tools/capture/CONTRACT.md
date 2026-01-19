# CAPTURE v1 — Correction Capture Contract

Purpose: collect human corrections and suggested fixes produced during REVIEW so they can be converted into training artefacts or rule/prompt improvements.

Storage:
- Append-only JSON Lines file: `captures/captures.log`

Capture entry fields:
- `ts` (ISO8601 string)
- `capture_id` (opaque id)
- `document_id` (optional)
- `prompt_hash` (optional)
- `actor` (who captured the correction)
- `source` (review-extract|manual|other)
- `suggested_fix` (string) — required

APIs / Tools:
- `tools/capture/add_capture.py` — append a capture via CLI or stdin JSON
- `tools/capture/extract_from_audit.py` — scan the audit log and convert review rejects / correction: comments into captures

Guidelines:
- Prefer capturing fixes as soon as discovered (recommended via `--capture` flow in review)
- Captures are NOT authoritative; they are training data drafts or rule suggestions.
- Captures should be reviewed by a maintainer before being converted into RULES or prompt updates.

Coord-v2 CONTRACT — Parsing + Echo (summary)

See `C6-CONTRACT-FULL.md` for the full, canonical contract (exact request/response schemas, canonicalization rules, invariants, acceptance tests, and governance checklist).

Summary
- Stateless parsing endpoint that returns `server_nonce` (fresh) and `hash` (canonicalized SHA-256) for valid requests.
- Rejects malformed JSON, unsupported media types, and oversized payloads.
- Must not persist raw payloads or maintain shared state. No auth, no leader logic, no retry orchestration.

Acceptance criteria
- See `C6-CONTRACT-FULL.md` for exact unit, integration, and governance tests required for C6 PASS.

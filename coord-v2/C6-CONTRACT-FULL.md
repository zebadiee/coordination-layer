C6 — coord-v2 Full Contract (draft)

Purpose
- Define the exact, testable contract for `/coord/v2` (C6): a stateless semantic endpoint that parses requests and returns a nonce and deterministic hash echo without creating shared state.

High-level rules (immutable constraints)
- Stateless: No persistence, no shared state, no durable side-effects.
- No authority: No auth, no identity enforcement, no leader or consensus logic.
- No retries, no retry orchestration and no retry amplification behaviors.
- Minimal surface: Do not modify or call `/coord` (coordination-v1 remains sealed and read-only).

Transport
- Protocols: HTTP/1.1 or HTTP/2 over TLS recommended; service MUST accept `application/json` requests and return `application/json` responses.
- Content-Type validation: Requests with non-JSON content should be rejected with 415.
- Max payload size: 64 KiB. Larger requests must return 413 Payload Too Large.

Request schema (application/json)
- Top-level object fields (all-names are case-sensitive):
  - `version` (string; REQUIRED) — protocol version identifier (e.g., "coord-v2-1").
  - `client_nonce` (string; OPTIONAL) — opaque client-supplied nonce. If present, server MUST echo it back in `echo.client_nonce`.
  - `payload` (object | string; OPTIONAL) — application payload. Server MUST NOT interpret application-level semantics beyond syntactic validation.
  - `meta` (object; OPTIONAL) — arbitrary flat key/value pairs (values must be strings or numbers). Nested objects are permitted but should be shallow (depth ≤ 2).

Validation rules
- `version` must be present and equal to the server-accepted version string (server responds 412 Precondition Failed otherwise with `reason`).
- `client_nonce` if present must be a printable UTF-8 string ≤ 256 bytes.
- `payload` and `meta` are syntactically validated for JSON well-formedness only; semantic validation beyond this is the responsibility of higher layers.

Canonicalization for hashing
- To produce a deterministic hash, the server must canonicalize the request by:
  1. Parsing JSON and removing any fields not in the top-level schema (`version`, `client_nonce`, `payload`, `meta`).
  2. Serializing keys in lexicographic order.
  3. Using UTF-8 without extra whitespace.
  4. Applying JSON canonicalization (RFC 8785 style minimal canonical form) and computing SHA-256 over the canonical bytes.

Response schema (application/json)
- Success (HTTP 200 OK):
{
  "status": "ok",
  "server_nonce": "<base64url, 22-24 chars>",
  "hash": "<hex-sha256-of-canonicalized-request>",
  "echo": {
    "client_nonce": "<client nonce if supplied>"
  }
}

- Rejection (HTTP 4xx):
{
  "status": "rejected",
  "reason": "<human-readable single-line reason string>",
  "code": "<machine_code>"
}

Machine codes (non-exhaustive)
- `invalid_version` — `version` mismatch
- `malformed_json` — invalid JSON
- `payload_too_large` — payload > 64KiB
- `unsupported_media_type` — non-JSON Content-Type

Operational invariants (must hold for all implementations)
- Statelessness: The endpoint MUST NOT write files, databases, or persistent logs that store request payloads. Short-lived in-memory buffers are allowed but must not grow unbounded per-client.
- Observability-only metrics: Request counters and latency histograms are allowed. No counters may be used to maintain client state or drive behavior that alters responses.
- No identity enforcement: Any `sender` or `client_*` fields are informational and MAY be echoed but MUST NOT be used to gate or change semantics (no ACLs, no access control decisions based on these fields).
- Time independence: Do not rely on client-provided timestamps or local clocks to change semantics. If used, clocks must be validated but not used for control decisions.
- Safe defaults: On ambiguous input, prefer `rejected` with a clear reason rather than guessing.

Privacy & Security
- Do NOT persist request payloads. If audit logging is required, logs must redact or hash payload content; raw payloads must not be written to disk.
- Rate limiting is permitted as an implementation detail (in-memory or per-process) but must be documented and not relied upon for correctness.
- Return minimal error detail to clients; avoid leaking internal state or stack traces.

Acceptance Criteria — C6 PASS
1. Behavior tests (unit):
   - Accepts valid `application/json` with required `version` and returns `status: ok` plus `server_nonce` and `hash`.
   - Rejects malformed JSON (HTTP 400) with `code=malformed_json`.
   - Rejects large payload (HTTP 413) with `code=payload_too_large`.
   - Rejects unsupported media types with HTTP 415 and `code=unsupported_media_type`.
   - Echoes `client_nonce` when supplied.
   - Deterministic `hash` produced for identical inputs.
2. Integration tests:
   - Repeated requests do not create files or database entries (assert no filesystem changes under a working directory during test run).
   - Observability metrics exist (request count, success/failure counts, latency histogram) and do not include raw payload storage.
   - Load test: basic stress (e.g., 100 req/s for a minute) without memory growth or state leakage.
3. Security/Privacy:
   - No raw payloads are written to disk during tests.
   - Error responses do not leak internal data.
4. Governance:
   - PR template includes a checkbox verifying `coordination-v1/` was not modified.
   - A governance reviewer (owner) must sign off before merging.

Minimal test matrix (examples)
- Unit: parse-valid.json → expect 200 and canonical hash matches reference
- Unit: malformed.json → expect 400 malformed_json
- Unit: oversized.json → expect 413 payload_too_large
- Integration: repeated.json x1000 → expect no file system changes, stable memory

Developer notes
- Nonce format: recommend base64url 16 bytes random (server_nonce). Avoid predictable nonces.
- Hash format: hex-encoded SHA-256 of canonicalized request.
- Implementation may provide an option to return only `hash` and `status` (to save bandwidth); that is acceptable if agreed in tests and documented.

Change policy for coord-v2 work
- coord-v2 is an evolving workstream; changes to the contract MUST be small, documented, and approved with governance sign-off. Each change must include updated acceptance tests and backward-compatibility notes.

Appendix: Example request & response
- Request
{
  "version": "coord-v2-1",
  "client_nonce": "abc123",
  "payload": {"x": 1},
  "meta": {"env": "test"}
}

- Response (200)
{
  "status": "ok",
  "server_nonce": "Z3VhcmRzLXdpc2U",
  "hash": "e3b0c44298fc1c149afbf4c8996fb924...",
  "echo": {"client_nonce": "abc123"}
}

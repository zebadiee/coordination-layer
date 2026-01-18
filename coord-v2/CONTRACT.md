Coord-v2 CONTRACT — Parsing + Echo (draft)

Purpose
- Define the minimal semantic contract for `/coord/v2` used in C6: parse payload, verify allowed fields, and return a stable nonce/hash echo without maintaining shared state.

Allowed behavior
- Parse JSON or application/x-www-form-urlencoded payloads.
- Validate syntactic correctness and reject malformed requests with 4xx responses.
- Return a JSON response including:
  - `nonce`: server-generated opaque nonce (UUID or base64) or a hash derived deterministically from allowed inputs
  - `status`: `ok` or `rejected`
  - `reason`: on rejected requests

Prohibited behavior
- No persistent writes or shared state across requests.
- No retry orchestration or client-scoped backoff enforcement.
- No implicit coupling to `/coord` (the frozen endpoint remains untouched).

Acceptance criteria
- Unit tests for parsing, rejection rules, and nonce format.
- Integration test asserting absence of side-effects after repeated requests.
- Performance check: minimal latency under baseline load.

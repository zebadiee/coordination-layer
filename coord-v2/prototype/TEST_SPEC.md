Test spec — coord-v2 (C6)

Unit tests
- test_valid_request: send valid request, assert 200, `status==ok`, `server_nonce` present, `hash` matches expected canonical hash.
- test_malformed_json: send invalid JSON, assert 400 and code `malformed_json`.
- test_unsupported_media_type: send text/plain, assert 415 and code `unsupported_media_type`.
- test_payload_too_large: send >64KiB JSON, assert 413 and code `payload_too_large`.
- test_echo_client_nonce: send client_nonce and confirm echoed in response.
- test_hash_determinism: identical requests produce identical `hash` values.

Integration tests
- test_no_persistence: hit endpoint multiple times and verify there are no new files under a temporary working directory and no persistent logs of raw payloads.
- test_stable_memory_under_load: run small load test (100 rps × 60s) and assert memory does not grow beyond a reasonable bound (e.g., <50MB increase).

Security tests
- test_error_leakage: ensure error responses do not contain stack traces or internal data.

Notes
- Use pytest for unit tests, and a simple load runner (wrk or python-based) for integration load test.
- Tests must run in CI with ephemeral environment and clean workspace.

Prototype plan — minimal coord-v2 handler

Goal
- Implement the smallest possible handler that satisfies the C6 contract: parse request, canonicalize, compute sha256 hash, return server_nonce and hash; do not persist anything.

Files to add
- `coord_v2/app.py` — minimal Flask/FastAPI handler (`/coord/v2`) with JSON validation.
- `coord_v2/tests/test_contract.py` — unit tests for parsing, rejection, and hash correctness.
- `coord_v2/Makefile` — targets: test, lint

Runtime constraints
- Keep dependencies minimal (prefer standard library + lightweight microframework: Flask or FastAPI + uvicorn for dev).
- No DB or filesystem writes in the prototype.

Acceptance
- All tests pass locally in CI.
- Memory usage remains stable under a small load test (100 req/s for 60s).

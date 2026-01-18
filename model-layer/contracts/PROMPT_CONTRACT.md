PROMPT CONTRACT — model-layer (v1)

Overview

This document records the canonical prompt execution contract for C8. It is binding: operator-controlled system prompts are rejected when submitted externally (policy: system prompts are operator-only).

Key rules (summary)
- Input validation follows `contracts/schemas/input.json`.
- Output validation follows `contracts/schemas/output.json`.
- System prompts submitted externally must be rejected with `code=policy_refusal`.
- No raw prompt or raw output persistence; only hashed audit is recorded.
- Deterministic mode (`params.deterministic=true`) mandates `params.seed` be present; adapters must honor it when possible.

Request lifecycle
1. Receive JSON request
2. Validate against input schema
3. Enforce policy: if `prompt_type==system` and submission is external -> reject (`policy_refusal`)
4. Canonicalize and compute `request_hash` (SHA-256 on canonical JSON)
5. Return structured rejection or a `status: ok` with `audit.request_hash` and `schema_version` set to `model-layer-v1`.

Refusal codes
- `policy_refusal` — prompt rejected due to policy (e.g., external system prompt)
- `invalid_prompt` — schema validation error
- `payload_too_large` — body over 64KiB
- `unsupported_type` — unknown prompt_type

Change control
- Any change to this contract requires a PR and governance sign-off.

Recorded decision
- System prompt external submission: **REJECT** (operator-only). This is the canonical choice for C8.

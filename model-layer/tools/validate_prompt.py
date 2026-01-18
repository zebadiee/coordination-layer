"""Lightweight validator enforcing C8 prompt contract rules.
This module does NOT call any model or backend. It only validates and enforces
policy decisions (e.g., external system prompt rejection).
"""
import jsonschema
import json
import hashlib
from pathlib import Path

SCHEMA_DIR = Path(__file__).resolve().parents[1] / 'contracts' / 'schemas'
INPUT_SCHEMA = json.loads((SCHEMA_DIR / 'input.json').read_text())
OUTPUT_SCHEMA = json.loads((SCHEMA_DIR / 'output.json').read_text())

MAX_PAYLOAD_BYTES = 64 * 1024

class ValidationError(Exception):
    def __init__(self, code, reason):
        self.code = code
        self.reason = reason
        super().__init__(f"{code}: {reason}")


def compute_request_hash(obj: dict) -> str:
    canonical = json.dumps(obj, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def validate_input(obj: dict, payload_bytes: int = None, external_submission: bool = True) -> dict:
    """Validate input against schema and enforce policy.

    Returns audit info dict on success.
    Raises ValidationError on rejection.
    """
    # Size check
    if payload_bytes is not None and payload_bytes > MAX_PAYLOAD_BYTES:
        raise ValidationError('payload_too_large', 'payload exceeds 64KiB')

    # Schema validation
    try:
        jsonschema.validate(instance=obj, schema=INPUT_SCHEMA)
    except jsonschema.ValidationError as e:
        raise ValidationError('invalid_prompt', str(e))

    # Enforce system prompt policy: external submissions rejected
    if external_submission and obj.get('prompt_type') == 'system':
        raise ValidationError('policy_refusal', 'system prompts are operator-only')

    # If deterministic requested, seed must be present
    params = obj.get('params', {}) or {}
    if params.get('deterministic') and 'seed' not in params:
        raise ValidationError('invalid_prompt', 'deterministic true requires an explicit seed')

    # Compute request hash
    request_hash = compute_request_hash({k: obj[k] for k in sorted(obj.keys())})
    return {'request_hash': request_hash, 'schema_version': 'model-layer-v1'}


# Small helper to produce standardized rejection output
def rejection_response(code: str, reason: str) -> dict:
    return {'status': 'rejected', 'code': code, 'reason': reason}


if __name__ == '__main__':
    import sys
    raw = sys.stdin.read()
    try:
        obj = json.loads(raw)
    except Exception:
        print(json.dumps(rejection_response('malformed_json', 'malformed json')))
        sys.exit(1)
    try:
        audit = validate_input(obj, payload_bytes=len(raw.encode('utf-8')))
        print(json.dumps({'status': 'ok', 'audit': audit}))
    except ValidationError as e:
        print(json.dumps(rejection_response(e.code, e.reason)))
        sys.exit(2)

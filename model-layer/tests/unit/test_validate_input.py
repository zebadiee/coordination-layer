import json
from model_layer.tools.validate_prompt import validate_input, ValidationError


def test_valid_input_ok():
    obj = {"version": "model-layer-v1", "prompt_type": "task", "prompt": "Do X", "params": {"deterministic": False}}
    audit = validate_input(obj, payload_bytes=len(str(obj).encode('utf-8')))
    assert 'request_hash' in audit
    assert audit['schema_version'] == 'model-layer-v1'


def test_payload_too_large():
    obj = {"version": "model-layer-v1", "prompt_type": "task", "prompt": "x"}
    try:
        validate_input(obj, payload_bytes=64*1024 + 1)
        assert False, "expected ValidationError"
    except ValidationError as e:
        assert e.code == 'payload_too_large'


def test_system_prompt_is_rejected_externally():
    obj = {"version": "model-layer-v1", "prompt_type": "system", "prompt": "do admin"}
    try:
        validate_input(obj, payload_bytes=len(str(obj).encode('utf-8')), external_submission=True)
        assert False, "expected ValidationError"
    except ValidationError as e:
        assert e.code == 'policy_refusal'


def test_deterministic_requires_seed():
    obj = {"version": "model-layer-v1", "prompt_type": "task", "prompt": "x", "params": {"deterministic": True}}
    try:
        validate_input(obj, payload_bytes=len(str(obj).encode('utf-8')))
        assert False
    except ValidationError as e:
        assert e.code == 'invalid_prompt'

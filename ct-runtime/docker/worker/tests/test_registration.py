def test_payload_shape():
    payload = {
        "agent_id": "worker-01",
        "role": "worker",
        "capabilities": ["execute_task"],
        "code_hash": "abc",
        "ts": 0,
    }
    assert "agent_id" in payload
    assert payload["role"] == "worker"

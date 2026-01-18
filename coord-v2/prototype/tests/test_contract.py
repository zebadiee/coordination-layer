import os
import json
import hashlib
from fastapi.testclient import TestClient
from coord_v2.app import app, _canonicalize_request, SERVER_VERSION

client = TestClient(app)


def canonical_hash(obj):
    return hashlib.sha256(_canonicalize_request(obj)).hexdigest()


def test_valid_request():
    body = {"version": SERVER_VERSION, "client_nonce": "abc123", "payload": {"x": 1}, "meta": {"env": "test"}}
    r = client.post("/coord/v2", json=body)
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "ok"
    assert "server_nonce" in j and isinstance(j["server_nonce"], str)
    assert "hash" in j and j["hash"] == canonical_hash(body)
    assert j["echo"]["client_nonce"] == "abc123"


def test_malformed_json():
    # invalid JSON body
    r = client.post("/coord/v2", data='{"version": "coord-v2-1", ', headers={"content-type": "application/json"})
    assert r.status_code == 400
    j = r.json()
    assert j["code"] == "malformed_json"


def test_unsupported_media_type():
    r = client.post("/coord/v2", data="hello", headers={"content-type": "text/plain"})
    assert r.status_code == 415
    j = r.json()
    assert j["code"] == "unsupported_media_type"


def test_payload_too_large():
    big = {"version": SERVER_VERSION, "payload": "x" * (64 * 1024 + 1)}
    r = client.post("/coord/v2", json=big)
    assert r.status_code == 413
    j = r.json()
    assert j["code"] == "payload_too_large"


def test_hash_determinism():
    body = {"version": SERVER_VERSION, "payload": {"a": 1, "b": 2}}
    r1 = client.post("/coord/v2", json=body)
    r2 = client.post("/coord/v2", json=body)
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["hash"] == r2.json()["hash"]


def test_no_persistence(tmp_path):
    # ensure that handling requests does not create files under cwd
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    before = set(os.listdir(cwd))

    # run requests with working directory changed
    old = os.getcwd()
    try:
        os.chdir(str(cwd))
        for _ in range(10):
            r = client.post("/coord/v2", json={"version": SERVER_VERSION, "payload": {"x": 1}})
            assert r.status_code == 200
    finally:
        os.chdir(old)

    after = set(os.listdir(cwd))
    assert before == after

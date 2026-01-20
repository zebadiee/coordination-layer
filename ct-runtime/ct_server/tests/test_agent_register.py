import json
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
import os
import tempfile

from ct_runtime.ct_server import agent_register as ar


def start_server(port, allowlist_path, audit_path, accepted_path):
    # Point module-level paths at temp files
    ar.ALLOWLIST_PATH = allowlist_path
    ar.AUDIT_PATH = audit_path
    ar.ACCEPTED_PATH = accepted_path
    ar.ROLES = ar.load_allowlist(allowlist_path)
    ar.LAST.clear()
    srv = ar.run_server(port=port, host="127.0.0.1")
    return srv


def post_payload(port, payload):
    url = f"http://127.0.0.1:{port}/agent/register"
    r = requests.post(url, json=payload, timeout=2)
    return r.json()


def test_happy_path(tmp_path):
    port = 9781
    allow = tmp_path / "allow.json"
    audit = tmp_path / "audit.log"
    accepted = tmp_path / "accepted.jsonl"
    # copy default allowlist
    default_allow = json.loads(open(os.path.join(os.path.dirname(ar.__file__), "allowlist.json")).read())
    allow.write_text(json.dumps(default_allow))

    srv = start_server(port, str(allow), str(audit), str(accepted))
    payload = {
        "agent_id": "observer-01",
        "role": "observer",
        "capabilities": ["read_logs"],
        "code_hash": "a" * 64,
        "ts": int(time.time()),
    }
    resp = post_payload(port, payload)
    assert resp.get("status") == "ACCEPTED"
    srv.shutdown()


def test_capability_overreach(tmp_path):
    port = 9782
    allow = tmp_path / "allow.json"
    audit = tmp_path / "audit.log"
    accepted = tmp_path / "accepted.jsonl"
    default_allow = json.loads(open(os.path.join(os.path.dirname(ar.__file__), "allowlist.json")).read())
    allow.write_text(json.dumps(default_allow))

    srv = start_server(port, str(allow), str(audit), str(accepted))
    payload = {
        "agent_id": "bad-1",
        "role": "observer",
        "capabilities": ["read_logs", "write"],
        "code_hash": "b" * 64,
        "ts": int(time.time()),
    }
    resp = post_payload(port, payload)
    assert resp.get("status") == "DENIED"
    assert resp.get("reason") == "capability_overreach"
    srv.shutdown()


def test_unknown_role(tmp_path):
    port = 9783
    allow = tmp_path / "allow.json"
    audit = tmp_path / "audit.log"
    accepted = tmp_path / "accepted.jsonl"
    default_allow = json.loads(open(os.path.join(os.path.dirname(ar.__file__), "allowlist.json")).read())
    allow.write_text(json.dumps(default_allow))

    srv = start_server(port, str(allow), str(audit), str(accepted))
    payload = {
        "agent_id": "unk-1",
        "role": "mystery",
        "capabilities": [],
        "code_hash": "c" * 64,
        "ts": int(time.time()),
    }
    resp = post_payload(port, payload)
    assert resp.get("status") == "DENIED"
    assert resp.get("reason") == "unknown_role"
    srv.shutdown()


def test_hash_mismatch_and_replay(tmp_path):
    port = 9784
    allow = tmp_path / "allow.json"
    audit = tmp_path / "audit.log"
    accepted = tmp_path / "accepted.jsonl"
    default_allow = json.loads(open(os.path.join(os.path.dirname(ar.__file__), "allowlist.json")).read())
    allow.write_text(json.dumps(default_allow))

    srv = start_server(port, str(allow), str(audit), str(accepted))

    ts1 = int(time.time())
    payload1 = {
        "agent_id": "observer-01",
        "role": "observer",
        "capabilities": ["read_logs"],
        "code_hash": "d" * 64,
        "ts": ts1,
    }
    resp1 = post_payload(port, payload1)
    assert resp1.get("status") == "ACCEPTED"

    # Replay same timestamp -> denied
    resp_replay = post_payload(port, payload1)
    assert resp_replay.get("status") == "DENIED"
    assert resp_replay.get("reason") == "replay_or_stale"

    # New timestamp but different hash -> denied
    payload2 = payload1.copy()
    payload2["ts"] = ts1 + 10
    payload2["code_hash"] = "e" * 64
    resp2 = post_payload(port, payload2)
    assert resp2.get("status") == "DENIED"
    assert resp2.get("reason") == "hash_mismatch"

    srv.shutdown()


def test_stale_timestamp(tmp_path):
    port = 9785
    allow = tmp_path / "allow.json"
    audit = tmp_path / "audit.log"
    accepted = tmp_path / "accepted.jsonl"
    default_allow = json.loads(open(os.path.join(os.path.dirname(ar.__file__), "allowlist.json")).read())
    allow.write_text(json.dumps(default_allow))

    srv = start_server(port, str(allow), str(audit), str(accepted))
    payload = {
        "agent_id": "obs-old",
        "role": "observer",
        "capabilities": ["read_logs"],
        "code_hash": "f" * 64,
        "ts": int(time.time()) - 10000,
    }
    resp = post_payload(port, payload)
    assert resp.get("status") == "DENIED"
    assert resp.get("reason") == "stale_timestamp"
    srv.shutdown()

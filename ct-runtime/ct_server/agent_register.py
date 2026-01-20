#!/usr/bin/env python3
"""Simple CT agent registration endpoint.

POST /agent/register
Payload JSON: {agent_id, role, capabilities, code_hash, ts}
Responds with JSON {status: ACCEPTED|DENIED, reason?: str}

Audit trail written to `registrations.log` and accepted registrations to `accepted.jsonl`.
"""

import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread

ALLOWLIST_PATH = os.environ.get("ALLOWLIST_PATH", os.path.join(os.path.dirname(__file__), "allowlist.json"))
AUDIT_PATH = os.environ.get("REGISTRATIONS_AUDIT", os.path.join(os.path.dirname(__file__), "registrations.log"))
ACCEPTED_PATH = os.environ.get("ACCEPTED_REGISTRATIONS", os.path.join(os.path.dirname(__file__), "accepted.jsonl"))
MAX_DRIFT = None


def load_allowlist(path=ALLOWLIST_PATH):
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    global MAX_DRIFT
    MAX_DRIFT = int(data.get("max_time_drift_seconds", 300))
    return data.get("roles", {})


ROLES = load_allowlist()

# In-memory record of last ts and code_hash for agents (also recorded in files)
LAST = {}


def audit_record(payload, remote_addr, accepted, reason=None):
    entry = {
        "ts": time.time(),
        "remote": remote_addr,
        "payload": payload,
        "accepted": accepted,
        "reason": reason,
    }
    os.makedirs(os.path.dirname(AUDIT_PATH), exist_ok=True)
    with open(AUDIT_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, separators=(",", ":")) + "\n")


def record_accepted(payload):
    os.makedirs(os.path.dirname(ACCEPTED_PATH), exist_ok=True)
    with open(ACCEPTED_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, separators=(",", ":")) + "\n")


def validate_payload(payload):
    # Required fields
    required = {"agent_id", "role", "capabilities", "code_hash", "ts"}
    if not required.issubset(set(payload.keys())):
        return False, "missing_fields"

    agent_id = payload["agent_id"]
    role = payload["role"]
    capabilities = payload["capabilities"]
    code_hash = payload["code_hash"]
    ts = payload["ts"]

    # Types
    if not isinstance(agent_id, str) or not isinstance(role, str):
        return False, "invalid_types"
    if not isinstance(capabilities, list) or not all(isinstance(c, str) for c in capabilities):
        return False, "invalid_capabilities"
    if not isinstance(code_hash, str) or len(code_hash) != 64:
        return False, "invalid_code_hash"
    if not isinstance(ts, int):
        return False, "invalid_timestamp"

    # Role known
    if role not in ROLES:
        return False, "unknown_role"

    # Capability escalation
    allowed_caps = set(ROLES[role].get("capabilities", []))
    if not set(capabilities).issubset(allowed_caps):
        return False, "capability_overreach"

    # Timestamp validation
    now = int(time.time())
    if ts < now - MAX_DRIFT:
        return False, "stale_timestamp"
    if ts > now + MAX_DRIFT:
        return False, "future_timestamp"

    # Replay or hash mismatch
    prev = LAST.get(agent_id)
    if prev:
        prev_ts = prev.get("ts")
        prev_hash = prev.get("code_hash")
        if ts <= prev_ts:
            return False, "replay_or_stale"
        if prev_hash != code_hash:
            return False, "hash_mismatch"

    return True, None


class RegisterHandler(BaseHTTPRequestHandler):
    def _reply(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_POST(self):
        if self.path != "/agent/register":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", "0"))
        try:
            raw = self.rfile.read(length)
            payload = json.loads(raw.decode())
        except Exception:
            self._reply({"status": "DENIED", "reason": "invalid_json"})
            return

        ok, reason = validate_payload(payload)
        remote = self.client_address[0] if self.client_address else None
        if not ok:
            audit_record(payload, remote, False, reason)
            self._reply({"status": "DENIED", "reason": reason})
            return

        # Accept: persist and update LAST
        LAST[payload["agent_id"]] = {"ts": payload["ts"], "code_hash": payload["code_hash"]}
        record_accepted({"ts": time.time(), "agent_id": payload["agent_id"], "role": payload["role"], "code_hash": payload["code_hash"]})
        audit_record(payload, remote, True)
        self._reply({"status": "ACCEPTED"})

    def log_message(self, *_):
        return


def run_server(port=7778, host="127.0.0.1"):
    srv = HTTPServer((host, port), RegisterHandler)
    t = Thread(target=srv.serve_forever, daemon=True)
    t.start()
    print(f"CT agent register listening on {host}:{port}")
    return srv


if __name__ == "__main__":
    run_server()
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass

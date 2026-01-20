#!/usr/bin/env python3
import hashlib
import json
import os
import sys
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import requests
import yaml

CT_HANDSHAKE_URL = os.getenv("CT_HANDSHAKE_URL", "")
AGENT_YAML_PATH = os.getenv("AGENT_YAML_PATH", "/app/agent.yaml")
HEALTH_PORT = int(os.getenv("HEALTH_PORT", "8080"))
TIMEOUT = float(os.getenv("CT_TIMEOUT", "5.0"))


def log(msg):
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    print(f"[{ts}] observer: {msg}", flush=True)


def compute_code_hash(root="/app"):
    h = hashlib.sha256()
    for p in sorted(Path(root).rglob("*")):
        if p.is_file() and p.suffix in {".py", ".yaml"}:
            with open(p, "rb") as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    h.update(chunk)
    return h.hexdigest()


def read_agent_yaml(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def register(payload):
    if not CT_HANDSHAKE_URL:
        log("CT_HANDSHAKE_URL not set; denying self.")
        return {"status": "DENIED", "reason": "missing_handshake_url"}
    try:
        r = requests.post(
            CT_HANDSHAKE_URL,
            json=payload,
            timeout=TIMEOUT,
            headers={"Content-Type": "application/json"},
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log(f"handshake error: {e}")
        return {"status": "DENIED", "reason": "handshake_error"}


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, *_):
        return


def start_health():
    srv = HTTPServer(("", HEALTH_PORT), HealthHandler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    log(f"health endpoint on :{HEALTH_PORT}")


def main():
    cfg = read_agent_yaml(AGENT_YAML_PATH)
    code_hash = compute_code_hash("/app")

    payload = {
        "agent_id": cfg.get("agent_id"),
        "role": cfg.get("role"),
        "capabilities": cfg.get("capabilities", []),
        "code_hash": code_hash,
        "ts": int(time.time()),
    }

    log("starting registration")
    resp = register(payload)
    status = resp.get("status", "DENIED")

    if status != "ACCEPTED":
        log(f"registration denied: {resp}")
        start_health()
        while True:
            time.sleep(60)

    log("registration accepted")
    start_health()

    # Observer is passive: log-only loop
    while True:
        time.sleep(30)
        log("alive")


if __name__ == "__main__":
    main()

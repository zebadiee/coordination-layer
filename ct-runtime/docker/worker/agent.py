#!/usr/bin/env python3
import hashlib
import json
import os
import sys
import time
import yaml
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer

AGENT_YAML_PATH = os.environ.get("AGENT_YAML_PATH", "agent.yaml")
CT_HANDSHAKE_URL = os.environ.get("CT_HANDSHAKE_URL")
HEALTH_PORT = int(os.environ.get("HEALTH_PORT", "8090"))


def load_agent_config(path):
    with open(path, "r") as f:
        return yaml.safe_load(f)


def compute_code_hash():
    h = hashlib.sha256()
    with open(__file__, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def register_agent(cfg):
    payload = {
        "agent_id": cfg["agent_id"],
        "role": cfg["role"],
        "capabilities": cfg.get("capabilities", []),
        "code_hash": compute_code_hash(),
        "ts": int(time.time()),
    }
    r = requests.post(CT_HANDSHAKE_URL, json=payload, timeout=5)
    r.raise_for_status()
    return r.json()


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
        else:
            self.send_response(404)
            self.end_headers()


def serve_health():
    server = HTTPServer(("0.0.0.0", HEALTH_PORT), HealthHandler)
    server.serve_forever()


def main():
    if not CT_HANDSHAKE_URL:
        print("CT_HANDSHAKE_URL not set", file=sys.stderr)
        sys.exit(1)

    cfg = load_agent_config(AGENT_YAML_PATH)
    resp = register_agent(cfg)

    if resp.get("status") != "ACCEPTED":
        print("Registration denied; exiting")
        sys.exit(0)

    print("Worker registered and idle")
    serve_health()


if __name__ == "__main__":
    main()

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import subprocess
import sys
import time

from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent

class MockHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        data = json.loads(body.decode())
        assert "agent_id" in data
        assert "role" in data
        assert "capabilities" in data
        assert "code_hash" in data
        assert "ts" in data
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ACCEPTED"}).encode())
    def log_message(self, *_):
        return


def run_mock(port):
    srv = HTTPServer(("127.0.0.1", port), MockHandler)
    srv.serve_forever()


def test_registration_smoke(tmp_path):
    port = 8999
    t = threading.Thread(target=run_mock, args=(port,), daemon=True)
    t.start()
    time.sleep(0.5)

    env = {
        **dict(**{"CT_HANDSHAKE_URL": f"http://127.0.0.1:{port}"}),
        **dict(**{"HEALTH_PORT": "8090"}),
        **dict(**{"AGENT_YAML_PATH": str(ROOT / "agent.yaml")}),
    }
    p = subprocess.Popen(
        [sys.executable, str(ROOT / "agent.py")],
        cwd=str(ROOT),
        env={**env, **dict(**{"PYTHONUNBUFFERED": "1"})},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    time.sleep(2)
    p.terminate()
    out = p.stdout.read()
    assert "registration accepted" in out

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
import hashlib
import base64
import secrets

MAX_PAYLOAD = 64 * 1024
SERVER_VERSION = "coord-v2-1"

app = FastAPI()


def _canonicalize_request(obj: dict) -> bytes:
    # Keep only the canonical top-level fields in lexicographic order
    canonical = {}
    for k in sorted([k for k in ("version", "client_nonce", "payload", "meta") if k in obj]):
        canonical[k] = obj[k]
    # JSON canonicalization: separators without spaces, sorted keys already applied
    return json.dumps(canonical, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


@app.post("/coord/v2")
async def coord_v2(request: Request):
    content_type = (request.headers.get("content-type") or "").split(";")[0].strip()
    if content_type != "application/json":
        return JSONResponse(status_code=415, content={"status": "rejected", "reason": "unsupported media type", "code": "unsupported_media_type"})

    body = await request.body()
    if len(body) > MAX_PAYLOAD:
        return JSONResponse(status_code=413, content={"status": "rejected", "reason": "payload too large", "code": "payload_too_large"})

    try:
        obj = json.loads(body)
    except json.JSONDecodeError:
        return JSONResponse(status_code=400, content={"status": "rejected", "reason": "malformed json", "code": "malformed_json"})

    version = obj.get("version")
    if not isinstance(version, str) or version != SERVER_VERSION:
        return JSONResponse(status_code=412, content={"status": "rejected", "reason": "invalid version", "code": "invalid_version"})

    canonical = _canonicalize_request(obj)
    digest = hashlib.sha256(canonical).hexdigest()
    server_nonce = base64.urlsafe_b64encode(secrets.token_bytes(16)).rstrip(b"=").decode("ascii")

    echo = {}
    if "client_nonce" in obj:
        echo["client_nonce"] = obj.get("client_nonce")

    return {"status": "ok", "server_nonce": server_nonce, "hash": digest, "echo": echo}

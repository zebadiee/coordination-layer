#!/usr/bin/env python3
"""Add a capture entry (append-only) for human corrections/training data.

Usage:
  # simple CLI flags
  ./tools/capture/add_capture.py --document-id doc-1 --prompt-hash abcd --actor alice --suggested-fix "Rule R411.3.3 should be applied"

  # or via stdin JSON
  echo '{"document_id":"doc-1","prompt_hash":"abcd","actor":"alice","suggested_fix":"..."}' | ./tools/capture/add_capture.py

This appends one JSON object per line to `captures/captures.log`.
"""

import argparse
import json
import os
import sys
from datetime import datetime

CAPTURES_PATH = os.environ.get("CAPTURES_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "captures", "captures.log"))

os.makedirs(os.path.dirname(CAPTURES_PATH), exist_ok=True)


def load_input_from_stdin():
    raw = sys.stdin.read()
    if not raw.strip():
        return None
    try:
        return json.loads(raw)
    except Exception as e:
        print(json.dumps({"status":"error","message":f"failed to parse JSON from stdin: {e}"}), file=sys.stderr)
        sys.exit(2)


def main():
    ap = argparse.ArgumentParser(prog="add_capture")
    ap.add_argument("--document-id", help="Document ID (optional)")
    ap.add_argument("--prompt-hash", help="Prompt hash or identifier (optional)")
    ap.add_argument("--actor", help="Actor name (who captured)")
    ap.add_argument("--suggested-fix", help="Suggested fix / correction text")
    ap.add_argument("--source", help="Source tag (review|manual|extract)")
    args = ap.parse_args()

    data = load_input_from_stdin() or {}

    # Command-line flags override stdin
    if args.document_id:
        data["document_id"] = args.document_id
    if args.prompt_hash:
        data["prompt_hash"] = args.prompt_hash
    if args.actor:
        data["actor"] = args.actor
    if args.suggested_fix:
        data["suggested_fix"] = args.suggested_fix
    if args.source:
        data["source"] = args.source

    if "suggested_fix" not in data or not data.get("suggested_fix"):
        print(json.dumps({"status":"error","message":"suggested_fix is required"}), file=sys.stderr)
        sys.exit(3)

    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "capture_id": os.environ.get("CAPTURE_ID") or os.urandom(8).hex(),
        "document_id": data.get("document_id"),
        "prompt_hash": data.get("prompt_hash"),
        "actor": data.get("actor") or "unknown",
        "source": data.get("source") or "manual",
        "suggested_fix": data.get("suggested_fix"),
    }

    with open(CAPTURES_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, separators=(',', ':')) + "\n")

    print(json.dumps({"status":"ok","capture_id":entry["capture_id"]}))


if __name__ == "__main__":
    main()

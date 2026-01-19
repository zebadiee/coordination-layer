#!/usr/bin/env python3
"""Sherlock HIL review CLI (minimal, append-only decisions to audit log).

Usage:
  # Non-interactive (recommended for automation):
  ./tools/review/review.py --input tacqo/final.json --decision accept --comment "Looks good"

  # Interactive (simple prompts):
  ./tools/review/review.py --input tacqo/final.json

Behavior:
  - Reads TACQO JSON from --input or stdin
  - Records a decision entry (accept/reject/comment) to audit log (env REVIEW_AUDIT_PATH or llm-cli/audit.log)
  - Does not modify RULES or outcomes
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime

DEFAULT_AUDIT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "llm-cli", "audit.log")
AUDIT_PATH = os.environ.get("REVIEW_AUDIT_PATH", os.path.abspath(DEFAULT_AUDIT))


def write_audit(entry: dict):
    # Append-only, one JSON object per line
    with open(AUDIT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, separators=(",", ":")) + "\n")


def load_input(path):
    if path:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    else:
        return json.load(sys.stdin)


def main():
    ap = argparse.ArgumentParser(prog="review")
    ap.add_argument("--input", help="Path to TACQO JSON input (defaults to stdin)")
    ap.add_argument("--decision", choices=["accept", "reject"], help="Decision (accept|reject)")
    ap.add_argument("--comment", help="Optional comment")
    ap.add_argument("--actor", default="sherlock", help="Actor name to record")
    args = ap.parse_args()

    try:
        data = load_input(args.input)
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"failed to load input: {e}"}), file=sys.stderr)
        sys.exit(2)

    decision = args.decision
    comment = args.comment

    if not decision:
        # Interactive mode
        print("Observations:")
        for o in data.get("observations", []):
            desc = o.get("description", "<no description>")
            loc = o.get("location")
            print(f" - {desc}" + (f" ({loc})" if loc else ""))
        print()
        d = None
        while d not in ("accept", "reject"):
            d = input("Decision (accept/reject): ").strip().lower()
        decision = d
        if not comment:
            comment = input("Comment (optional): ").strip()

    # Construct audit entry
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "decision_id": str(uuid.uuid4()),
        "actor": args.actor,
        "decision": decision,
        "comment": comment or "",
    }

    # Optional references
    try:
        if isinstance(data.get("metadata", {}), dict):
            entry["document_type"] = data["metadata"].get("document_type")
            if "id" in data["metadata"]:
                entry["document_id"] = data["metadata"].get("id")
    except Exception:
        pass

    try:
        write_audit(entry)
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"failed to write audit: {e}"}), file=sys.stderr)
        sys.exit(3)

    print(json.dumps({"status": "ok", "decision": decision, "decision_id": entry["decision_id"]}))


if __name__ == "__main__":
    main()

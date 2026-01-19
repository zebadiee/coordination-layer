#!/usr/bin/env python3
"""Extract candidate captures from the audit log.

Rules:
 - Any review entry (from tools/review) with decision=="reject" becomes a capture
 - Any review entry with comment starting with `correction:` becomes a capture (remaining text is suggested_fix)

This writes to the captures log as produced by add_capture.py (append-only).
"""

import json
import os
import sys
from datetime import datetime

AUDIT_PATH = os.environ.get("LLM_AUDIT_PATH", os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "llm-cli", "audit.log"))
ADD_CAPTURE = os.path.join(os.path.dirname(__file__), "add_capture.py")


def iter_audit():
    try:
        with open(AUDIT_PATH, "r", encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    yield json.loads(ln)
                except Exception:
                    continue
    except FileNotFoundError:
        return


def main():
    for entry in iter_audit():
        # We're interested in review entries which have 'decision' and possibly 'comment'
        if entry.get("decision"):
            decision = entry.get("decision")
            comment = entry.get("comment", "") or ""
            doc = entry.get("document_id") or entry.get("document") or None
            actor = entry.get("actor") or entry.get("actor")

            if decision == "reject":
                suggested = comment or "Reviewer rejected — needs correction"
            elif comment.lower().strip().startswith("correction:"):
                suggested = comment.split("correction:", 1)[1].strip()
            else:
                continue

            # Build capture object and append via add_capture.py
            payload = {
                "document_id": doc,
                "prompt_hash": entry.get("prompt_hash"),
                "actor": actor or "reviewer",
                "suggested_fix": suggested,
                "source": "review-extract",
            }
            # call add_capture.py via subprocess (keeps modules decoupled)
            import subprocess
            p = subprocess.run([sys.executable, ADD_CAPTURE], input=json.dumps(payload), text=True, capture_output=True)
            if p.returncode != 0:
                print(f"failed to add capture for doc={doc}: {p.stderr}", file=sys.stderr)


if __name__ == "__main__":
    main()

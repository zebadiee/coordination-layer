#!/usr/bin/env python3
"""Propose a change artifact from validated claims (does NOT edit rules).

Writes a proposal JSON and a small human note for maintainers.
"""

import argparse
import json
import os
from datetime import datetime


def main():
    ap = argparse.ArgumentParser(prog="propose_change")
    ap.add_argument("--validated", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--reviewer", required=True)
    args = ap.parse_args()

    with open(args.validated, "r", encoding="utf-8") as fh:
        validated = json.load(fh)

    proposals = [v for v in validated if v.get("status") in ("confirmed", "needs_review")]

    os.makedirs(args.outdir, exist_ok=True)
    out_path = os.path.join(args.outdir, "proposal.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump({"reviewer": args.reviewer, "time": datetime.utcnow().isoformat() + "Z", "proposals": proposals}, fh, indent=2)

    note = os.path.join(args.outdir, "proposal_note.md")
    with open(note, "w", encoding="utf-8") as fh:
        fh.write(f"# Proposal by {args.reviewer} at {datetime.utcnow().isoformat()}\n\n")
        fh.write(f"Proposals: {len(proposals)}\n")

    print(json.dumps({"status": "ok", "proposal": out_path, "note": note}))


if __name__ == "__main__":
    main()

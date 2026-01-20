#!/usr/bin/env python3
"""Append a topology or note to an ATLAS vault topology file (append-only).

Usage:
  ./write_topology.py --vault /mnt/atlas-vault --actor hermes --action "Locked topology"

This writes a timestamped entry to SYSTEM/topology.md under the given vault path.
"""

import argparse
import os
from datetime import datetime


def append_topology(vault_path, actor, action):
    system_dir = os.path.join(vault_path, "SYSTEM")
    os.makedirs(system_dir, exist_ok=True)
    path = os.path.join(system_dir, "topology.md")
    ts = datetime.utcnow().isoformat() + "Z"
    entry = f"## {ts} — {action}\n\n- actor: {actor}\n\n"
    # Append-only
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(entry)
    print(path)


def main():
    ap = argparse.ArgumentParser(prog="write_topology")
    ap.add_argument("--vault", required=True, help="Mount point of ATLAS vault")
    ap.add_argument("--actor", required=True)
    ap.add_argument("--action", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.dry_run:
        print(f"DRY RUN: would append to {os.path.join(args.vault,'SYSTEM/topology.md')}")
        return

    append_topology(args.vault, args.actor, args.action)


if __name__ == "__main__":
    main()

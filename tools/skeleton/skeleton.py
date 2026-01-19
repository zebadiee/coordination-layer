#!/usr/bin/env python3
"""Skeleton v0: Non-interactive ASCII renderer for TACQO + RULES outputs.

Usage:
  ./tools/skeleton/skeleton.py --input tacqo/final.json
  cat tacqo/final.json | ./tools/skeleton/skeleton.py

It renders four fixed regions to stdout:
  - SYSTEM
  - INPUT
  - RULE MATCHES
  - OUTCOME

Designed for operator inspection, not machine parsing.
"""

import argparse
import json
import os
import shutil
import sys
from textwrap import fill

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
GOV_FILE = os.path.join(ROOT, "governance", "rules_v1_seal.md")
AUDIT_LOG = os.path.join(ROOT, "llm-cli", "audit.log")

BOX_WIDTH = 60


def render_box(title: str, lines, width=BOX_WIDTH):
    top = f"┌─ {title} {'─' * (width - len(title) - 6)}┐"
    bottom = "└" + "─" * (width - 2) + "┘"
    out = [top]
    for line in lines:
        # ensure we wrap long lines
        wrapped = fill(line, width - 4).splitlines() or [""]
        for w in wrapped:
            out.append(f"│ {w.ljust(width-4)} │")
    out.append(bottom)
    return "\n".join(out)


def detect_rules_version():
    if os.path.exists(GOV_FILE):
        try:
            with open(GOV_FILE, "r", encoding="utf-8") as fh:
                for ln in fh:
                    if ln.strip().startswith("Date:"):
                        date = ln.strip().split("Date:", 1)[1].strip()
                        return f"RULES v1 (sealed {date})"
        except Exception:
            pass
        return "RULES v1 (sealed)"
    return "RULES (unknown)"


def load_input(path):
    if path:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    else:
        return json.load(sys.stdin)


def main():
    ap = argparse.ArgumentParser(prog="skeleton")
    ap.add_argument("--input", help="Path to TACQO JSON (defaults to stdin)")
    ap.add_argument("--model", default="gemma:2b", help="Model label to show")
    args = ap.parse_args()

    try:
        data = load_input(args.input)
    except Exception as e:
        print(f"Failed to load input JSON: {e}", file=sys.stderr)
        sys.exit(2)

    # SYSTEM
    rules = detect_rules_version()
    audit_enabled = os.path.exists(AUDIT_LOG)
    term_width = shutil.get_terminal_size((80, 20)).columns
    width = min(BOX_WIDTH, max(40, term_width - 10))

    system_lines = [f"Model: {args.model}", f"Rules: {rules}", f"Audit: {'enabled' if audit_enabled else 'disabled'}"]
    system_box = render_box("SYSTEM", system_lines, width=width)

    # INPUT — show up to 3 observations
    obs = data.get("observations", [])
    if obs:
        input_lines = []
        for o in obs[:3]:
            desc = o.get("description") or "<no description>"
            loc = o.get("location")
            if loc:
                input_lines.append(f"{desc} — {loc}")
            else:
                input_lines.append(desc)
    else:
        input_lines = ["<no observations>"]
    input_box = render_box("INPUT", input_lines, width=width)

    # RULE MATCHES — list unique matches
    matches_lines = []
    seen = set()
    for o in obs:
        for m in o.get("regulation_matches", []):
            key = (m.get("regulation"), m.get("code"))
            if key not in seen:
                seen.add(key)
                matches_lines.append(f"{m.get('regulation')} → {m.get('code')}: {m.get('title')}")
    if not matches_lines:
        matches_lines = ["<no matches>"]
    matches_box = render_box("RULE MATCHES", matches_lines, width=width)

    # OUTCOME
    summary = data.get("summary", {})
    overall = summary.get("overall_result", "<unknown>")
    notes = summary.get("notes", "") or ""
    outcome_lines = [f"Overall: {overall}"]
    if notes:
        outcome_lines.append(notes)
    outcome_box = render_box("OUTCOME", outcome_lines, width=width)

    # Print in order
    print(system_box)
    print()
    print(input_box)
    print()
    print(matches_box)
    print()
    print(outcome_box)


if __name__ == "__main__":
    main()

# Skeleton v0 — Non-interactive CLI renderer

This tiny tool renders a fixed, operator-first layout from TACQO+RULES JSON output.

Usage:
  ./tools/skeleton/skeleton.py --input tacqo/final.json
  cat tacqo/final.json | ./tools/skeleton/skeleton.py

It prints four boxes to stdout: SYSTEM, INPUT, RULE MATCHES, OUTCOME.
It is intentionally non-interactive (no curses) and is meant for quick operator inspection.

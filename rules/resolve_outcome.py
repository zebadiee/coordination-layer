#!/usr/bin/env python3
import json
import sys

try:
    t = json.load(sys.stdin)
except Exception as e:
    print(json.dumps({"error": f"failed to read TACQO JSON from stdin: {e}"}), file=sys.stderr)
    sys.exit(2)

codes = {m["code"] for o in t.get("observations", []) for m in o.get("regulation_matches", [])}

if "C1" in codes or "C2" in codes:
    t.setdefault("summary", {})["overall_result"] = "UNSATISFACTORY"
else:
    t.setdefault("summary", {})["overall_result"] = "SATISFACTORY"

print(json.dumps(t, indent=2))

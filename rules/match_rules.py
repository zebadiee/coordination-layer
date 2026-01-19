#!/usr/bin/env python3
import json
import sys

RULES_PATH = "rules/bs7671/observations_v1.json"

try:
    rules = json.load(open(RULES_PATH))
    rules = rules.get("rules", [])
except Exception as e:
    print(json.dumps({"error": f"failed to load rules: {e}"}), file=sys.stderr)
    sys.exit(2)

try:
    tacqo = json.load(sys.stdin)
except Exception as e:
    print(json.dumps({"error": f"failed to read TACQO JSON from stdin: {e}"}), file=sys.stderr)
    sys.exit(3)

for obs in tacqo.get("observations", []):
    desc = (obs.get("description", "") or "").lower()
    matched = []

    for r in rules:
        if any(k in desc for k in r["applies_if"]):
            matched.append({
                "regulation": r["regulation"],
                "code": r["code"],
                "title": r["title"]
            })

    obs["regulation_matches"] = matched

print(json.dumps(tacqo, indent=2))

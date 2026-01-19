#!/usr/bin/env python3
"""CERTGEN v1 — deterministic certificate generator

Reads TACQO JSON (stdin or --input), optionally includes review decisions from an audit log,
and emits a certificate JSON and a human-readable Markdown certificate suitable for
inspection and archival.

Usage:
  ./certgen/generate.py --input tacqo/final.json --output-json cert.json --output-md cert.md
  cat tacqo/final.json | ./certgen/generate.py --output-json cert.json

Notes:
- This generator is deterministic and does not call any LLM.
- It does not modify input data or rules; it projects them into a certificate artifact.
"""

import argparse
import json
import os
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
DEFAULT_AUDIT = os.path.join(ROOT, "llm-cli", "audit.log")
GOV_FILE = os.path.join(ROOT, "governance", "rules_v1_seal.md")


def load_input(path):
    # Support '-' to mean stdin for CLI compatibility with tests
    if path and path != "-":
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    # read from stdin
    return json.load(sys.stdin)


def detect_rules_version():
    try:
        with open(GOV_FILE, "r", encoding="utf-8") as fh:
            for ln in fh:
                if ln.strip().startswith("Date:"):
                    date = ln.strip().split("Date:", 1)[1].strip()
                    return f"RULES v1 (sealed {date})"
    except Exception:
        pass
    return "RULES v1"


def read_audit(audit_path):
    entries = []
    try:
        with open(audit_path, "r", encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    entries.append(json.loads(ln))
                except Exception:
                    # ignore malformed lines
                    continue
    except FileNotFoundError:
        return []
    return entries


def build_certificate(tacqo, include_review=False, audit_path=None, generator="certgen v1"):
    cert = {}
    cert["metadata"] = tacqo.get("metadata", {}).copy()
    # ensure an id
    if "id" not in cert["metadata"]:
        cert["metadata"]["id"] = f"cert-{int(datetime.utcnow().timestamp())}"

    cert["generator"] = generator
    cert["rules_version"] = detect_rules_version()
    cert["generated_at"] = datetime.utcnow().isoformat() + "Z"

    # Installation: take from tacqo.installation if present
    cert["installation"] = tacqo.get("installation", {})

    # Observations: project regulation matches and keep provenance
    cert_obs = []
    for o in tacqo.get("observations", []):
        obs = {
            "description": o.get("description"),
            "location": o.get("location"),
            "codes": [m.get("code") for m in o.get("regulation_matches", []) if m.get("code")],
            "regulations": [m.get("regulation") for m in o.get("regulation_matches", []) if m.get("regulation")],
            "titles": [m.get("title") for m in o.get("regulation_matches", []) if m.get("title")],
        }
        cert_obs.append(obs)
    cert["observations"] = cert_obs

    # Test results and summary pass through
    cert["test_results"] = tacqo.get("test_results", {})
    cert["summary"] = tacqo.get("summary", {}).copy()

    # Optional review notes
    cert["reviews"] = []
    if include_review:
        audit_path = audit_path or DEFAULT_AUDIT
        entries = read_audit(audit_path)
        doc_id = cert["metadata"].get("id")
        for e in entries:
            # include decisions referencing this document id
            if e.get("document_id") and doc_id and e.get("document_id") == doc_id:
                cert["reviews"].append(e)

    return cert


def to_markdown(cert):
    md = []
    md.append(f"# Certificate — {cert['metadata'].get('id')}")
    md.append("")
    md.append(f"**Generated:** {cert.get('generated_at')}")
    md.append(f"**Rules:** {cert.get('rules_version')}")
    md.append("")
    md.append("## Installation")
    inst = cert.get("installation") or {}
    md.append(f"- Address: {inst.get('address', '')}")
    md.append(f"- Client: {inst.get('client', '')}")
    md.append("")
    md.append("## Observations")
    for i, o in enumerate(cert.get("observations", []), start=1):
        md.append(f"### {i}. {o.get('description')}")
        if o.get("location"):
            md.append(f"- Location: {o.get('location')}")
        if o.get("codes"):
            md.append(f"- Codes: {', '.join(o.get('codes'))}")
        if o.get("regulations"):
            md.append(f"- Regulations: {', '.join(o.get('regulations'))}")
        md.append("")

    md.append("## Summary")
    md.append(f"- Overall result: {cert.get('summary', {}).get('overall_result', '')}")
    if cert.get('summary', {}).get('notes'):
        md.append(f"- Notes: {cert.get('summary', {}).get('notes')}")
    md.append("")

    if cert.get("reviews"):
        md.append("## Reviews")
        for r in cert.get("reviews"):
            md.append(f"- {r.get('ts')} — {r.get('actor')} — {r.get('decision')} — {r.get('comment')}")
        md.append("")

    return "\n".join(md)


def main():
    ap = argparse.ArgumentParser(prog="certgen")
    ap.add_argument("--input", help="Path to TACQO JSON input (defaults to stdin)")
    ap.add_argument("--output-json", help="Path to write certificate JSON")
    ap.add_argument("--output-md", help="Path to write certificate Markdown")
    ap.add_argument("--include-review", action="store_true", help="Include review entries from audit log")
    ap.add_argument("--audit-path", help="Path to audit log (overrides default)")
    args = ap.parse_args()

    try:
        tacqo = load_input(args.input)
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"failed to load input: {e}"}), file=sys.stderr)
        sys.exit(2)

    cert = build_certificate(tacqo, include_review=args.include_review, audit_path=args.audit_path)

    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as fh:
            json.dump(cert, fh, indent=2)
    else:
        print(json.dumps(cert, indent=2))

    if args.output_md:
        with open(args.output_md, "w", encoding="utf-8") as fh:
            fh.write(to_markdown(cert))


if __name__ == "__main__":
    main()

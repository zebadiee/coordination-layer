#!/usr/bin/env python3
"""Learning CLI — run learning scripts: fetch, extract, validate, promote, run

Usage examples:
  tools/learn/run.py fetch --script tools/learn/scripts/learn_rcd_protection.yaml --out runs/rcd/evidence.json
  tools/learn/run.py extract --evidence runs/rcd/evidence.json --out runs/rcd/extracted.json
  tools/learn/run.py validate --extracted runs/rcd/extracted.json --out runs/rcd/validated.json
  tools/learn/run.py run --script tools/learn/scripts/learn_rcd_protection.yaml --outdir runs/rcd --dry-run
"""

import argparse
import json
import os
import sys
import shutil
from datetime import datetime
import subprocess
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

DEFAULT_EVIDENCE_DIR = "evidence"


def load_script(path):
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def fetch(script_path, out_path, whitelist=None):
    script = load_script(script_path)
    sources = script.get("sources", [])
    evidence = []

    for s in sources:
        url = s.get("url")
        # If url is present, check whitelist; if no url but content present, accept
        if url:
            if whitelist and not any(url.startswith(p) for p in whitelist):
                print(f"Skipping fetch (not whitelisted): {url}", file=sys.stderr)
                continue
            # For v0: support local `file://` URIs
            if url.startswith("file://"):
                p = url[len("file://"):]
                try:
                    excerpt = open(p, "r", encoding="utf-8").read()
                except Exception as e:
                    print(f"Failed to read {p}: {e}", file=sys.stderr)
                    continue
                evidence.append({"source": s.get("source"), "url": url, "excerpt": excerpt, "retrieved_at": datetime.utcnow().isoformat() + "Z"})
            else:
                # External fetch disabled in v0
                print(f"External fetch disabled in v0 for {url}", file=sys.stderr)
                continue
        elif s.get("content"):
            evidence.append({"source": s.get("source"), "url": None, "excerpt": s.get("content"), "retrieved_at": datetime.utcnow().isoformat() + "Z"})
        else:
            print("Source missing url and content — skipping", file=sys.stderr)
            continue

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(evidence, fh, indent=2)

    print(json.dumps({"status": "ok", "evidence_count": len(evidence)}))


def call_extractor(evidence_path, out_path, extractor_prompt_path=None):
    with open(evidence_path, "r", encoding="utf-8") as fh:
        evidence = json.load(fh)

    # Create a combined source text
    combined = "\n\n----\n\n".join([f"SOURCE: {e.get('source')}\n{e.get('excerpt')}" for e in evidence])

    # Read extractor prompt template
    if extractor_prompt_path and os.path.exists(extractor_prompt_path):
        with open(extractor_prompt_path, "r", encoding="utf-8") as fh:
            prompt_tpl = fh.read()
    else:
        prompt_tpl = "Extract explicit requirements and quoted regulation numbers. Output JSON list of claims with 'claim' and 'source'."

    prompt = prompt_tpl + "\n\nSource text:\n" + combined

    # Call llm-cli to extract (use inspector profile, json mode)
    proc = subprocess.run([sys.executable, os.path.join(ROOT, "llm-cli", "llm.py"), "--json", "--profile", "inspector"], input=json.dumps({"prompt": prompt}), text=True, capture_output=True)
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
        raise SystemExit(2)

    try:
        out = json.loads(proc.stdout)
    except Exception as e:
        print(f"Failed to parse extractor output: {e}", file=sys.stderr)
        raise

    # Expect response text contains JSON list; try to parse
    resp_text = out.get("response") or out.get("response_text") or ""
    try:
        claims = json.loads(resp_text)
    except Exception:
        # Fallback: wrap as single claim
        claims = [{"claim": resp_text, "source": [e.get('source') for e in evidence]}]

    # Normalize to a list
    if isinstance(claims, dict):
        claims = [claims]

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(claims, fh, indent=2)

    print(json.dumps({"status": "ok", "claims": len(claims)}))


def validate(extracted_path, out_path):
    # Dynamically import the validators module by path to avoid package import issues
    import importlib.util
    spec = importlib.util.spec_from_file_location("validators", os.path.join(os.path.dirname(__file__), "validate", "validators.py"))
    validators = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validators)

    with open(extracted_path, "r", encoding="utf-8") as fh:
        claims = json.load(fh)

    validated = []
    for c in claims:
        claim_text = c.get("claim") if isinstance(c, dict) else str(c)
        res = validators.simple_validate(claim_text)
        validated.append({"claim": claim_text, "status": res["status"], "reason": res.get("reason"), "sources": c.get("source")})

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(validated, fh, indent=2)

    print(json.dumps({"status": "ok", "validated": len(validated)}))


def promote(validated_path, target, reviewer, outdir):
    # Only generate proposal artifact and append to captures
    with open(validated_path, "r", encoding="utf-8") as fh:
        validated = json.load(fh)

    proposals = [v for v in validated if v.get("status") == "confirmed"]

    os.makedirs(outdir, exist_ok=True)
    prop_path = os.path.join(outdir, "proposals.json")
    with open(prop_path, "w", encoding="utf-8") as fh:
        json.dump({"reviewer": reviewer, "proposals": proposals}, fh, indent=2)

    # Append to captures log as suggestions
    from tools.capture.add_capture import CAPTURES_PATH
    import subprocess, json as _json
    for p in proposals:
        payload = {"document_id": None, "prompt_hash": None, "actor": reviewer, "suggested_fix": p.get("claim"), "source": "learn-promote"}
        subprocess.run([sys.executable, os.path.join(ROOT, "tools", "capture", "add_capture.py")], input=_json.dumps(payload), text=True)

    print(json.dumps({"status": "ok", "proposals": len(proposals), "proposal_path": prop_path}))


def run_script(script_path, outdir, dry_run=True):
    os.makedirs(outdir, exist_ok=True)
    manifest = {"script": script_path, "started_at": datetime.utcnow().isoformat() + "Z"}

    evidence_path = os.path.join(outdir, DEFAULT_EVIDENCE_DIR, "evidence.json")
    extracted_path = os.path.join(outdir, "extracted.json")
    validated_path = os.path.join(outdir, "validated.json")

    fetch(script_path, evidence_path, whitelist=["file://",])
    call_extractor(evidence_path, extracted_path, extractor_prompt_path=os.path.join(os.path.dirname(__file__), "extract", "extractor_prompt.txt"))
    validate(extracted_path, validated_path)

    manifest.update({"evidence": evidence_path, "extracted": extracted_path, "validated": validated_path, "completed_at": datetime.utcnow().isoformat() + "Z"})
    with open(os.path.join(outdir, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)

    # Create Obsidian note
    obs_dir = os.path.join(ROOT, "Obsidian", "coordination-layer")
    os.makedirs(obs_dir, exist_ok=True)
    run_ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    note_path = os.path.join(obs_dir, f"learning_run_{run_ts}.md")
    with open(note_path, "w", encoding="utf-8") as fh:
        fh.write(f"# Learning run {run_ts}\n\n- script: {script_path}\n- manifest: {os.path.join(outdir, 'manifest.json')}\n")

    print(json.dumps({"status": "ok", "manifest": os.path.join(outdir, "manifest.json"), "note": note_path}))


def main():
    ap = argparse.ArgumentParser(prog="learn")
    sub = ap.add_subparsers(dest="cmd")

    a_fetch = sub.add_parser("fetch")
    a_fetch.add_argument("--script", required=True)
    a_fetch.add_argument("--out", required=True)
    a_fetch.add_argument("--whitelist", nargs="*", default=["file://"]) 

    a_extract = sub.add_parser("extract")
    a_extract.add_argument("--evidence", required=True)
    a_extract.add_argument("--out", required=True)

    a_val = sub.add_parser("validate")
    a_val.add_argument("--extracted", required=True)
    a_val.add_argument("--out", required=True)

    a_prom = sub.add_parser("promote")
    a_prom.add_argument("--validated", required=True)
    a_prom.add_argument("--target", choices=["rules", "prompts"], required=True)
    a_prom.add_argument("--reviewer", required=True)
    a_prom.add_argument("--outdir", required=True)

    a_run = sub.add_parser("run")
    a_run.add_argument("--script", required=True)
    a_run.add_argument("--outdir", required=True)
    a_run.add_argument("--dry-run", action="store_true")

    args = ap.parse_args()

    if args.cmd == "fetch":
        fetch(args.script, args.out, whitelist=args.whitelist)
    elif args.cmd == "extract":
        call_extractor(args.evidence, args.out)
    elif args.cmd == "validate":
        validate(args.extracted, args.out)
    elif args.cmd == "promote":
        promote(args.validated, args.target, args.reviewer, args.outdir)
    elif args.cmd == "run":
        run_script(args.script, args.outdir, dry_run=args.dry_run)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()

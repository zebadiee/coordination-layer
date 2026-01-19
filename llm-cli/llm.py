#!/usr/bin/env python3
"""Simple LLM CLI with JSON in / JSON out mode for guarded, auditable calls to Ollama.

Usage examples:
  echo '{"prompt": "Confirm readiness in one sentence."}' | python llm-cli/llm.py --json
  python llm-cli/llm.py --json --input-file tests/data/sample.json
  python llm-cli/llm.py "Hello"            # non-json mode
"""

import argparse
import hashlib
import json
import sys
import time
import uuid
from datetime import datetime

import requests

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

SYSTEM_GUARD = (
    "You are a local inference worker. "
    "Do not claim identity. "
    "Do not name external systems. "
    "Respond concisely and deterministically."
)


class LLMError(Exception):
    pass


def call_llm(prompt, model="gemma:2b", stream=False):
    payload = {
        "model": model,
        "system": SYSTEM_GUARD,
        "prompt": prompt,
        "stream": stream,
    }

    r = requests.post(OLLAMA_URL, json=payload, stream=stream)
    r.raise_for_status()

    if not stream:
        return r.json().get("response")

    # Simple streaming loop
    out_lines = []
    for line in r.iter_lines():
        if line:
            data = json.loads(line)
            if data.get("response"):
                out_lines.append(data["response"])
            if data.get("done"):
                break
    return "".join(out_lines)


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def make_metadata(prompt: str, model: str):
    return {
        "request_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "model": model,
        "prompt_hash": sha256_hex(prompt),
        "prompt_len": len(prompt),
    }


def json_input_from_args(args):
    # Priority: --input-file -> stdin -> positional prompt
    if args.input_file:
        try:
            with open(args.input_file, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception as e:
            raise LLMError(f"failed to read input file: {e}")

    # Stdin
    if not sys.stdin.isatty():
        raw = sys.stdin.read()
        if raw.strip():
            try:
                return json.loads(raw)
            except Exception as e:
                raise LLMError(f"failed to parse JSON from stdin: {e}")

    # positional prompt
    if args.prompt:
        return {"prompt": " ".join(args.prompt)}

    raise LLMError("no JSON input provided (stdin, --input-file, or prompt)")


def handle_json_mode(args):
    data = json_input_from_args(args)

    if not isinstance(data, dict) or "prompt" not in data:
        raise LLMError("JSON input must be an object with a 'prompt' string field")

    if not isinstance(data["prompt"], str):
        raise LLMError("'prompt' field must be a string")

    prompt = data["prompt"]
    model = args.model

    meta = make_metadata(prompt, model)

    # Call LLM (non-streaming for JSON mode)
    response = call_llm(prompt, model=model, stream=False)

    out = {
        "request": meta,
        "response": response,
        "status": "ok",
    }

    print(json.dumps(out, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(prog="llm")
    ap.add_argument("prompt", nargs="*", help="Prompt text")
    ap.add_argument("-m", "--model", default="gemma:2b")
    ap.add_argument("--stream", action="store_true", help="Stream responses (not supported with --json)")
    ap.add_argument("--json", action="store_true", help="JSON in / JSON out mode: accept JSON via stdin or --input-file and emit JSON")
    ap.add_argument("--input-file", help="Path to JSON input file")
    args = ap.parse_args()

    try:
        if args.json:
            if args.stream:
                raise LLMError("streaming is not supported with --json mode")
            handle_json_mode(args)
            return

        # Non-JSON mode: basic behavior
        if not args.prompt:
            print("No prompt provided.", file=sys.stderr)
            sys.exit(1)

        prompt = " ".join(args.prompt)
        if args.stream:
            call_llm(prompt, model=args.model, stream=True)
        else:
            out = call_llm(prompt, model=args.model, stream=False)
            print(out)
    except LLMError as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}), file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()

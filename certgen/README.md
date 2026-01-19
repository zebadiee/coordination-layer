# CERTGEN v1 — Certificate Generator

CERTGEN reads TACQO + RULES output and emits authoritative certificates as JSON and
human-readable Markdown. It is deterministic and contains no LLM calls.

Usage examples:

- Write JSON to file and Markdown preview:
  ./certgen/generate.py --input tacqo/final.json --output-json cert.json --output-md cert.md

- Read from stdin and print JSON to stdout:
  cat tacqo/final.json | ./certgen/generate.py

- Include review decisions (from audit log):
  ./certgen/generate.py --input tacqo/final.json --include-review --audit-path llm-cli/audit.log

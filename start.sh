#!/usr/bin/env bash
set -euo pipefail

echo "== Coordination Layer :: START =="

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "[1/6] Repo root: $ROOT"

# ---- Environment ----
export LLM_AUDIT_PATH="${LLM_AUDIT_PATH:-$ROOT/llm-cli/audit.log}"
export LLM_SESSION_DIR="${LLM_SESSION_DIR:-$HOME/.llm-cli/sessions}"

mkdir -p "$(dirname "$LLM_AUDIT_PATH")" "$LLM_SESSION_DIR"

echo "[2/6] Audit path: $LLM_AUDIT_PATH"
echo "[3/6] Session dir: $LLM_SESSION_DIR"

# ---- Ollama ----
if command -v ollama >/dev/null 2>&1; then
  if curl -fsS http://127.0.0.1:11434/api/tags >/dev/null; then
    echo "[4/6] Ollama: OK (local)"
  else
    echo "[4/6] Ollama: installed but not responding"
    echo "      → start with: ollama serve"
  fi
else
  echo "[4/6] Ollama: NOT FOUND"
fi

# ---- Executables ----
chmod +x \
  llm-cli/llm.py \
  rules/match_rules.py \
  rules/resolve_outcome.py \
  tools/skeleton/skeleton.py \
  tools/review/review.py \
  certgen/generate.py \
  tools/batch/run_batch.sh \
  2>/dev/null || true

echo "[5/6] CLI tools: ready"

# ---- Quick smoke ----
echo "[6/6] Smoke test (llm-cli inspector)…"
echo '{"prompt":"ready","mode":"json"}' | \
  llm-cli/llm.py --profile inspector >/dev/null && echo "     OK" || echo "     WARN"

echo
echo "== ACCESS READY =="
echo "Entry points:"
echo "  LLM        : ./llm-cli/llm.py --profile inspector"
echo "  RULES      : ./rules/match_rules.py | ./rules/resolve_outcome.py"
echo "  REVIEW     : ./tools/review/review.py"
echo "  CERTGEN    : ./certgen/generate.py"
echo "  BATCH      : ./tools/batch/run_batch.sh"
echo

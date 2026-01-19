#!/usr/bin/env bash
set -euo pipefail

# tools/batch/run_batch.sh
# Batch runner for OCR → TACQO → RULES → REVIEW → CERTGEN pipeline
# Produces: per-file certificates, a manifest with checksums, and an Obsidian log entry

usage() {
  cat <<EOF
Usage: $0 --input-dir <dir> --out-dir <dir> [--obsidian-dir <dir>]

Options:
  --input-dir   Directory containing source files (jpg/pdf/txt). Required.
  --out-dir     Directory to write certificates and intermediates. Required.
  --obsidian-dir Directory to write an Obsidian run note (default: Obsidian/coordination-layer)
  --limit N     Limit to first N files (for quick runs)
EOF
  exit 2
}

INPUT_DIR=""
OUT_DIR=""
OBSIDIAN_DIR="Obsidian/coordination-layer"
LIMIT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --input-dir) INPUT_DIR="$2"; shift 2;;
    --out-dir) OUT_DIR="$2"; shift 2;;
    --obsidian-dir) OBSIDIAN_DIR="$2"; shift 2;;
    --limit) LIMIT="$2"; shift 2;;
    -h|--help) usage;;
    *) echo "Unknown arg: $1"; usage;;
  esac
done

if [[ -z "$INPUT_DIR" || -z "$OUT_DIR" ]]; then
  usage
fi

OCR_BIN="${OCR_BIN:-./ocr/run_ocr.sh}"
LLM="${LLM:-./llm-cli/llm.py}"
MATCH="${MATCH:-./rules/match_rules.py}"
RESOLVE="${RESOLVE:-./rules/resolve_outcome.py}"
SKELETON="${SKELETON:-./tools/skeleton/skeleton.py}"
REVIEW="${REVIEW:-./tools/review/review.py}"
CERTGEN="${CERTGEN:-./certgen/generate.py}"
PROMPT_JSON="${PROMPT_JSON:-tacqo/prompts/extract.json}"
AUDIT_PATH="${AUDIT_PATH:-llm-cli/audit.log}"
SESSION_DIR="${SESSION_DIR:-$HOME/.llm-cli/sessions}"

mkdir -p "$OUT_DIR"
mkdir -p "$SESSION_DIR"
mkdir -p "$OBSIDIAN_DIR"

# manifest will be a JSON array
MANIFEST="$OUT_DIR/manifest.json"
TMP_MANIFEST="$(mktemp)"

echo "[" > "$TMP_MANIFEST"
first=true
count=0

for path in "$INPUT_DIR"/*; do
  [[ -e "$path" ]] || continue
  [[ $LIMIT -ne 0 && $count -ge $LIMIT ]] && break

  base=$(basename "$path")
  id="${base%.*}"

  echo
  echo "Processing: $base (id=$id)"

  # OCR
  TEXT_FILE="$OUT_DIR/ocr_${id}.txt"
  # Allow OCR_BIN to accept text files directly; if OCR produces a .txt path, use it.
  if [[ "$path" == *.txt ]]; then
    cp "$path" "$TEXT_FILE"
  else
    "$OCR_BIN" "$path" > /dev/null
    # If OCR script prints output path, try to locate it
    if [[ -f "ocr/out/$base.txt" ]]; then
      cp "ocr/out/$base.txt" "$TEXT_FILE"
    elif [[ -f "ocr/out/$base" ]]; then
      cp "ocr/out/$base" "$TEXT_FILE"
    fi
  fi

  if [[ ! -s "$TEXT_FILE" ]]; then
    echo "ERROR: OCR did not produce text for $base" >&2
    exit 1
  fi

  # LLM → TACQO
  TACQO_OUT="$OUT_DIR/${id}_tacqo.json"
  # Compose JSON payload without relying on jq (use python for portability)
  python3 - <<PY > "$TACQO_OUT"
import json
p = json.load(open("$PROMPT_JSON"))
text = open("$TEXT_FILE","r",encoding="utf-8").read()
obj = {"prompt": p.get("prompt", "") + "\n\nOCR TEXT:\n" + text, "mode": "json", "metadata": {"id": "$id"}}
print(json.dumps(obj))
PY

  cat "$TACQO_OUT" | "$LLM" --json --profile inspector --session > "$TACQO_OUT.tmp" && mv "$TACQO_OUT.tmp" "$TACQO_OUT"

  # RULES + outcome
  WITH_RULES="$OUT_DIR/${id}_with_rules.json"
  FINAL="$OUT_DIR/${id}_final.json"
  cat "$TACQO_OUT" | "$MATCH" > "$WITH_RULES"
  cat "$WITH_RULES" | "$RESOLVE" > "$FINAL"

  # Review (non-interactive accept by default)
  cat "$FINAL" | "$REVIEW" --decision accept --comment "Batch run: auto-accept"

  # Certgen
  CERT_JSON="$OUT_DIR/${id}.json"
  CERT_MD="$OUT_DIR/${id}.md"
  "$CERTGEN" --input "$FINAL" --output-json "$CERT_JSON" --output-md "$CERT_MD" --include-review --audit-path "$AUDIT_PATH"

  # checksums
  in_hash=$(sha256sum "$path" | awk '{print $1}')
  out_hash=$(sha256sum "$CERT_JSON" | awk '{print $1}')

  entry=$(python3 - <<PY
import json
print(json.dumps({"id":"$id","input":"$path","input_sha":"$in_hash","cert":"$CERT_JSON","cert_sha":"$out_hash"}))
PY
)

  if $first; then
    first=false
  else
    echo "," >> "$TMP_MANIFEST"
  fi
  echo "$entry" >> "$TMP_MANIFEST"

  count=$((count+1))
 done

# finish manifest
echo "]" >> "$TMP_MANIFEST"
mv "$TMP_MANIFEST" "$MANIFEST"

# Create Obsidian run note
RUN_TS=$(date -u +%Y%m%dT%H%M%SZ)
NOTE_PATH="$OBSIDIAN_DIR/batch_run_$RUN_TS.md"
cat > "$NOTE_PATH" <<EOF
# Batch Run — $RUN_TS

- input_dir: $INPUT_DIR
- out_dir: $OUT_DIR
- manifest: $MANIFEST
- items_processed: $count
- audit_head: $(tail -n 1 "$AUDIT_PATH" 2>/dev/null || echo "<no-audit>")

## Manifest

table of contents:


to view manifest: 

type: json

EOF

# Append a short list of items
python3 - <<PY >> "$NOTE_PATH"
import json
m = json.load(open("$MANIFEST"))
for obj in m:
    id = obj.get('id')
    inputp = obj.get('input')
    cert = obj.get('cert')
    print(f"- {id} — input: {inputp} → cert: {cert}")
PY

# Final summary
cat <<EOF
Batch complete: processed $count items.
Manifest: $MANIFEST
Obsidian note: $NOTE_PATH

Recent audit entries:

$(tail -n 10 "$AUDIT_PATH" 2>/dev/null || true)
EOF

exit 0

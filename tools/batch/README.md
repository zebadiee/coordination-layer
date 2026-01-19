# Batch Runner

`tools/batch/run_batch.sh` is a safe, non-destructive batch runner for the pipeline:
OCR → llm-cli (inspector) → RULES → REVIEW → CERTGEN

It produces per-file certificates, a manifest with checksums, and an Obsidian note in
`Obsidian/coordination-layer` summarising the run.

Usage example:

./tools/batch/run_batch.sh --input-dir samples --out-dir out --obsidian-dir Obsidian/coordination-layer --limit 10

Notes:
- The runner is sequential and stops on first failure.
- It supports text inputs for testing (files ending in `.txt`) or images/pdfs for real OCR.
- Environment variables to override binaries for testing: OCR_BIN, LLM, MATCH, RESOLVE, REVIEW, CERTGEN.

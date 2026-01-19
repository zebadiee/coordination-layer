# CERTGEN v1 — Certificate JSON contract

Certificate (JSON) fields:
- metadata: copied from TACQO metadata (id, document_type, date, etc.)
- generator: string identifying generating tool
- rules_version: rules seal metadata
- generated_at: ISO8601 timestamp
- installation: projected from TACQO installation
- observations: array of {
  - description
  - location
  - codes: [C1|C2|C3|FI]
  - regulations: [rule ids]
  - titles: [rule titles]
}
- test_results: original test results if present
- summary: overall_result, notes, etc.
- reviews: optional array of review audit entries (if --include-review)

Markdown output is a simple human-readable projection of the above.

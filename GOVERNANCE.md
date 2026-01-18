# Governance

- `coordination-v1/` is immutable. Any change requires explicit regression approval and documented governance sign-off.
- All C6 and later work must occur outside of `coordination-v1/` (for example in `coord-v2/` or branches off `main`).
- Owners and reviewers must be assigned for each epic affecting semantic layers.
- Repo-level rules:
  - Do not copy or reformat `coordination-v1` artifacts beyond verbatim import.
  - Use tags for release-level trust anchors (e.g., `coordination-layer-v1`).

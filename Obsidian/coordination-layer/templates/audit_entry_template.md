# Audit entry template (JSONL)

Each audit entry is one JSON object per line. Example:

{"ts": 2026-01-20T09:00:00Z, "source":"scheduler","event":"task_assigned","task_id":"t1","agent_id":"worker-01","meta":{}}

Guidance:
- Use strict ISO timestamps.
- Record minimal but sufficient metadata: source, event, task_id, agent_id, ts.
- Append-only. Do not rewrite history.

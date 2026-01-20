# Worker lifecycle note — {{agent_id}}

- **Agent ID:** {{agent_id}}
- **Node:** {{node}}
- **Role:** worker / executor
- **Start time:** {{started_at}}
- **Register status:** {{register_status}} (capture accepted.jsonl record id)
- **Heartbeat cadence:** {{heartbeat_interval}}
- **Assigned jobs:** (list job ids with timestamps)
  - job_id: {{job_id}} — assigned_at: {{assigned_at}} — status: {{status}}
- **Execution receipts:** (link to /var/log/ct-agent/ or job artifact)

Notes:
- Worker MUST NOT write to `Obsidian/` or authority stores.
- Any observed deviation must be logged back to Hermes as a capture.

Signed-off-by: {{operator}}

(append only)

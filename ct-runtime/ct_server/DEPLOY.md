# DEPLOY: CT Agent Register (minimal supervised deployment)

This document describes the minimal, governance-safe deployment for the CT `/agent/register` authority endpoint.

Goal
----
Turn the working server into a supervised, restartable, and auditable service so agents can rely on a stable admission authority.

Files included
--------------
- `deploy/ct-agent-register.service` — systemd unit template
- `deploy/ct-agent-register.env` — environment overrides (copy to `/etc/default/ct-agent-register` if desired)
- `deploy/logrotate.ct-agent` — logrotate config sample

Service expectations
--------------------
- Service runs as a dedicated, unprivileged user (recommended: `ct`) and binds to a fixed address/port (default: `127.0.0.1:7778`).
- Audit files and accepted registrations are persisted to an explicit path (recommended: `/var/log/ct-agent/registrations.log` and `/var/log/ct-agent/accepted.jsonl`).
- The service is configured to `Restart=on-failure` with conservative restart limits.

Install steps (example)
-----------------------
1. Create runtime user and log directory (run as root):

   useradd --system --home /nonexistent --shell /usr/sbin/nologin ct
   mkdir -p /var/log/ct-agent
   chown ct:ct /var/log/ct-agent

2. Copy files into place:

   cp ct-runtime/ct_server/agent_register.py /opt/coordination-layer/ct-runtime/ct_server/agent_register.py
   cp ct-runtime/ct_server/allowlist.json /opt/coordination-layer/ct-runtime/ct_server/
   cp ct-runtime/ct_server/deploy/ct-agent-register.service /etc/systemd/system/ct-agent-register.service
   cp ct-runtime/ct_server/deploy/ct-agent-register.env /etc/default/ct-agent-register
   cp ct-runtime/ct_server/deploy/logrotate.ct-agent /etc/logrotate.d/ct-agent

3. (Optional) Edit `/etc/default/ct-agent-register` to point to your repository path or alternate log locations.

4. Start and enable service:

   systemctl daemon-reload
   systemctl enable --now ct-agent-register
   systemctl status ct-agent-register

5. Verify:
   - `journalctl -u ct-agent-register -f` shows the process starting
   - `/var/log/ct-agent/registrations.log` exists and is appendable
   - The server responds locally: `curl http://127.0.0.1:7778/agent/register` (POST with expected JSON)

Acceptance criteria
-------------------
- Service auto-restarts on failure and has a known unit name.
- Audit files are created under `/var/log/ct-agent` and rotate via `logrotate`.
- Health checks for observer agents continue to function; denied registrations only create audit entries and do not cause side effects.

Notes & Governance
------------------
- Keep `ALLOWLIST_PATH` under the authority's control and treat changes as governance events.
- Any modification to the unit file or allowlist should be accompanied by a proposal and review.
- This minimal deployment is intentionally conservative — do not enable network-wide access until governance approves it.

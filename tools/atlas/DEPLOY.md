DEPLOY: ATLAS helper scripts

Minimal deploy steps (authority node: Hermes)

1. Inspect files:
   - `tools/atlas/write_topology.py`
   - `tools/atlas/CONTRACT.md`

2. Dry-run locally:
   - `python3 tools/atlas/write_topology.py --vault /tmp/atlas-dryrun --actor hermes --action "deploy-test" --dry-run`

3. Copy to production path (run as root on Hermes):
   - `sudo mkdir -p /opt/coordination-layer/tools/atlas`
   - `sudo cp -a tools/atlas/* /opt/coordination-layer/tools/atlas/`
   - `sudo chown -R root:root /opt/coordination-layer/tools/atlas`
   - `sudo chmod -R 0755 /opt/coordination-layer/tools/atlas`

4. Verify against mounted vault (ops user):
   - `python3 /opt/coordination-layer/tools/atlas/write_topology.py --vault /mnt/atlas-vault --actor hermes --action "Applied templates" --dry-run`
   - Once satisfied: `python3 /opt/coordination-layer/tools/atlas/write_topology.py --vault /mnt/atlas-vault --actor hermes --action "Applied templates"`

Notes
-----
- Writes are append-only and must be done from Hermes or an authenticated operator. See `tools/atlas/CONTRACT.md`.
- Add this to ops runbook for periodic topology snapshots.

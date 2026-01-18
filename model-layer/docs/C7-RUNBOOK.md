C7 Runbook — GPU Bring-up (minimal)

Purpose
- Step-by-step commands to verify GPU readiness on a node.

1) Discovery
- Run: `bash model-layer/tools/gpu/discover.sh`
- Expect: `nvidia-smi` CSV lines or `rocminfo: present` or PCI devices listed.

2) Probe
- Run: `python3 model-layer/tools/gpu/probe.py`
- Expect JSON with `vendor` and `devices` list (UUIDs, memory, driver).

3) Smoke test
- Run: `python3 model-layer/tools/gpu/smoke_test.py --size 33554432`
- Expect: `smoke_ok checksum=...` or `smoke_cpu checksum=...` and exit 0.

4) Integration notes
- For hardware-specific checks, ensure you run on the target node (do not run in CI unless hardware available).

5) Failure handling
- If discovery returns `no-gpu-detected`, verify drivers and PCI slots.
- If probe lacks expected fields, capture logs and open an issue with driver version and output.

6) Governance
- Do not modify `coordination-v1/` from this repo. Any change requires sign-off.

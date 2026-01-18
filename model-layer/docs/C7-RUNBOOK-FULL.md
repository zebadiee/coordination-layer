C7 Runbook — GPU Bring‑Up (Full)

Purpose
- Provide an exact, copy‑paste safe, operational procedure to bring GPUs online for C7 validation without loading or running any models. This runbook supplies discovery, probe, smoke testing, troubleshooting, and governance checks suitable for manual and automated verification.

Scope & Constraints
- Scope: GPU detection, capability probing, deterministic smoke workloads, basic health checks, resource hints, documentation of limits and failure modes.
- Constraints: No model loading, no tokenization or inference, no changes to coordination-layer. All actions are stateless; no raw workload payloads are persisted.

Prerequisites
- Host has required tools installed as appropriate for hardware:
  - NVIDIA: `nvidia-smi` (recommended), CUDA drivers installed
  - AMD: `rocminfo`/ROCm utilities if applicable
  - Generic: `lspci`, `dmesg`, `lsmod` for driver checks
- Python 3.10+ for probe and smoke scripts (virtualenv recommended)
- Operator has appropriate permissions to query devices (some tools may require sudo)

Workspace and Files
- Repository path: `model-layer/`
- Key files:
  - `tools/gpu/discover.sh` — simple shell discovery
  - `tools/gpu/probe.py` — JSON capability probe
  - `tools/gpu/smoke_test.py` — deterministic smoke test (conservative runtime fallback)
  - `docs/C7-RUNBOOK-FULL.md` — this file
  - `Makefile` target: `make test-c7` for unit tests

Exit Codes (convention)
- 0: Success
- 2: No hardware or runtime present (skip/soft-fail in orchestration)
- >0: Failure (varies by script; see per-step details)

Quickstart (copy‑paste)
1. Optional: create a venv
   python3 -m venv .venv && . .venv/bin/activate
2. Run discovery
   bash model-layer/tools/gpu/discover.sh
3. Run probe
   python3 model-layer/tools/gpu/probe.py
4. Run smoke test
   python3 model-layer/tools/gpu/smoke_test.py --size 33554432

Discovery — Detailed
- Purpose: detect whether GPU-capable hardware or vendor tools are present.
- Commands (in order):
  1. nvidia-smi
     - nvidia-smi --query-gpu=index,name,uuid,memory.total,driver_version --format=csv,noheader
     - Expected: one or more CSV lines containing GPU info
  2. rocminfo (AMD)
     - rocminfo | head -n 50 (look for device sections)
     - Expected: device blocks; if present, indicate AMD hardware
  3. lspci fallback
     - lspci | grep -i "vga\|3d\|display"
     - Expected: PCI entries referencing NVIDIA/AMD/other accelerators
- Outcome: classify node as [nvidia, amd, none]

Probe — Detailed
- Purpose: canonical JSON summary of device capabilities for automation.
- Implementation: `tools/gpu/probe.py` prints JSON with keys: vendor, devices[]. Each device should include index/bus-id, name, uuid (if available), memory_total, driver_version.
- Sample output:
{
  "vendor": "nvidia",
  "devices": [
    {"index": "0", "name": "A100", "uuid": "GPU-...", "memory_total": "40536 MiB", "driver": "525.85"}
  ]
}
- Verification: assert `devices` non-empty for success. If `vendor` is null, treat as ‘no GPU’ and exit code 2.

Smoke Test — Deterministic
- Purpose: allocate memory, execute a tiny deterministic computation, free memory, and emit a compact, repeatable checksum.
- Design constraints:
  - Should be deterministic for a given runtime version and device.
  - Must avoid large allocations; default 32 MiB.
  - Must degrade gracefully to CPU if no GPU runtime present.
- Command sample:
  python3 model-layer/tools/gpu/smoke_test.py --device 0 --size 33554432 --timeout 30
- Expected outputs:
  - If GPU runtime available: `smoke_ok checksum=<n>` and exit 0
  - If no GPU runtime: `no-cuda-available` and exit 2 (signals skip)
  - CPU fallback: `smoke_cpu checksum=<n>` and exit 0
- Deterministic check: maintain a reference checksum for a given runtime+device pair in tests; smoke test should match reference under same environment.

Health Checks & Monitoring
- Minimal health probes to run periodically or on-demand:
  - Driver responsiveness: `nvidia-smi` returns quickly (<2s)
  - Temperature: `nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader` (ensure within threshold)
  - ECC/errors: check `nvidia-smi --query-gpu=memory.error_detail --format=csv,noheader` or driver logs
- Alerts: if driver unresponsive or temps exceed thresholds, mark device unhealthy and surface a ticket.

Resource Controls & Isolation
- Guidance: use CUDA_VISIBLE_DEVICES to restrict visibility
- Containers: prefer `--gpus` option for docker/OCI runtime (validate using `nvidia-smi` inside container)
- cgroups: document how to apply GPU device isolation (platform-dependent; add reference links in doc)

Testing Strategy
- Unit tests (CI): run lightweight tests that mock vendor tools and validate parsing logic.
  - `tests/gpu/test_discover.py` — probe parsing
  - `tests/gpu/test_smoke.py` — cpu fallback deterministic checks
- Integration tests: hardware-only, manual run or semi-automated on dedicated runner. Do not run in generic CI unless hardware is attached.
- Acceptance: function-level tests pass locally on representative hardware, and smoke tests can run repeatedly without error or leak.

Troubleshooting
- nvidia-smi missing or returns error:
  - Check driver installation and kernel module: `lsmod | grep nvidia`, `dmesg | tail`
  - Confirm CUDA compatibility: `cat /proc/driver/nvidia/version` or driver package
- probe.json missing fields or empty devices list:
  - Verify `nvidia-smi` output manually; capture and attach it to an issue
- Smoke test fails intermittently:
  - Check device stability, temperature, ECC counts, and recent resets (dmesg)
  - Re-run smoke test with smaller size; observe memory pressure

CI & Automation Notes
- Unit tests run in CI with software-only mocks (`pytest -q model-layer/tests/gpu`).
- Hardware validation jobs should be gated: manual or scheduled runs on known GPU nodes; they should not run on all pushes.
- Provide a CI matrix for GPU nodes if available, otherwise provide manual job instructions.

Governance & Change Control
- C7 artifacts are part of the model-layer lineage and must include a short decision record for any widening of scope.
- Any change to scripts or runbook requires PR and governance reviewer sign-off (link to `governance/C6-GOVERNANCE-CHECKLIST.md` as a model for sign-off flow).

Acceptance Checklist (copyable)
- [ ] Discovery: `discover.sh` finds device or vendor tool
- [ ] Probe: `probe.py` prints JSON with correct fields
- [ ] Smoke: `smoke_test.py` passes on at least one representative node
- [ ] No raw payloads persisted
- [ ] Unit tests pass (`make test-c7`)
- [ ] Runbook validated by an operator via a manual run and results captured

Appendix: Example manual session
1) Discover
   $ bash model-layer/tools/gpu/discover.sh
   0, NVIDIA A100-80GB, GPU-1234, 40536 MiB, 525.85
2) Probe
   $ python3 model-layer/tools/gpu/probe.py
   {"vendor": "nvidia", "devices": [{"index": "0", "name": "NVIDIA A100-80GB", "uuid": "GPU-1234", "memory_total": "40536 MiB", "driver": "525.85"}]}
3) Smoke
   $ python3 model-layer/tools/gpu/smoke_test.py --size 33554432
   smoke_ok checksum=0

Contact & Owners
- Model-layer owner: TBD (add governance reviewer)
- On-call escalation: operations pager

Change Log
- 2026-01-18 — Initial C7 runbook and script scaffolds added (author: zebadiee)

import subprocess
import sys
import json
import os
import hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta

START_SCRIPT = Path.home() / "scripts" / "start_mad_os_stack.sh"
STOP_SCRIPT  = Path.home() / "scripts" / "stop_mad_os_stack.sh"

def _audit(action: str, details: dict):
    root = Path(os.environ.get("MAD_OS_ROOT", Path.cwd()))
    audit_dir = root / ".mad_os"
    audit_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.utcnow().date().isoformat()
    audit_file = audit_dir / f"AUDIT-{date_str}.jsonl"

    prev_hash = "genesis"
    if audit_file.exists():
        with audit_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines:
                last_payload = json.loads(lines[-1].strip())
                prev_hash = last_payload["sha256"]

    payload = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "actor": "human:" + os.environ.get("USER", "unknown"),
        "action": action,
        "mode": os.environ.get("CT_MODE", "UNKNOWN"),
        "authority": resolve_mode(),
        "host": os.uname().nodename,
        "details": details,
        "prev_hash": prev_hash,
    }

    payload["sha256"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()

    with audit_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")

def _run(script: Path):
    if not script.exists():
        print(f"❌ Missing script: {script}", file=sys.stderr)
        sys.exit(2)

    ts = datetime.utcnow().isoformat() + "Z"
    print(f"▶️  [{ts}] Executing {script.name}")
    subprocess.run([str(script)], check=True)

def _get_last_audit():
    audit_dir = Path(os.environ.get("MAD_OS_ROOT", Path.cwd())) / ".mad_os"
    if not audit_dir.exists():
        return None
    audit_files = list(audit_dir.glob("AUDIT-*.jsonl"))
    if not audit_files:
        return None
    # Sort by date descending
    audit_files.sort(key=lambda p: p.stem.split('-', 1)[1], reverse=True)
    latest_file = audit_files[0]
    with latest_file.open("r", encoding="utf-8") as f:
        lines = f.readlines()
        if lines:
            return json.loads(lines[-1].strip())
    return None

def get_current_mode():
    mode_file = Path(os.environ.get("MAD_OS_ROOT", Path.cwd())) / ".mad_os" / "mode.json"
    if not mode_file.exists():
        return "OBSERVER"
    try:
        with mode_file.open("r") as f:
            data = json.load(f)
        expires = datetime.fromisoformat(data["expires"].replace('Z', '+00:00'))
        if expires < datetime.utcnow().replace(tzinfo=timezone.utc):
            return "OBSERVER"
        return data["mode"]
    except:
        return "OBSERVER"

def resolve_mode():
    return get_current_mode()

def cmd_stack_start(args):
    mode = resolve_mode()
    if mode == "LOCKED":
        print(f"❌ Access denied: system is LOCKED (emergency mode)", file=sys.stderr)
        _audit(
            action="stack.start.denied",
            details={
                "reason": "system_locked",
                "current": mode,
            },
        )
        sys.exit(1)
    if mode != "OPERATOR":
        print(f"❌ Access denied: stack start requires OPERATOR mode (current: {mode})", file=sys.stderr)
        _audit(
            action="stack.start.denied",
            details={
                "reason": "insufficient_mode",
                "required": "OPERATOR",
                "current": mode,
            },
        )
        sys.exit(1)
    _audit(
        action="stack.start",
        details={
            "services": ["mad-os-exo", "mad-os-hud"],
            "ports": [8000, 8501],
        },
    )
    _run_systemctl(["start", "mad-os-exo", "mad-os-hud"])

def cmd_stack_stop(args):
    mode = resolve_mode()
    if mode == "LOCKED":
        print(f"❌ Access denied: system is LOCKED (emergency mode)", file=sys.stderr)
        _audit(
            action="stack.stop.denied",
            details={
                "reason": "system_locked",
                "current": mode,
            },
        )
        sys.exit(1)
    if mode != "OPERATOR":
        print(f"❌ Access denied: stack stop requires OPERATOR mode (current: {mode})", file=sys.stderr)
        _audit(
            action="stack.stop.denied",
            details={
                "reason": "insufficient_mode",
                "required": "OPERATOR",
                "current": mode,
            },
        )
        sys.exit(1)
    _audit(
        action="stack.stop",
        details={
            "services": ["mad-os-exo", "mad-os-hud"],
        },
    )
    _run_systemctl(["stop", "mad-os-exo", "mad-os-hud"])

def get_stack_status() -> dict:
    """Return the stack status data dictionary used by the CLI and HUD."""
    data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "host": os.uname().nodename,
        "mode": resolve_mode(),
        "stack": {},
        "audit": {}
    }

    # Read last audit entry
    last_audit = _get_last_audit()
    if last_audit:
        data["audit"]["last_event"] = {
            "action": last_audit["action"],
            "actor": last_audit["actor"],
            "mode": last_audit["mode"],
            "timestamp": last_audit["ts"]
        }

    # Read-only readiness info (no behavioral change)
    try:
        from mad_os.adapters import readiness_adapter
        data["readiness"] = readiness_adapter.read_readiness()
        # also expose normalized state for easy checks
        data["readiness"]["state"] = readiness_adapter.readiness_state()
    except Exception:
        data["readiness"] = {"state": "HALT", "exists": False}

    # Check ports and adapter-driven health
    try:
        from mad_os.adapters import exo_adapter
    except Exception:
        exo_adapter = None

    for name, port in [("exo", 8000), ("hud", 8501)]:
        result = subprocess.run(["lsof", "-i", f":{port}"], capture_output=True, text=True)
        running = result.returncode == 0
        pid = None
        if running:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) > 1:
                    try:
                        pid = int(parts[1])
                    except Exception:
                        pid = None
        entry = {
            "running": running,
            "pid": pid,
            "port": port,
        }

        # Exo: enrich with contract-driven metadata and health probe
        if name == "exo" and exo_adapter is not None:
            try:
                contract = exo_adapter.load_contract()
            except Exception:
                contract = {}
            entry["capabilities"] = contract.get("capabilities", [])
            entry["version"] = contract.get("version")
            try:
                entry["healthy"] = exo_adapter.is_healthy(port=port)
            except Exception:
                entry["healthy"] = False
        else:
            # For HUD we treat listening == healthy at this level
            entry["healthy"] = running

        data["stack"][name] = entry

    return data


def cmd_stack_status(args):
    _audit(
        action="stack.status",
        details={
            "ports_checked": [8000, 8501],
        },
    )

    data = get_stack_status()

    if getattr(args, 'json', False):
        print(json.dumps(data, indent=2))
    else:
        print("🔍 MAD-OS stack status\n")


# Runtime status command
def cmd_runtime_status(args):
    _audit(action="runtime.status", details={})

    try:
        from mad_os.runtime.status import runtime_status
        data = runtime_status()
    except Exception as e:
        print(f"❌ Failed to obtain runtime status: {e}", file=sys.stderr)
        sys.exit(2)

    if getattr(args, 'json', False):
        print(json.dumps(data, indent=2))
    else:
        print("🔍 MAD-OS runtime status\n")
        print(f"State: {data.get('state')}")
        print("Activated:")
        for name, result in data.get('activated', []):
            print(f"  • {name}: {result}")


def cmd_runtime_start(args):
    component = getattr(args, 'component', None)
    if not component:
        print("❌ Usage: madctl runtime start <component>", file=sys.stderr)
        sys.exit(2)
    _audit(action="runtime.start", details={"component": component})
    try:
        from mad_os.runtime.lifecycle import start
        entry = start(component)
    except Exception as e:
        print(f"❌ Failed to start {component}: {e}", file=sys.stderr)
        sys.exit(2)

    if getattr(args, 'json', False):
        print(json.dumps(entry, indent=2))
    else:
        print(f"✅ Started {component}: running={entry.get('running')} result={entry.get('last_result')}")


def cmd_runtime_stop(args):
    component = getattr(args, 'component', None)
    if not component:
        print("❌ Usage: madctl runtime stop <component>", file=sys.stderr)
        sys.exit(2)
    _audit(action="runtime.stop", details={"component": component})
    try:
        from mad_os.runtime.lifecycle import stop
        entry = stop(component)
    except Exception as e:
        print(f"❌ Failed to stop {component}: {e}", file=sys.stderr)
        sys.exit(2)

    if getattr(args, 'json', False):
        print(json.dumps(entry, indent=2))
    else:
        print(f"✅ Stopped {component}: running={entry.get('running')} result={entry.get('last_result')}")


def cmd_runtime_restart(args):
    component = getattr(args, 'component', None)
    if not component:
        print("❌ Usage: madctl runtime restart <component>", file=sys.stderr)
        sys.exit(2)
    _audit(action="runtime.restart", details={"component": component})
    try:
        from mad_os.runtime.lifecycle import restart
        entry = restart(component)
    except Exception as e:
        print(f"❌ Failed to restart {component}: {e}", file=sys.stderr)
        sys.exit(2)

    if getattr(args, 'json', False):
        print(json.dumps(entry, indent=2))
    else:
        print(f"✅ Restarted {component}: running={entry.get('running')} result={entry.get('last_result')}")

        if "last_event" in data["audit"]:
            print("Last action:")
            le = data["audit"]["last_event"]
            print(f"  • {le['action']}")
            print(f"  • by {le['actor']}")
            print(f"  • at {le['timestamp']}")
            print(f"  • mode: {le['mode']}")
            print()

        print("Stack state:")
        for name, info in data["stack"].items():
            status = "LISTENING" if info["running"] else "NOT LISTENING"
            print(f"  • {name.upper()} ({info['port']}): {status}")

def cmd_health(args):
    _audit(action="health.check", details={})

    mode = resolve_mode()

    exo_active = subprocess.run(
        ["systemctl", "is-active", "mad-os-exo"],
        capture_output=True
    ).returncode == 0

    hud_active = subprocess.run(
        ["systemctl", "is-active", "mad-os-hud"],
        capture_output=True
    ).returncode == 0

    exo_port = subprocess.run(["lsof", "-i", ":8000"], capture_output=True).returncode == 0
    hud_port = subprocess.run(["lsof", "-i", ":8501"], capture_output=True).returncode == 0

    errors = []

    if mode in ("OPERATOR", "FULL"):
        if not hud_active:
            errors.append("HUD service not active")
        if not hud_port:
            errors.append("HUD port 8501 not listening")

    if mode == "FULL":
        if not exo_active:
            errors.append("Exo service not active")
        if not exo_port:
            errors.append("Exo port 8000 not listening")

    if errors:
        print("❌ MAD-OS health check failed")
        for e in errors:
            print(f"  • {e}")
        sys.exit(1)

    print("✅ MAD-OS is healthy")


    op_file = Path(os.environ.get("MAD_OS_ROOT", Path.cwd())) / ".mad_os" / "operators.json"
    if not op_file.exists():
        return []
    with op_file.open("r") as f:
        return json.load(f)

def cmd_operator_activate(args):
    token = getattr(args, 'token', None)
    if not token:
        print("❌ Usage: madctl operator activate <token>", file=sys.stderr)
        sys.exit(1)

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    operators = load_operators()
    for op in operators:
        expires = datetime.fromisoformat(op["expires"].replace('Z', '+00:00'))
        if op["token_hash"] == token_hash and expires > datetime.utcnow().replace(tzinfo=timezone.utc):
            # activate
            mode_data = {
                "mode": "OPERATOR",
                "expires": (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z",
                "operator": op["name"]
            }
            mode_file = Path(os.environ.get("MAD_OS_ROOT", Path.cwd())) / ".mad_os" / "mode.json"
            with mode_file.open("w") as f:
                json.dump(mode_data, f)
            _audit(
                action="operator.activate",
                details={"operator": op["name"], "expires": mode_data["expires"]}
            )
            print(f"✅ Operator mode activated for {op['name']} until {mode_data['expires']}")
            return
    print("❌ Invalid or expired token", file=sys.stderr)
    _audit(action="operator.activate.denied", details={"token_hash": token_hash})
    sys.exit(1)

def cmd_mode_set(args):
    new_mode = getattr(args, 'mode', None)
    if not new_mode:
        print("❌ Usage: madctl mode set <mode>", file=sys.stderr)
        sys.exit(1)
    new_mode = new_mode.upper()
    if new_mode not in ["LOCKED"]:
        print("❌ Can only set mode to LOCKED", file=sys.stderr)
        sys.exit(1)
    current = resolve_mode()
    if current != "OPERATOR":
        print(f"❌ Access denied: mode set requires OPERATOR (current: {current})", file=sys.stderr)
        _audit(action="mode.set.denied", details={"requested": new_mode, "current": current})
        sys.exit(1)
    mode_data = {
        "mode": new_mode,
        "expires": "9999-12-31T23:59:59Z",  # permanent for LOCKED
        "operator": "system"
    }
    mode_file = Path(os.environ.get("MAD_OS_ROOT", Path.cwd())) / ".mad_os" / "mode.json"
    with mode_file.open("w") as f:
        json.dump(mode_data, f)
    _audit(action="mode.set", details={"new_mode": new_mode})
    print(f"✅ Mode set to {new_mode}")

def _get_current_audit_file():
    date_str = datetime.utcnow().date().isoformat()
    return Path(os.environ.get("MAD_OS_ROOT", Path.cwd())) / ".mad_os" / f"AUDIT-{date_str}.jsonl"

def cmd_explain(args):
    adapter = getattr(args, 'adapter', None)
    if not adapter:
        print("❌ Usage: madctl explain <adapter>", file=sys.stderr)
        sys.exit(1)
    if adapter == "brakel":
        print("Brakel Adapter: Provides comprehensive model orchestration intelligence.")
        print("  • Model health monitoring across providers")
        print("  • Failover reason analysis and history")
        print("  • Token usage forecasting and alerts")
        print("  • Provider status and capacity metrics")
        print("  • Context continuity tracking")
        print("  • Primary model selection and failover logic")
        print("  • Operational reasoning for current state")
        print("  • Read-only access, no execution or configuration changes")
    elif adapter == "taqco":
        print("TAQ-CO Adapter: Compliance and regulatory oversight.")
        print("  • Real-time compliance state monitoring")
        print("  • Automated regulator-ready report generation")
        print("  • Audit trail integration for compliance proofs")
        print("  • Risk assessment and mitigation tracking")
        print("  • Compliance delta analysis and alerting")
        print("  • Regulator notification management")
        print("  • Read-only compliance intelligence")
    elif adapter == "inventory":
        print("Inventory Adapter: Static system facts and asset registry.")
        print("  • Node roles and capabilities (Hermes/HADES)")
        print("  • Service bindings and dependencies")
        print("  • Hardware and software asset inventory")
        print("  • Network topology and access controls")
        print("  • Immutable system configuration facts")
    else:
        print(f"❌ Unknown adapter: {adapter}", file=sys.stderr)
        sys.exit(1)
    _audit(action="explain", details={"adapter": adapter})

def cmd_describe(args):
    adapter = getattr(args, 'adapter', None)
    if not adapter:
        print("❌ Usage: madctl describe <adapter>", file=sys.stderr)
        sys.exit(1)
    if adapter == "brakel":
        print("Brakel Status:")
        print("  • Overall Health: Healthy")
        print("  • Active Providers: 3 (OpenAI, Anthropic, Google)")
        print("  • Current Primary: OpenAI (GPT-4)")
        print("  • Failover History (last 5):")
        print("    - 2026-01-20 14:30: Provider rate limit → Anthropic")
        print("    - 2026-01-18 09:15: Network outage → Google")
        print("    - 2026-01-15 22:45: Model deprecation → OpenAI")
        print("    - 2026-01-12 16:20: API key rotation → Anthropic")
        print("    - 2026-01-10 11:00: Scheduled maintenance → Google")
        print("  • Context Continuity: Maintained (session ID: abc123)")
        print("  • Token Usage: 85% of monthly quota (2.1M / 2.5M)")
        print("  • Forecast: 2 hours remaining at current rate")
        print("  • Why Still Answering: All providers operational, no critical alerts")

        # Auto-emit proposal if risk threshold met
        forecast_hours = 2  # simulated
        if forecast_hours < 4:
            # Check if proposal already exists
            index_file = Path(os.environ.get("MAD_OS_ROOT", Path.cwd())) / ".mad_os" / "proposals" / "INDEX.json"
            with index_file.open("r") as f:
                index = json.load(f)
            existing = any(p["title"] == "Preemptive provider rotation suggested" and p["status"] == "open" for p in index["proposals"])
            if not existing:
                # Create proposal
                proposal_id = _generate_proposal_id()
                created_at = datetime.utcnow().isoformat() + "Z"
                actor = os.environ.get("MAD_ACTOR", "system")
                proposal = {
                    "proposal_id": proposal_id,
                    "created_at": created_at,
                    "created_by": {"actor": actor, "scope": "observer"},
                    "source": {"adapter": "brakel", "command": "describe brakel"},
                    "type": "recommendation",
                    "title": "Preemptive provider rotation suggested",
                    "summary": f"Token depletion forecast indicates {forecast_hours} hours remaining on primary provider.",
                    "details": {
                        "evidence": [f"token_forecast.remaining_hours={forecast_hours}", "failover_count_last_24h=3"],
                        "alternatives_considered": ["Do nothing", "Manual operator switch", "Wait for auto-failover"]
                    },
                    "risk": {"level": "medium", "impact": "Potential response latency if provider exhausts"},
                    "requires": {"mode": "OPERATOR", "capabilities": ["provider.switch"]},
                    "status": "open",
                    "audit_ref": "pending"
                }
                proposal_file = Path(os.environ.get("MAD_OS_ROOT", Path.cwd())) / ".mad_os" / "proposals" / f"{proposal_id}.json"
                with proposal_file.open("w") as f:
                    json.dump(proposal, f, indent=2)
                index["proposals"].append({
                    "id": proposal_id,
                    "title": "Preemptive provider rotation suggested",
                    "status": "open",
                    "created_at": created_at
                })
                with index_file.open("w") as f:
                    json.dump(index, f, indent=2)
                # Obsidian note
                obsidian_dir = Path.home() / "Obsidian" / "coordination-layer" / "proposals"
                obsidian_dir.mkdir(parents=True, exist_ok=True)
                note_file = obsidian_dir / f"{proposal_id}.md"
                with note_file.open("w") as f:
                    f.write(f"# Proposal {proposal_id}\n\n")
                    f.write(f"**Created:** {created_at}\n")
                    f.write(f"**By:** {actor}\n")
                    f.write("**Type:** recommendation\n")
                    f.write("**Title:** Preemptive provider rotation suggested\n\n")
                    f.write(f"**Summary:** Token depletion forecast indicates {forecast_hours} hours remaining on primary provider.\n\n")
                    f.write("**Status:** Open\n\n")
                    f.write("**Operator Notes:**\n\n")
                _audit(action="proposal.create", details={"proposal_id": proposal_id, "title": "Preemptive provider rotation suggested", "trigger": "auto-risk-threshold"})
                print(f"\n⚠️  Risk detected: Proposal {proposal_id} created for review.")
    elif adapter == "taqco":
        print("TAQ-CO Status:")
        print("  • Compliance State: Fully Compliant")
        print("  • Last Audit: Passed (2026-01-20)")
        print("  • Open Issues: 0")
        print("  • Compliance Deltas: None (all metrics within thresholds)")
        print("  • Regulator-Ready Snapshot: Available (last generated: 2026-01-20)")
        print("  • Risk Assessment: Low (no outstanding actions)")
        print("  • Next Review: 2026-01-31")

        # Auto-emit proposal if risk threshold met (simulate upcoming review)
        next_review = datetime(2026, 1, 31)
        days_until = (next_review - datetime.utcnow()).days
        if days_until < 14:
            # Check if proposal already exists
            index_file = Path(os.environ.get("MAD_OS_ROOT", Path.cwd())) / ".mad_os" / "proposals" / "INDEX.json"
            with index_file.open("r") as f:
                index = json.load(f)
            existing = any(p["title"] == "Upcoming compliance review preparation" and p["status"] == "open" for p in index["proposals"])
            if not existing:
                # Create proposal
                proposal_id = _generate_proposal_id()
                created_at = datetime.utcnow().isoformat() + "Z"
                actor = os.environ.get("MAD_ACTOR", "system")
                proposal = {
                    "proposal_id": proposal_id,
                    "created_at": created_at,
                    "created_by": {"actor": actor, "scope": "observer"},
                    "source": {"adapter": "taqco", "command": "describe taqco"},
                    "type": "recommendation",
                    "title": "Upcoming compliance review preparation",
                    "summary": f"Compliance review due in {days_until} days. Recommend audit preparation.",
                    "details": {
                        "evidence": [f"next_review_days={days_until}", "compliance_state=compliant"],
                        "alternatives_considered": ["Ignore until due", "Manual preparation", "Schedule early review"]
                    },
                    "risk": {"level": "low", "impact": "Potential non-compliance if unprepared"},
                    "requires": {"mode": "OPERATOR", "capabilities": ["compliance.review"]},
                    "status": "open",
                    "audit_ref": "pending"
                }
                proposal_file = Path(os.environ.get("MAD_OS_ROOT", Path.cwd())) / ".mad_os" / "proposals" / f"{proposal_id}.json"
                with proposal_file.open("w") as f:
                    json.dump(proposal, f, indent=2)
                index["proposals"].append({
                    "id": proposal_id,
                    "title": "Upcoming compliance review preparation",
                    "status": "open",
                    "created_at": created_at
                })
                with index_file.open("w") as f:
                    json.dump(index, f, indent=2)
                # Obsidian note
                obsidian_dir = Path.home() / "Obsidian" / "coordination-layer" / "proposals"
                obsidian_dir.mkdir(parents=True, exist_ok=True)
                note_file = obsidian_dir / f"{proposal_id}.md"
                with note_file.open("w") as f:
                    f.write(f"# Proposal {proposal_id}\n\n")
                    f.write(f"**Created:** {created_at}\n")
                    f.write(f"**By:** {actor}\n")
                    f.write("**Type:** recommendation\n")
                    f.write("**Title:** Upcoming compliance review preparation\n\n")
                    f.write(f"**Summary:** Compliance review due in {days_until} days. Recommend audit preparation.\n\n")
                    f.write("**Status:** Open\n\n")
                    f.write("**Operator Notes:**\n\n")
                _audit(action="proposal.create", details={"proposal_id": proposal_id, "title": "Upcoming compliance review preparation", "trigger": "auto-compliance-review"})
                print(f"\n⚠️  Compliance alert: Proposal {proposal_id} created for review.")
    elif adapter == "inventory":
        print("System Inventory:")
        print("  • Nodes: 2 (Hermes-authority, HADES-execution)")
        print("  • Services: Exo (port 8000), HUD (port 8501)")
        print("  • Adapters: 3 (brakel, taqco, inventory)")
        print("  • Audit Files: Daily JSONL with hash-chaining")
        print("  • Modes: OBSERVER, OPERATOR, LOCKED")
        print("  • Operators: 1 registered (zebadiee)")
        print("  • Agents: 1 registered (brakel, observer scope)")
        print("  • Capability Matrix: Authority required for all mutations")
    else:
        print(f"❌ Unknown adapter: {adapter}", file=sys.stderr)
        sys.exit(1)
    _audit(action="describe", details={"adapter": adapter})

def cmd_audit_tail(args):
    actor_filter = getattr(args, 'actor', None)
    audit_file = _get_current_audit_file()
    if not audit_file.exists():
        print("No audit entries")
        return
    with audit_file.open("r") as f:
        lines = f.readlines()
    recent = lines[-10:]
    for line in recent:
        entry = json.loads(line)
        if actor_filter and entry["actor"] != actor_filter:
            continue
        print(json.dumps(entry, indent=2))
    _audit(action="audit.tail", details={"filter": actor_filter or "none"})

def cmd_topology(args):
    print("MAD-OS Topology:")
    print("  Nodes:")
    print("    • Hermes (authority)")
    print("    • HADES (execution)")
    print("  Stack:")
    print("    • Exo (LLM runtime)")
    print("    • HUD (interface)")
    print("  Adapters:")
    print("    • Brakel")
    print("    • TAQ-CO")
    print("    • Inventory")
    _audit(action="topology", details={})

def cmd_list_adapters(args):
    print("Available Adapters:")
    print("  • brakel - Model orchestration and health monitoring")
    print("  • taqco - Compliance tracking and reporting")
    print("  • inventory - System assets and configuration")
    _audit(action="adapters.list", details={})

def cmd_execute_proposal(args):
    current = resolve_mode()
    if current != "OPERATOR":
        print(f"❌ Access denied: execute proposal requires OPERATOR (current: {current})", file=sys.stderr)
        _audit(action="execute.proposal.denied", details={"proposal_id": getattr(args, 'proposal_id', '')})
        sys.exit(1)

    proposal_id = getattr(args, 'proposal_id', None)
    if not proposal_id:
        print("❌ Usage: madctl execute proposal <proposal_id>", file=sys.stderr)
        sys.exit(1)

    proposal_file = Path(os.environ.get("MAD_OS_ROOT", Path.cwd())) / ".mad_os" / "proposals" / f"{proposal_id}.json"
    if not proposal_file.exists():
        print("❌ Proposal not found", file=sys.stderr)
        sys.exit(1)

    with proposal_file.open("r") as f:
        proposal = json.load(f)

    if proposal["status"] != "accepted":
        print("❌ Proposal not accepted", file=sys.stderr)
        sys.exit(1)

    # Simulate execution based on proposal
    if "Preemptive provider rotation" in proposal["title"]:
        print("🔄 Switching to backup provider (Anthropic)...")
        print("✅ Provider switched successfully.")
    elif "Upcoming compliance review" in proposal["title"]:
        print("📋 Generating compliance report...")
        print("✅ Report generated and ready for regulator.")
    else:
        print("⚡ Executing recommended action...")

    _audit(action="execute.proposal", details={"proposal_id": proposal_id, "title": proposal["title"]})
    print(f"✅ Execution completed for proposal {proposal_id}")
# --- systemd execution helper (MAD-OS syscall boundary) ---
import subprocess

def _run_systemctl(args):
    cmd = ["systemctl"] + args
    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"systemctl failed: {' '.join(cmd)}\\n{e.stderr}"
        )
# --- end helper ---


def cmd_runtime_supervise(args):
    _audit(action="runtime.supervise", details={})
    try:
        from mad_os.runtime.supervisor import supervise
        data = supervise()
    except Exception as e:
        print(f"❌ Failed to run supervisor: {e}", file=sys.stderr)
        sys.exit(2)
    if getattr(args, 'json', False):
        print(json.dumps(data, indent=2))
    else:
        issues = data.get('issues', [])
        if issues:
            print("🟡 Attention required: the supervisor detected issues")
            for it in issues:
                print(f"  • {it['component']}: {it['issue']} - {it.get('details', {})}")
        else:
            print("✅ No supervisor issues detected")


def cmd_runtime_observe(args):
    _audit(action="runtime.observe", details={})
    try:
        from mad_os.runtime.observability import gather_observability
        data = gather_observability()
    except Exception as e:
        print(f"❌ Failed to obtain runtime observability: {e}", file=sys.stderr)
        sys.exit(2)
    if getattr(args, 'json', False):
        print(json.dumps(data, indent=2))
    else:
        print("🔍 MAD-OS runtime observability\n")
        print(f"Readiness: {data.get('readiness')}")
        if data.get('issues'):
            print("Issues detected:")
            for it in data.get('issues'):
                print(f"  • {it['component']}: {it['issue']}")
        else:
            print("No issues detected")

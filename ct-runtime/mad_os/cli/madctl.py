#!/usr/bin/env python3
import argparse
import sys

from mad_os.cli.madctl_stack import (
    cmd_stack_start,
    cmd_stack_stop,
    cmd_stack_status,
    cmd_health,
    cmd_operator_activate,
    cmd_mode_set,
    cmd_explain,
    cmd_describe,
    cmd_audit_tail,
    cmd_topology,
    cmd_list_adapters,
    cmd_execute_proposal,
)

def main():
    parser = argparse.ArgumentParser(description="MAD-OS Control Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Stack commands
    stack = subparsers.add_parser("stack", help="MAD-OS stack control")
    stack_sub = stack.add_subparsers(dest="stack_cmd", required=True)

    p_start = stack_sub.add_parser("start", help="Start MAD-OS stack")
    p_start.set_defaults(func=cmd_stack_start)

    p_stop = stack_sub.add_parser("stop", help="Stop MAD-OS stack")
    p_stop.set_defaults(func=cmd_stack_stop)

    p_status = stack_sub.add_parser("status", help="Show stack status")
    p_status.add_argument("--json", action="store_true", help="Output in JSON format")
    p_status.set_defaults(func=cmd_stack_status)

    # Health command
    health = subparsers.add_parser("health", help="Check MAD-OS health")
    health.set_defaults(func=cmd_health)

    # Operator command
    operator = subparsers.add_parser("operator", help="Operator management")
    op_sub = operator.add_subparsers(dest="op_cmd", required=True)
    p_activate = op_sub.add_parser("activate", help="Activate operator mode")
    p_activate.add_argument("token", help="Operator token")
    p_activate.set_defaults(func=cmd_operator_activate)

    # Mode command
    mode = subparsers.add_parser("mode", help="Mode management")
    mode_sub = mode.add_subparsers(dest="mode_cmd", required=True)
    p_set = mode_sub.add_parser("set", help="Set system mode")
    p_set.add_argument("mode", help="Mode to set (LOCKED)")
    p_set.set_defaults(func=cmd_mode_set)

    # Observer commands
    explain = subparsers.add_parser("explain", help="Explain an adapter")
    explain.add_argument("adapter", help="Adapter name")
    explain.set_defaults(func=cmd_explain)

    describe = subparsers.add_parser("describe", help="Describe an adapter")
    describe.add_argument("adapter", help="Adapter name")
    describe.set_defaults(func=cmd_describe)

    audit = subparsers.add_parser("audit", help="Audit operations")
    audit_sub = audit.add_subparsers(dest="audit_cmd", required=True)
    tail = audit_sub.add_parser("tail", help="Show recent audit entries")
    tail.add_argument("--actor", help="Filter by actor")
    tail.set_defaults(func=cmd_audit_tail)

    topology = subparsers.add_parser("topology", help="Show system topology")
    topology.set_defaults(func=cmd_topology)

    adapters = subparsers.add_parser("adapters", help="List available adapters")
    adapters.set_defaults(func=cmd_list_adapters)

    # Runtime commands
    runtime = subparsers.add_parser("runtime", help="MAD-OS runtime control")
    runtime_sub = runtime.add_subparsers(dest="runtime_cmd", required=True)

    p_rt_status = runtime_sub.add_parser("status", help="Show runtime status")
    p_rt_status.add_argument("--json", action="store_true", help="Output in JSON format")
    from mad_os.cli.madctl_stack import cmd_runtime_status, cmd_runtime_start, cmd_runtime_stop, cmd_runtime_restart
    p_rt_status.set_defaults(func=cmd_runtime_status)

    p_rt_start = runtime_sub.add_parser("start", help="Start a runtime component")
    p_rt_start.add_argument("component", help="Component name to start")
    p_rt_start.add_argument("--json", action="store_true", help="Output in JSON format")
    p_rt_start.set_defaults(func=cmd_runtime_start)

    p_rt_stop = runtime_sub.add_parser("stop", help="Stop a runtime component")
    p_rt_stop.add_argument("component", help="Component name to stop")
    p_rt_stop.add_argument("--json", action="store_true", help="Output in JSON format")
    p_rt_stop.set_defaults(func=cmd_runtime_stop)

    p_rt_restart = runtime_sub.add_parser("restart", help="Restart a runtime component")
    p_rt_restart.add_argument("component", help="Component name to restart")
    p_rt_restart.add_argument("--json", action="store_true", help="Output in JSON format")
    p_rt_restart.set_defaults(func=cmd_runtime_restart)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
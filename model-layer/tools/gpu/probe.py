#!/usr/bin/env python3
"""Probe GPU capabilities and print JSON summary.
Minimal, dependency-light implementation; expands when hardware is available.
"""
import json
import shutil
import subprocess

OUTPUT = {}


def run_cmd(cmd):
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL)
        return out.decode('utf-8').strip()
    except Exception:
        return None


def probe_nvidia():
    out = run_cmd('nvidia-smi --query-gpu=index,name,uuid,memory.total,driver_version --format=csv,noheader')
    if not out:
        return None
    devices = []
    for line in out.splitlines():
        parts = [p.strip() for p in line.split(',')]
        devices.append({
            'index': parts[0],
            'name': parts[1],
            'uuid': parts[2],
            'memory_total': parts[3],
            'driver': parts[4],
        })
    return {'vendor': 'nvidia', 'devices': devices}


def main():
    if shutil.which('nvidia-smi'):
        res = probe_nvidia()
        if res:
            print(json.dumps(res, indent=2))
            return 0

    # fallback signals
    if shutil.which('rocminfo'):
        print(json.dumps({'vendor': 'amd', 'devices': []}))
        return 0

    print(json.dumps({'vendor': None, 'devices': []}))
    return 2


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env bash
set -euo pipefail

# Simple GPU discovery script
# Outputs minimal CSV: index,name,uuid,memory_total_mb,driver

if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=index,name,uuid,memory.total,driver_version --format=csv,noheader
  exit 0
fi

if command -v rocminfo >/dev/null 2>&1; then
  # Basic parsing of rocminfo is left to probe.py; print a minimal marker
  echo "rocminfo: present"
  exit 0
fi

# Fallback: check for PCI devices
if command -v lspci >/dev/null 2>&1; then
  lspci | grep -i "vga\|3d\|display" || true
  exit 0
fi

echo "no-gpu-detected"
exit 2

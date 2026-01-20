#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd -P)"
SRC_DIR="$REPO_ROOT/tools/atlas"
DEST_DIR="/opt/coordination-layer/tools/atlas"

DRY_RUN=1
ASSUME_YES=0

usage(){
  cat <<EOF
Usage: $0 [--apply] [--yes]

This script installs ATLAS helper scripts to /opt/coordination-layer/tools/atlas and
ensures they are executable. Dry-run by default.
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --apply) DRY_RUN=0 ;; 
    --yes) ASSUME_YES=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1"; usage; exit 2 ;;
  esac
  shift
done

if [ "$DRY_RUN" -eq 1 ]; then
  echo "DRY RUN: would copy $SRC_DIR to $DEST_DIR"
  echo "DRY RUN: would ensure /opt/coordination-layer/tools/atlas is owned by root or ops user"
  echo "Run with --apply to perform actions."
  exit 0
fi

sudo mkdir -p "$DEST_DIR"
sudo cp -a "$SRC_DIR/"* "$DEST_DIR/"
sudo chown -R root:root "$DEST_DIR"
sudo chmod -R 0755 "$DEST_DIR"

# Verify dry-run of write_topology
sudo -u $(whoami) "$DEST_DIR/write_topology.py" --vault /tmp/atlas-dryrun --actor hermes --action "deploy-test" --dry-run

echo "Apply complete. Verify by running a dry-run against the actual ATLAS mount as the ops user."

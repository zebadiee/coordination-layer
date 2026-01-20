#!/usr/bin/env bash
set -euo pipefail

# Resolve repository root deterministically (script lives in ct-runtime/ct_server/deploy)
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd -P)"
ENV_SRC="$REPO_ROOT/ct-runtime/ct_server/deploy/ct-agent-register.env"
UNIT_SRC="$REPO_ROOT/ct-runtime/ct_server/deploy/ct-agent-register.service"
LOGROT_SRC="$REPO_ROOT/ct-runtime/ct_server/deploy/logrotate.ct-agent"

DEST_ENV="/etc/ct/agent-register.env"
DEST_UNIT="/etc/systemd/system/ct-agent-register.service"
DEST_LOGROT="/etc/logrotate.d/ct-agent"

# Runtime user/group and directories
CT_USER="ct"
CT_GROUP="ct"
LOG_DIR="/var/log/ct-agent"
CONF_DIR="/etc/ct"

DRY_RUN=1
ASSUME_YES=0

usage() {
  cat <<EOF
Usage: $0 [--apply] [--yes]

This script applies the CT Agent Register deployment to a single authority node.
By default it performs a dry-run and prints the steps. Use --apply to perform actions.
Use --yes to skip interactive confirmation.

Examples:
  $0          # dry-run
  $0 --apply   # run with prompts
  $0 --apply --yes  # run non-interactive (careful)
EOF
}

confirm() {
  if [ "$ASSUME_YES" -eq 1 ]; then
    return 0
  fi
  read -p "$1 [y/N] " -r
  case "$REPLY" in
    [Yy]*) return 0 ;;
    *) echo "Aborting."; exit 1 ;;
  esac
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

echo "[ct-agent] REPO_ROOT=$REPO_ROOT"

# Preconditions
echo "\n[ct-agent] Preconditions: whoami / hostname"
whoami || true
hostname || true

if [ "$DRY_RUN" -eq 1 ]; then
  echo "\n[ct-agent] DRY-RUN mode. No changes will be made. Re-run with --apply to execute." 
fi

# Step 1: create runtime user
echo "\n[ct-agent] Step 1: ensure runtime user 'ct' exists"
if id -u ct >/dev/null 2>&1; then
  echo " - user 'ct' exists"
else
  echo " - user 'ct' does not exist and will be created: useradd --system --home /var/lib/ct --shell /usr/sbin/nologin ct"
  if [ "$DRY_RUN" -eq 0 ]; then
    confirm "Create system user 'ct'?"
    sudo useradd --system --home /var/lib/ct --shell /usr/sbin/nologin ct
  fi
fi

# Step 2: create directories
echo "\n[ct-agent] Step 2: create directories and set ownership"
echo " - /var/lib/ct, $LOG_DIR, /etc/ct"
if [ "$DRY_RUN" -eq 0 ]; then
  sudo mkdir -p /var/lib/ct "$LOG_DIR" "$CONF_DIR"
  sudo chown -R "$CT_USER:$CT_GROUP" /var/lib/ct "$LOG_DIR" "$CONF_DIR"
fi

# Step 3: install env file
echo "\n[ct-agent] Step 3: install env file"
if [ ! -f "$ENV_SRC" ]; then
  echo "ENV source file missing: $ENV_SRC"; exit 2
fi
echo " - will copy $ENV_SRC -> $DEST_ENV (mode 0640, owner ct:ct)"
if [ "$DRY_RUN" -eq 0 ]; then
  sudo install -m 0640 -o ct -g ct "$ENV_SRC" "$DEST_ENV"
fi

# Step 4: install systemd unit
echo "\n[ct-agent] Step 4: install systemd unit"
if [ ! -f "$UNIT_SRC" ]; then
  echo "Unit file missing: $UNIT_SRC"; exit 2
fi
echo " - will copy $UNIT_SRC -> $DEST_UNIT"
if [ "$DRY_RUN" -eq 0 ]; then
  sudo install -m 0644 "$UNIT_SRC" "$DEST_UNIT"
  sudo systemctl daemon-reload
fi

# Step 5: install logrotate config
echo "\n[ct-agent] Step 5: install logrotate config"
if [ ! -f "$LOGROT_SRC" ]; then
  echo "Logrotate file missing: $LOGROT_SRC"; exit 2
fi
echo " - will copy $LOGROT_SRC -> $DEST_LOGROT"
if [ "$DRY_RUN" -eq 0 ]; then
  sudo install -m 0644 "$LOGROT_SRC" "$DEST_LOGROT"
fi

# Step 6: enable and start
echo "\n[ct-agent] Step 6: enable and start service"
if [ "$DRY_RUN" -eq 0 ]; then
  confirm "Enable and start ct-agent-register service now?"
  sudo systemctl enable ct-agent-register
  sudo systemctl start ct-agent-register
  echo " - status:"
  sudo systemctl status ct-agent-register --no-pager || true
fi

# Step 7: verify
echo "\n[ct-agent] Step 7: verification guidance"
cat <<'VER'
Check the following:
 - The unit is active and not in a restart loop: systemctl status ct-agent-register
 - Port is listening: ss -lntp | grep 7778
 - Logs: journalctl -u ct-agent-register -n 200 --no-pager
 - Audit files: ls -l /var/log/ct-agent
 - Re-register observer: run observer and confirm ACCEPTED entry in /var/log/ct-agent/registrations.log
VER

if [ "$DRY_RUN" -eq 1 ]; then
  echo "\n[ct-agent] Dry-run complete. Re-run with --apply to perform the actions." 
else
  echo "\n[ct-agent] Apply complete; run verification steps above." 
fi

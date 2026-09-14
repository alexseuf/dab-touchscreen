#!/bin/bash
set -euo pipefail

SRC_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ADMIN_USER="${OPENCLAW_ADMIN_USER:-openclaw}"
HELPER=/usr/local/sbin/openclaw-storage
SUDOERS_FILE=/etc/sudoers.d/openclaw-storage

if [ "${EUID}" -ne 0 ]; then
  echo "Please run as root" >&2
  exit 1
fi

if ! getent passwd "$ADMIN_USER" >/dev/null; then
  echo "Required OpenClaw administration user does not exist: $ADMIN_USER" >&2
  exit 1
fi

install -o root -g root -m 0755 "$SRC_DIR/scripts/openclaw-storage" "$HELPER"
install -d -o root -g root -m 0755 /mnt/openclaw-storage

cat >"$SUDOERS_FILE" <<EOF
# Managed by dab-touchscreen/OpenClaw provisioning.
# Intentionally grants only the validated storage helper, never NOPASSWD: ALL.
$ADMIN_USER ALL=(root) NOPASSWD: $HELPER *
EOF
chown root:root "$SUDOERS_FILE"
chmod 0440 "$SUDOERS_FILE"

command -v visudo >/dev/null 2>&1 || {
  echo "visudo is required" >&2
  exit 1
}
visudo -cf "$SUDOERS_FILE"

# Optional packages used by the helper. Install them automatically when apt is
# available so a newly provisioned Raspberry Pi can partition/format media.
missing=()
command -v parted >/dev/null 2>&1 || missing+=(parted)
command -v sgdisk >/dev/null 2>&1 || missing+=(gdisk)
command -v mkfs.vfat >/dev/null 2>&1 || missing+=(dosfstools)
command -v mkfs.exfat >/dev/null 2>&1 || missing+=(exfatprogs)

if ((${#missing[@]})); then
  if command -v apt-get >/dev/null 2>&1; then
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install -y "${missing[@]}"
  else
    echo "WARNING: optional storage packages missing: ${missing[*]}" >&2
  fi
fi

# Critical no-prompt preflight.
su - "$ADMIN_USER" -c "sudo -n $HELPER check"
su - "$ADMIN_USER" -c "sudo -n $HELPER list >/dev/null"

cat <<EOF
OpenClaw storage helper installed.
User: $ADMIN_USER
Helper: $HELPER
Sudoers: $SUDOERS_FILE
PASS openclaw_storage_noninteractive
EOF

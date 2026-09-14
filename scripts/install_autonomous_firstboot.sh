#!/bin/bash
set -euo pipefail

SRC_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DST=/opt/dab-touchscreen
ADMIN_USER="${OPENCLAW_ADMIN_USER:-openclaw}"
DEPLOY_HELPER=/usr/local/sbin/dab-deploy
SUDOERS_FILE=/etc/sudoers.d/dab-deploy-openclaw

if [ "${EUID}" -ne 0 ]; then
  echo "Please run as root" >&2
  exit 1
fi

if ! getent passwd "$ADMIN_USER" >/dev/null; then
  echo "Required administration user does not exist: $ADMIN_USER" >&2
  exit 1
fi

install -d -m 0755 "$DST"
rsync -a --delete --exclude '.git' --exclude 'secrets.env' "$SRC_DIR/" "$DST/"

install -d -m 0700 /etc/dab-touchscreen
install -d -m 0700 /var/lib/dab-touchscreen/backups
install -d -m 0755 /var/log/dab-touchscreen

# Local secrets are intentionally never copied into Git.
if [ ! -e /etc/dab-touchscreen/secrets.env ]; then
  install -m 0600 /dev/null /etc/dab-touchscreen/secrets.env
fi

install -m 0644 "$DST/systemd/dab-firstboot.service" /etc/systemd/system/dab-firstboot.service

# Install a root-owned, deliberately restricted maintenance helper. OpenClaw is
# NOT granted general passwordless sudo. It may invoke only this helper, whose
# own argument validation limits deployment to /opt/dab-touchscreen and an
# explicit service allowlist.
install -o root -g root -m 0755 "$SRC_DIR/scripts/dab-deploy" "$DEPLOY_HELPER"
cat >"$SUDOERS_FILE" <<EOF
# Managed by dab-touchscreen provisioning. Do not grant broad NOPASSWD sudo.
$ADMIN_USER ALL=(root) NOPASSWD: $DEPLOY_HELPER *
EOF
chmod 0440 "$SUDOERS_FILE"
chown root:root "$SUDOERS_FILE"

if command -v visudo >/dev/null 2>&1; then
  visudo -cf "$SUDOERS_FILE"
else
  echo "visudo is required to validate $SUDOERS_FILE" >&2
  exit 1
fi

# OpenClaw wrapper placeholders. During SSD preparation OpenClaw shall replace
# their bodies with calls to the locally installed OpenClaw instance and its
# already configured primary messaging channel.
cat >/usr/local/bin/dab-openclaw-stage <<'EOF'
#!/bin/bash
set -euo pipefail
STAGE="${1:?stage required}"
# Provisioner: replace this placeholder with the local OpenClaw CLI/API call.
# It must ask OpenClaw to implement exactly the requested stage from
# /opt/dab-touchscreen/COMMISSIONING.md and then return an exit status.
echo "OpenClaw stage hook not yet wired: stage $STAGE" >&2
exit 3
EOF
chmod 0755 /usr/local/bin/dab-openclaw-stage

cat >/usr/local/bin/dab-openclaw-report <<'EOF'
#!/bin/bash
set -euo pipefail
MSG="${1:?message required}"
# Provisioner: replace with the configured OpenClaw messaging channel.
logger -t dab-openclaw-report -- "$MSG"
EOF
chmod 0755 /usr/local/bin/dab-openclaw-report

systemctl daemon-reload
systemctl enable dab-firstboot.service

# Critical autonomy preflight: this must succeed non-interactively. Otherwise
# the SSD must not be declared ready, because later project updates would stall
# at a sudo password prompt.
su - "$ADMIN_USER" -c "sudo -n $DEPLOY_HELPER check"

echo "Autonomous DAB commissioning prepared."
echo "Restricted passwordless deployment helper installed and verified for: $ADMIN_USER"
echo "IMPORTANT: Wire /usr/local/bin/dab-openclaw-stage and dab-openclaw-report"
echo "to the local OpenClaw installation BEFORE moving the SSD to the target Pi."

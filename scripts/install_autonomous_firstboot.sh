#!/bin/bash
set -euo pipefail

SRC_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DST=/opt/dab-touchscreen

if [ "${EUID}" -ne 0 ]; then
  echo "Please run as root" >&2
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

echo "Autonomous DAB commissioning prepared."
echo "IMPORTANT: Wire /usr/local/bin/dab-openclaw-stage and dab-openclaw-report"
echo "to the local OpenClaw installation BEFORE moving the SSD to the target Pi."

#!/bin/sh
set -eu

USER_NAME=${1:-dab}
HOME_DIR=$(getent passwd "$USER_NAME" | cut -d: -f6)
[ -n "$HOME_DIR" ] || HOME_DIR="/home/$USER_NAME"

# This script runs as root during installation, before LightDM is restarted.
# Do not start Wayland clients here: labwc supplies WAYLAND_DISPLAY and
# XDG_RUNTIME_DIR only inside the graphical session.

# Raspberry Pi Squeekboard uses the system keyboard directory. Back up the
# distribution layouts once and install the DAB wide German layout there.
SYSTEM_LAYOUT_DIR=/usr/share/misc/squeekboard/keyboards
install -d -m 0755 "$SYSTEM_LAYOUT_DIR"
for layout in de.yaml de_wide.yaml; do
    if [ -f "$SYSTEM_LAYOUT_DIR/$layout" ] && [ ! -f "$SYSTEM_LAYOUT_DIR/$layout.dab-stock" ]; then
        cp -a "$SYSTEM_LAYOUT_DIR/$layout" "$SYSTEM_LAYOUT_DIR/$layout.dab-stock"
    fi
    install -o root -g root -m 0644 "/opt/dab-touchscreen/system/squeekboard/$layout" "$SYSTEM_LAYOUT_DIR/$layout"
done

# Keep an exact user copy for diagnostics.
USER_LAYOUT_DIR="$HOME_DIR/.local/share/squeekboard/keyboards"
install -d -o "$USER_NAME" -g "$USER_NAME" -m 0755 "$USER_LAYOUT_DIR"
for layout in de.yaml de_wide.yaml; do
    install -o "$USER_NAME" -g "$USER_NAME" -m 0644 "/opt/dab-touchscreen/system/squeekboard/$layout" "$USER_LAYOUT_DIR/$layout"
done

# WayVNC configuration. It is started later from dab-wayland-app.sh, where the
# actual Wayland session variables are already present.
install -d -o "$USER_NAME" -g "$USER_NAME" -m 0700 "$HOME_DIR/.config/wayvnc"
cat >"$HOME_DIR/.config/wayvnc/config" <<'EOF'
address=0.0.0.0
port=5900
enable_auth=false
xkb_layout=de
EOF
chown "$USER_NAME:$USER_NAME" "$HOME_DIR/.config/wayvnc/config"
chmod 0600 "$HOME_DIR/.config/wayvnc/config"

# Preserve the existing Raspberry Pi panel configuration. Previous TEST builds
# attempted to invent panel keys and restart the panel from the application;
# that is intentionally removed here.

echo "DAB_TOUCH_DESKTOP_TEST_PASS"

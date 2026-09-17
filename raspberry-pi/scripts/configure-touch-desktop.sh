#!/bin/sh
set -eu

USER_NAME=${1:-dab}
HOME_DIR=$(getent passwd "$USER_NAME" | cut -d: -f6)
[ -n "$HOME_DIR" ] || HOME_DIR="/home/$USER_NAME"

# TEST: German Squeekboard layout with the stock key count, but larger outlines.
# This uses much more of the 800 px display width without adding a fifth column
# or a DAB-specific hide key.
install -d -m 0755 "$HOME_DIR/.local/share/squeekboard/keyboards"
for layout in de.yaml de_wide.yaml; do
    install -m 0644 "/opt/dab-touchscreen/system/squeekboard/$layout" \
        "$HOME_DIR/.local/share/squeekboard/keyboards/$layout"
done

# Force the Raspberry Pi panel to the top layer and keep it visible. The
# wfplug-squeek plugin supplies Raspberry Pi OS' native keyboard show/hide icon.
python3 - "$HOME_DIR" <<'PY'
from pathlib import Path
import configparser
import sys

home = Path(sys.argv[1])
paths = [home / ".config/wf-panel-pi.ini", home / ".config/wf-panel-pi/wf-panel-pi.ini"]
for path in paths:
    path.parent.mkdir(parents=True, exist_ok=True)
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.optionxform = str
    if path.exists():
        cfg.read(path, encoding="utf-8")
    if not cfg.has_section("panel"):
        cfg.add_section("panel")
    cfg.set("panel", "autohide", "false")
    cfg.set("panel", "minimal_height", "36")
    cfg.set("panel", "position", "top")
    cfg.set("panel", "layer", "top")
    right = cfg.get("panel", "widgets_right", fallback="").split()
    if "squeek" not in right:
        right.append("squeek")
    cfg.set("panel", "widgets_right", " ".join(right))
    with path.open("w", encoding="utf-8") as handle:
        cfg.write(handle, space_around_delimiters=True)
PY

# TEST remote access: WayVNC exposes the active Wayland desktop on TCP/5900.
# Authentication is intentionally disabled for this hardware test so RealVNC
# Viewer can connect without certificate setup. Use only on a trusted LAN.
install -d -m 0700 "$HOME_DIR/.config/wayvnc"
cat >"$HOME_DIR/.config/wayvnc/config" <<'EOF'
address=0.0.0.0
port=5900
enable_auth=false
xkb_layout=de
EOF

chown -R "$USER_NAME:$USER_NAME" "$HOME_DIR/.local/share/squeekboard" "$HOME_DIR/.config/wayvnc" 2>/dev/null || true
chown -R "$USER_NAME:$USER_NAME" "$HOME_DIR/.config/wf-panel-pi" 2>/dev/null || true
chown "$USER_NAME:$USER_NAME" "$HOME_DIR/.config/wf-panel-pi.ini" 2>/dev/null || true

# The panel is normally started before the DAB autostart entry. Restart it once
# so the TEST settings above are applied immediately instead of only next boot.
if command -v wf-panel-pi >/dev/null 2>&1; then
    pkill -x wf-panel-pi 2>/dev/null || true
    (nohup wf-panel-pi >/dev/null 2>&1 &) || true
fi

if command -v wayvnc >/dev/null 2>&1 && ! pgrep -x wayvnc >/dev/null 2>&1; then
    (nohup wayvnc --config="$HOME_DIR/.config/wayvnc/config" >"$HOME_DIR/.local/state/dab-touchscreen/wayvnc.log" 2>&1 &) || true
fi

echo "DAB_TOUCH_DESKTOP_TEST_PASS"

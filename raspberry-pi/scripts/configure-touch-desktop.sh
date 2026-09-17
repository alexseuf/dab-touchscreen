#!/bin/sh
set -eu

USER_NAME=${1:-dab}
HOME_DIR=$(getent passwd "$USER_NAME" | cut -d: -f6)
[ -n "$HOME_DIR" ] || HOME_DIR="/home/$USER_NAME"
LAYOUT_DIR="$HOME_DIR/.local/share/squeekboard/keyboards"
STATE_DIR="$HOME_DIR/.local/state/dab-touchscreen"
mkdir -p "$LAYOUT_DIR" "$STATE_DIR"

# Install the DAB layouts. The actual Squeekboard process is normally owned by
# the desktop session, so its environment must be set before that process is
# spawned; merely starting a second Squeekboard instance is not reliable.
for layout in de.yaml de_wide.yaml; do
    install -m 0644 "/opt/dab-touchscreen/system/squeekboard/$layout" "$LAYOUT_DIR/$layout"
done
chown -R "$USER_NAME:$USER_NAME" "$HOME_DIR/.local/share/squeekboard" "$STATE_DIR"

# Also place the layouts in Raspberry Pi Squeekboard's compiled-in fallback
# directory. This makes the TEST independent of how the desktop launches OSK.
if [ -d /usr/share/misc/squeekboard/keyboards ]; then
    for layout in de.yaml de_wide.yaml; do
        cp "/opt/dab-touchscreen/system/squeekboard/$layout" "/usr/share/misc/squeekboard/keyboards/$layout"
    done
fi

# Keep the panel visible and request the native Squeekboard toggle plugin.
python3 - "$HOME_DIR" <<'PY'
from pathlib import Path
import configparser, sys
home=Path(sys.argv[1])
for path in [home/'.config/wf-panel-pi.ini', home/'.config/wf-panel-pi/wf-panel-pi.ini']:
    path.parent.mkdir(parents=True, exist_ok=True)
    cfg=configparser.ConfigParser(interpolation=None); cfg.optionxform=str
    if path.exists(): cfg.read(path, encoding='utf-8')
    if not cfg.has_section('panel'): cfg.add_section('panel')
    cfg.set('panel','autohide','false'); cfg.set('panel','minimal_height','36')
    cfg.set('panel','position','top'); cfg.set('panel','layer','overlay')
    right=cfg.get('panel','widgets_right',fallback='').split()
    if 'squeek' not in right: right.append('squeek')
    cfg.set('panel','widgets_right',' '.join(right))
    with path.open('w',encoding='utf-8') as f: cfg.write(f,space_around_delimiters=True)
PY

# WayVNC: always restart it after an update. The previous TEST only started it
# when no process existed; a stale/failed process could therefore leave 5900
# unavailable after the firmware update.
install -d -m 0700 "$HOME_DIR/.config/wayvnc"
cat >"$HOME_DIR/.config/wayvnc/config" <<'EOF'
address=0.0.0.0
port=5900
enable_auth=false
xkb_layout=de
EOF
chown -R "$USER_NAME:$USER_NAME" "$HOME_DIR/.config/wayvnc" "$STATE_DIR" 2>/dev/null || true
chown -R "$USER_NAME:$USER_NAME" "$HOME_DIR/.config/wf-panel-pi" 2>/dev/null || true
chown "$USER_NAME:$USER_NAME" "$HOME_DIR/.config/wf-panel-pi.ini" 2>/dev/null || true

if command -v wf-panel-pi >/dev/null 2>&1; then
    pkill -x wf-panel-pi 2>/dev/null || true
    (nohup wf-panel-pi >"$STATE_DIR/wf-panel.log" 2>&1 &) || true
fi

if command -v wayvnc >/dev/null 2>&1; then
    pkill -x wayvnc 2>/dev/null || true
    sleep 1
    (nohup wayvnc --config="$HOME_DIR/.config/wayvnc/config" >"$STATE_DIR/wayvnc.log" 2>&1 &) || true
fi

echo "DAB_TOUCH_DESKTOP_TEST_PASS"

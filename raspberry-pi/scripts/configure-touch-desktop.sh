#!/bin/sh
set -eu

USER_NAME=${1:-dab}
HOME_DIR=$(getent passwd "$USER_NAME" | cut -d: -f6)
[ -n "$HOME_DIR" ] || HOME_DIR="/home/$USER_NAME"

# Use Raspberry Pi OS' stock German Squeekboard layout. Earlier DAB builds
# overrode de/de_wide with an extra key; that adds another column and makes
# every character key narrower on an 800 px display.
rm -f "$HOME_DIR/.local/share/squeekboard/keyboards/de.yaml" \
      "$HOME_DIR/.local/share/squeekboard/keyboards/de_wide.yaml"

# Keep the Raspberry Pi panel visible in this TEST build. wfplug-squeek then
# provides the native keyboard icon in the top bar, including the supported
# show/hide path for Squeekboard. The panel reserves its own area, so a
# maximized DAB window stays below it instead of covering it.
python3 - "$HOME_DIR" <<'PY'
from pathlib import Path
import configparser
import sys

home = Path(sys.argv[1])
paths = [
    home / ".config/wf-panel-pi/wf-panel-pi.ini",
    home / ".config/wf-panel-pi.ini",
]
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
    right = cfg.get("panel", "widgets_right", fallback="").split()
    if "squeek" not in right:
        right.append("squeek")
    cfg.set("panel", "widgets_right", " ".join(right))
    with path.open("w", encoding="utf-8") as handle:
        cfg.write(handle, space_around_delimiters=True)
PY

chown -R "$USER_NAME:$USER_NAME" "$HOME_DIR/.config/wf-panel-pi" 2>/dev/null || true
chown "$USER_NAME:$USER_NAME" "$HOME_DIR/.config/wf-panel-pi.ini" 2>/dev/null || true

echo "DAB_TOUCH_DESKTOP_TEST_PASS"

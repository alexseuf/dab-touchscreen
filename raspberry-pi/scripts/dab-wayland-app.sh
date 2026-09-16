#!/bin/sh
set -eu

STATE_DIR="$HOME/.local/state/dab-touchscreen"
mkdir -p "$STATE_DIR"
exec >>"$STATE_DIR/wayland-kiosk.log" 2>&1

export QT_QPA_PLATFORM=wayland
if [ -r /etc/dab-touchscreen/env ]; then
    set -a
    . /etc/dab-touchscreen/env
    set +a
fi

# labwc and wf-panel-pi are started by the Raspberry Pi OS session. Give the
# compositor a moment to publish its output and input-method interfaces.
sleep 2

# Preserve the physical installation's 180-degree display orientation. The
# installed autotouch helper associates the touchscreen with this transform.
if command -v wlr-randr >/dev/null 2>&1; then
    wlr-randr | awk '/^[^[:space:]]/{print $1}' | while read -r output; do
        [ -n "$output" ] && wlr-randr --output "$output" --transform 180 || true
    done
fi

cd /opt/dab-touchscreen
exec /usr/bin/python3 -m src.main --stage 8

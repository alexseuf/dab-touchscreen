#!/bin/sh
set -eu

STATE_DIR="$HOME/.local/state/dab-touchscreen"
mkdir -p "$STATE_DIR"
exec >>"$STATE_DIR/wayland-kiosk.log" 2>&1

export QT_QPA_PLATFORM=wayland
export QT_IM_MODULE=wayland
if [ -r /etc/dab-touchscreen/env ]; then
    set -a
    . /etc/dab-touchscreen/env
    set +a
fi

# This autostart entry is executed inside LXDE-pi-labwc, so WAYLAND_DISPLAY and
# XDG_RUNTIME_DIR are available here. Start WayVNC in exactly this environment.
if command -v wayvnc >/dev/null 2>&1; then
    pkill -x wayvnc 2>/dev/null || true
    nohup wayvnc --config="$HOME/.config/wayvnc/config" >"$STATE_DIR/wayvnc.log" 2>&1 &
fi

# Squeekboard is already managed by the Raspberry Pi desktop session. The TEST
# layout was installed into its real system keyboard directory before LightDM
# restarted, so do not kill/restart Squeekboard from the DAB application.

sleep 2
if command -v wlr-randr >/dev/null 2>&1; then
    wlr-randr | awk '/^[^[:space:]]/{print $1}' | while read -r output; do
        [ -n "$output" ] && wlr-randr --output "$output" --transform 180 || true
    done
fi

cd /opt/dab-touchscreen
exec /usr/bin/python3 -m src.main --stage 8

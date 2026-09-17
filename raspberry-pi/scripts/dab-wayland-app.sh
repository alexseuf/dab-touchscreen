#!/bin/sh
set -eu

STATE_DIR="$HOME/.local/state/dab-touchscreen"
mkdir -p "$STATE_DIR"
exec >>"$STATE_DIR/wayland-kiosk.log" 2>&1

export QT_QPA_PLATFORM=wayland
# Explicitly use the Wayland input-method path. On the kiosk image this avoids
# numeric/symbol pages of the on-screen keyboard being visible while their key
# events fail to reach the focused Qt line edit.
export QT_IM_MODULE=wayland
if [ -r /etc/dab-touchscreen/env ]; then
    set -a
    . /etc/dab-touchscreen/env
    set +a
fi

# TEST touch behaviour: use Raspberry Pi OS' native wf-panel-pi + wfplug-squeek
# control and remove the old DAB Squeekboard override. This makes the stock
# keyboard wider and exposes the native keyboard show/hide icon in the panel.
/opt/dab-touchscreen/scripts/configure-touch-desktop.sh "$(id -un)" || true

sleep 2
if command -v wlr-randr >/dev/null 2>&1; then
    wlr-randr | awk '/^[^[:space:]]/{print $1}' | while read -r output; do
        [ -n "$output" ] && wlr-randr --output "$output" --transform 180 || true
    done
fi

cd /opt/dab-touchscreen
exec /usr/bin/python3 -m src.main --stage 8

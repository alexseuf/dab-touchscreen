#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
INSTALL_DIR=/opt/dab-touchscreen
SERVICE_USER=dab
ENV_DIR=/etc/dab-touchscreen
RUN_APT=1
RESTART_DISPLAY=1

for arg in "$@"; do
    case "$arg" in
        --no-apt) RUN_APT=0 ;;
        --no-restart) RESTART_DISPLAY=0 ;;
        *) echo "Unbekannte Option: $arg" >&2; exit 2 ;;
    esac
done

if [[ ${EUID} -ne 0 ]]; then echo "Bitte mit sudo ausführen: sudo ./install.sh" >&2; exit 1; fi
. /etc/os-release
[[ ${VERSION_CODENAME:-} == bookworm ]] || echo "WARNUNG: Getestet wurde Raspberry Pi OS Bookworm; erkannt: ${PRETTY_NAME:-unbekannt}" >&2

PACKAGES=(network-manager policykit-1 dbus-user-session mosquitto mosquitto-clients python3 python3-yaml python3-pyqt5 python3-pyqtgraph python3-paho-mqtt sqlite3 lightdm labwc xwayland wf-panel-pi wfplug-squeek squeekboard wayvnc qtwayland5 wlr-randr autotouch raspberrypi-ui-mods fonts-dejavu-core avahi-daemon rsync ca-certificates util-linux)
if (( RUN_APT )); then apt-get update; DEBIAN_FRONTEND=noninteractive apt-get install -y "${PACKAGES[@]}"; fi
DEBIAN_FRONTEND=noninteractive apt-get remove -y lxplug-updater wfplug-updater 2>/dev/null || true

if ! id "$SERVICE_USER" >/dev/null 2>&1; then useradd --create-home --shell /bin/bash "$SERVICE_USER"; fi
for group in audio video input render netdev; do getent group "$group" >/dev/null && usermod -a -G "$group" "$SERVICE_USER"; done

install -d -o root -g root -m 0755 "$INSTALL_DIR"
if [[ $ROOT_DIR != "$INSTALL_DIR" ]]; then rsync -a --delete --exclude=.git --exclude=secrets.env --exclude='__pycache__' --exclude='*.pyc' "$ROOT_DIR/" "$INSTALL_DIR/"; fi
chown -R root:root "$INSTALL_DIR"
chmod 0755 "$INSTALL_DIR/install.sh" "$INSTALL_DIR/update.sh" "$INSTALL_DIR/uninstall.sh" "$INSTALL_DIR/scripts/"*.sh "$INSTALL_DIR/scripts/mqtt_simulator.py"
install -d -o "$SERVICE_USER" -g "$SERVICE_USER" -m 0750 /var/lib/dab-touchscreen
install -d -o root -g "$SERVICE_USER" -m 0750 "$ENV_DIR"

DAB_ENABLE_SIMULATOR=0
DAB_MQTT_LISTEN_ADDRESS=0.0.0.0
DAB_MQTT_USERNAME=
DAB_MQTT_PASSWORD=
if [[ -f "$ROOT_DIR/secrets.env" ]]; then . "$ROOT_DIR/secrets.env"; fi
DAB_ENABLE_SIMULATOR=0

python3 - "${DAB_MQTT_LISTEN_ADDRESS:-0.0.0.0}" <<'PY'
import ipaddress, sys
ipaddress.ip_address(sys.argv[1])
PY
for value in "${DAB_MQTT_USERNAME:-}" "${DAB_MQTT_PASSWORD:-}"; do
    if [[ -n $value && ! $value =~ ^[A-Za-z0-9._@%+=:-]+$ ]]; then echo "MQTT-Zugangsdaten dürfen nur A-Z, a-z, 0-9 und ._@%+=:- enthalten" >&2; exit 1; fi
done
if [[ -n ${DAB_MQTT_USERNAME:-} || -n ${DAB_MQTT_PASSWORD:-} ]]; then
    [[ -n ${DAB_MQTT_USERNAME:-} && -n ${DAB_MQTT_PASSWORD:-} ]] || { echo "DAB_MQTT_USERNAME und DAB_MQTT_PASSWORD müssen gemeinsam gesetzt werden" >&2; exit 1; }
    ALLOW_ANONYMOUS=false; PASSWORD_DIRECTIVE='password_file /etc/mosquitto/dab-touchscreen.passwd'; umask 077; mosquitto_passwd -b -c /etc/mosquitto/dab-touchscreen.passwd "$DAB_MQTT_USERNAME" "$DAB_MQTT_PASSWORD"; chown root:mosquitto /etc/mosquitto/dab-touchscreen.passwd; chmod 0640 /etc/mosquitto/dab-touchscreen.passwd
else
    ALLOW_ANONYMOUS=true; PASSWORD_DIRECTIVE=; rm -f /etc/mosquitto/dab-touchscreen.passwd
fi

umask 027
{
 printf 'DAB_ENABLE_SIMULATOR=0\n'
 printf 'DAB_MQTT_LISTEN_ADDRESS=%s\n' "${DAB_MQTT_LISTEN_ADDRESS:-0.0.0.0}"
 printf 'DAB_MQTT_USERNAME=%s\n' "${DAB_MQTT_USERNAME:-}"
 printf 'DAB_MQTT_PASSWORD=%s\n' "${DAB_MQTT_PASSWORD:-}"
} >"$ENV_DIR/env"
chown root:"$SERVICE_USER" "$ENV_DIR/env"; chmod 0640 "$ENV_DIR/env"

sed -e "s/__LISTEN_ADDRESS__/${DAB_MQTT_LISTEN_ADDRESS:-0.0.0.0}/" -e "s/__ALLOW_ANONYMOUS__/$ALLOW_ANONYMOUS/" -e "s|__PASSWORD_FILE__|$PASSWORD_DIRECTIVE|" "$ROOT_DIR/system/mosquitto-dab.conf" >/etc/mosquitto/conf.d/dab-touchscreen.conf
chown root:root /etc/mosquitto/conf.d/dab-touchscreen.conf; chmod 0644 /etc/mosquitto/conf.d/dab-touchscreen.conf

install -o root -g root -m 0644 "$ROOT_DIR/systemd/dab-mqtt-simulator.service" /etc/systemd/system/dab-mqtt-simulator.service
install -o root -g root -m 0644 "$ROOT_DIR/system/lightdm-dab-touchscreen.conf" /etc/lightdm/lightdm.conf.d/50-dab-touchscreen.conf
install -o root -g root -m 0644 "$ROOT_DIR/system/dab-touchscreen.desktop" /etc/xdg/autostart/dab-touchscreen.desktop
install -o root -g root -m 0644 "$ROOT_DIR/system/40-dab-touchscreen-rotate.conf" /etc/X11/xorg.conf.d/40-dab-touchscreen-rotate.conf
install -o root -g root -m 0644 "$ROOT_DIR/system/49-dab-networkmanager.rules" /etc/polkit-1/rules.d/49-dab-networkmanager.rules
install -o root -g root -m 0644 "$ROOT_DIR/system/49-dab-firmware-update.rules" /etc/polkit-1/rules.d/49-dab-firmware-update.rules

# Install the DAB German Squeekboard layouts. The TEST branch keeps the normal
# key count but uses larger outlines to make better use of the 800 px width.
install -d -o "$SERVICE_USER" -g "$SERVICE_USER" -m 0755 "/home/$SERVICE_USER/.local/share/squeekboard/keyboards"
for layout in de.yaml de_wide.yaml; do
    install -o "$SERVICE_USER" -g "$SERVICE_USER" -m 0644 "$ROOT_DIR/system/squeekboard/$layout" "/home/$SERVICE_USER/.local/share/squeekboard/keyboards/$layout"
done

install -d -o "$SERVICE_USER" -g "$SERVICE_USER" -m 0755 "/home/$SERVICE_USER/.config"
cat >"/home/$SERVICE_USER/.config/labwc-autostart-notifications-disabled" <<'EOF'
# DAB kiosk marker: desktop notification bubbles intentionally disabled.
EOF
chown "$SERVICE_USER:$SERVICE_USER" "/home/$SERVICE_USER/.config/labwc-autostart-notifications-disabled"
install -d -o "$SERVICE_USER" -g "$SERVICE_USER" -m 0755 "/home/$SERVICE_USER/.config/autostart"
for desktop in lxpolkit-notify.desktop nm-applet.desktop; do
 cat >"/home/$SERVICE_USER/.config/autostart/$desktop" <<EOF
[Desktop Entry]
Type=Application
Name=DAB kiosk suppression
Hidden=true
EOF
 chown "$SERVICE_USER:$SERVICE_USER" "/home/$SERVICE_USER/.config/autostart/$desktop"
done

python3 -m compileall -q "$INSTALL_DIR/src" "$INSTALL_DIR/scripts"
(cd "$INSTALL_DIR"; PYTHONPATH="$INSTALL_DIR${PYTHONPATH:+:$PYTHONPATH}" python3 -m unittest discover -s tests -v)
systemctl daemon-reload
systemctl enable NetworkManager.service mosquitto.service lightdm.service
systemctl disable --now dab-touchscreen.service 2>/dev/null || true
systemctl disable --now dab-mqtt-simulator.service 2>/dev/null || true
pkill -f '/opt/dab-touchscreen/scripts/mqtt_simulator.py' 2>/dev/null || true
systemctl restart mosquitto.service
systemctl set-default graphical.target
if (( RESTART_DISPLAY )); then systemctl restart lightdm.service; fi

echo "DAB_INSTALL_PASS"
echo "Installation: $INSTALL_DIR"
echo "Konfiguration: $ENV_DIR/env (root:$SERVICE_USER, 0640)"

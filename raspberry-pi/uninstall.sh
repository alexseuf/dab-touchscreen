#!/usr/bin/env bash
set -Eeuo pipefail

PURGE_DATA=0
REMOVE_USER=0
for arg in "$@"; do
    case "$arg" in
        --purge-data) PURGE_DATA=1 ;;
        --remove-user) REMOVE_USER=1 ;;
        *) echo "Unbekannte Option: $arg" >&2; exit 2 ;;
    esac
done
if [[ ${EUID} -ne 0 ]]; then echo "Bitte mit sudo ausführen" >&2; exit 1; fi

systemctl disable --now dab-mqtt-simulator.service 2>/dev/null || true
rm -f /etc/systemd/system/dab-mqtt-simulator.service
rm -f /etc/xdg/autostart/dab-touchscreen.desktop
rm -f /etc/lightdm/lightdm.conf.d/50-dab-touchscreen.conf
rm -f /etc/X11/xorg.conf.d/40-dab-touchscreen-rotate.conf
rm -f /etc/polkit-1/rules.d/49-dab-networkmanager.rules
rm -f /etc/mosquitto/conf.d/dab-touchscreen.conf /etc/mosquitto/dab-touchscreen.passwd
rm -rf /opt/dab-touchscreen
if (( PURGE_DATA )); then rm -rf /var/lib/dab-touchscreen /etc/dab-touchscreen; fi
if (( REMOVE_USER )) && id dab >/dev/null 2>&1; then userdel -r dab || true; fi
systemctl daemon-reload
systemctl restart mosquitto.service 2>/dev/null || true
systemctl restart lightdm.service 2>/dev/null || true
echo "DAB_UNINSTALL_PASS"

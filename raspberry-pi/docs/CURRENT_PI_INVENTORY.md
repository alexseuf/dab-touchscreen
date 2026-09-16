# Inventar des verifizierten Raspberry-Pi-Stands

Erfasst am 16.09.2026 vom laufenden DAB-Touchscreen-Pi, ohne Secret-Inhalte oder
NetworkManager-Verbindungsdateien auszulesen.

## Plattform

- Raspberry Pi 4 Model B Rev 1.5
- Debian/Raspberry Pi OS Bookworm 12, arm64
- Kernel `6.12.96+rpt-rpi-v8`
- Display-Ausgang `DSI-1`, 800×480, Laufzeitausrichtung 180° per `wlr-randr`
- Touch-Ausrichtung über `autotouch`; X11-Fallback über TransformationMatrix

## Aktiver Laufzeitpfad

1. `lightdm.service` meldet Benutzer `dab` automatisch an.
2. Sitzung `LXDE-pi-labwc` startet labwc/Wayland und `wf-panel-pi`.
3. XDG-Autostart ruft `scripts/dab-wayland-app.sh` auf.
4. Das Skript setzt `QT_QPA_PLATFORM=wayland`, dreht Ausgaben um 180° und startet
   `python3 -m src.main --stage 8`.
5. Squeekboard wird über D-Bus von der Anwendung ein-/ausgeblendet.

Der vorhandene X11-Dienst `dab-touchscreen.service` war deaktiviert und ist nur
ein historischer Fallback. Das eigenständige Repository installiert ihn nicht.

## Aktive Dienste

- `lightdm.service`: enabled/active
- `NetworkManager.service`: enabled/active
- `mosquitto.service`: enabled/active
- `dab-mqtt-simulator.service`: enabled/active
- `dab-touchscreen.service`: disabled

## Relevante Paketversionen des Referenzgeräts

- `network-manager 1.42.4-1+rpt1+deb12u1`
- `mosquitto 2.0.11-1.2+deb12u2`
- `python3 3.11.2-1+b1`
- `python3-pyqt5 5.15.9+dfsg-1`
- `python3-pyqtgraph 0.13.1-4`
- `python3-paho-mqtt 1.6.1-1`
- `python3-yaml 6.0-3+b2`
- `sqlite3 3.40.1-2+deb12u2`
- `lightdm 1.26.0-8+rpt5`
- `labwc 0.8.4-1+rpt1`
- `wf-panel-pi 0.102`
- `wfplug-squeek 0.6`
- `squeekboard 1.21.0-1+rpt11`
- `qtwayland5 5.15.8-2`
- `wlr-randr 0.2.0-2+rpt1`
- `autotouch 0.1`
- `raspberrypi-ui-mods 1.20250506`
- `fonts-dejavu-core 2.37-6`
- `avahi-daemon 0.8-10+deb12u1`

## Projektbezogene Dateien des untersuchten Systems

- `/opt/dab-touchscreen`: Anwendung, Konfiguration, Simulator und ältere
  Provisionierungsdokumente/-skripte
- `/etc/lightdm/lightdm.conf.d/50-dab-touchscreen.conf`
- `/etc/systemd/system/dab-mqtt-simulator.service`
- `/etc/systemd/system/dab-firstboot.service` (historische OpenClaw-Provisionierung)
- `/etc/systemd/system/dab-touchscreen.service` (deaktivierter X11-Fallback)
- `/etc/X11/xorg.conf.d/40-dab-touchscreen-rotate.conf`
- lokale NetworkManager-/Polkit-Konfiguration

Historische OpenClaw-, Flash-, Offline-Chroot- und SSD-Provisionierungsdateien
sind nicht Teil der neuen Laufzeitinstallation. Ihre Ergebnisse wurden in
`install.sh` überführt. Dadurch ist das neue Repository unabhängig von OpenClaw.

## Netzwerk- und Secret-Befund

- Ethernet und WLAN werden durch NetworkManager verwaltet.
- Die Anwendung kann DHCP/feste Ethernet-IPv4, Prefix, Gateway und DNS setzen.
- WLAN-Profile bleiben ausschließlich im NetworkManager Secret Store.
- Mosquitto lief lokal auf Port 1883.
- Keine WLAN-Schlüssel, Passwörter, Tokens, API-Keys oder privaten SSH-Schlüssel
  wurden in dieses Repository übernommen.
- OpenClaw 2026.9.4 und Node.js 24.21.0 waren installiert, sind jedoch keine
  Laufzeitabhängigkeiten der DAB-HMI.

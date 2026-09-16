# DAB Touchscreen – eigenständige Raspberry-Pi-Installation

Dieses Repository installiert den aktuell funktionierenden Stand der DAB-HMI auf
einem frisch installierten **Raspberry Pi OS Bookworm Desktop 64-bit**. OpenClaw
wird weder für Installation noch Betrieb benötigt.

Zielhardware des verifizierten Systems:

- Raspberry Pi 4 Model B
- offizielles Raspberry-Pi-7-Zoll-Touchdisplay, 800×480, um 180° montiert
- Raspberry Pi OS Bookworm arm64
- Ethernet und/oder WLAN über NetworkManager

## Funktionen

- Qt/PyQt5-HMI mit Übersicht, zoombaren Verläufen, MQTT Explorer und Einstellungs-Untermenü
- Squeekboard-Touch-Tastatur unter labwc/Wayland
- Display- und Touch-Ausrichtung um 180°
- DHCP oder feste LAN-Adresse mit Prefix, Gateway, DNS, Validierung und Rollback
- WLAN-Scan, Passwort-Eingabe und Statusanzeige
- lokaler Mosquitto-Broker; LAN-Adresse wird in der HMI bevorzugt
- optionale, abschaltbare MQTT-Demosignale
- SQLite-Historie unter `/var/lib/dab-touchscreen`
- Autostart über LightDM und systemweites XDG-Autostart

## Schnellinstallation

1. Raspberry Pi OS Bookworm Desktop 64-bit installieren und starten.
2. Dieses Repository lokal auf den Pi kopieren oder klonen.
3. Optional `secrets.env.example` nach `secrets.env` kopieren und anpassen.
4. Installieren:

```bash
chmod +x install.sh update.sh uninstall.sh
sudo ./install.sh
```

Am Ende muss `DAB_INSTALL_PASS` erscheinen. LightDM wird neu gestartet und meldet
den eigens angelegten Benutzer `dab` automatisch in der Wayland-Sitzung an.

Nützliche Optionen:

```bash
sudo ./install.sh --no-restart  # Display-Sitzung nicht sofort neu starten
sudo ./install.sh --no-apt      # Pakete nicht erneut prüfen/installieren
```

`install.sh` ist idempotent: wiederholte Ausführung aktualisiert Dateien,
Berechtigungen, Konfiguration und Services auf denselben Sollzustand.

## Aktualisieren

Im aktualisierten Repository-Checkout:

```bash
./update.sh
```

Das Skript verwendet den gleichen idempotenten Installer, überspringt aber
`apt-get`. Für neue Paketabhängigkeiten stattdessen erneut `sudo ./install.sh`
ausführen.

## Deinstallieren

```bash
sudo ./uninstall.sh
```

Standardmäßig bleiben `/var/lib/dab-touchscreen` und `/etc/dab-touchscreen`
erhalten. Vollständig entfernen:

```bash
sudo ./uninstall.sh --purge-data --remove-user
```

## Secrets und MQTT

**Nicht in Git speichern:** WLAN-Schlüssel, MQTT-Passwörter, SSH-Schlüssel,
Tokens oder Zertifikatschlüssel. `secrets.env` ist deshalb in `.gitignore`.

Ohne `secrets.env` lauscht Mosquitto ausschließlich auf `127.0.0.1:1883` und
benötigt lokal keine Anmeldung. Für Geräte im LAN ist Authentifizierung Pflicht:

```bash
cp secrets.env.example secrets.env
# DAB_MQTT_LISTEN_ADDRESS=0.0.0.0 setzen
# DAB_MQTT_USERNAME und DAB_MQTT_PASSWORD setzen
sudo ./install.sh
```

Die lokale Laufzeitkopie liegt danach mit Rechten `root:dab 0640` unter
`/etc/dab-touchscreen/env`. Unterstützte Zeichen für MQTT-Benutzer/Passwort:
`A-Z a-z 0-9 . _ @ % + = : -`.

WLAN-Zugangsdaten werden ausschließlich von NetworkManager lokal gespeichert.
Der Installer erstellt oder exportiert kein WLAN-Profil.

## Installierte Komponenten und Pfade

- Anwendung: `/opt/dab-touchscreen`
- persistente Historie: `/var/lib/dab-touchscreen`
- lokale Laufzeitvariablen: `/etc/dab-touchscreen/env`
- Autostart: `/etc/xdg/autostart/dab-touchscreen.desktop`
- LightDM: `/etc/lightdm/lightdm.conf.d/50-dab-touchscreen.conf`
- NetworkManager-Polkit: `/etc/polkit-1/rules.d/49-dab-networkmanager.rules`
- Mosquitto: `/etc/mosquitto/conf.d/dab-touchscreen.conf`
- Simulator-Service: `/etc/systemd/system/dab-mqtt-simulator.service`
- X11-Touch-Fallback: `/etc/X11/xorg.conf.d/40-dab-touchscreen-rotate.conf`

Die Polkit-Regel erlaubt nur dem **lokalen, aktiven** Benutzer `dab`,
NetworkManager-Aktionen auszuführen. Es wird kein allgemeines passwortloses sudo
eingerichtet.

## Pakete

Der Installer verwendet Raspberry-Pi-/Debian-Pakete für NetworkManager,
Mosquitto, Python 3, PyQt5, PyQtGraph, Paho MQTT, PyYAML, SQLite, LightDM,
labwc, XWayland, wf-panel-pi, Squeekboard, Qt Wayland, wlr-randr, autotouch,
DejaVu Sans und Avahi. Die auf dem Referenzgerät ermittelten Versionen stehen in
[`docs/CURRENT_PI_INVENTORY.md`](docs/CURRENT_PI_INVENTORY.md).

## Entwicklung und Tests

```bash
python3 -m compileall -q src tests scripts
python3 -m unittest discover -s tests -v
```

MQTT-Topics werden in `config/topics.yaml`, Laufzeitoptionen in
`config/app.yaml` gepflegt. Leistungswerte werden ohne Nachkommastellen,
Spannungen/Temperaturen mit einer und Ströme mit zwei Nachkommastellen angezeigt.

## Hinweise

- Das alte `dab-touchscreen.service` für direkten X11-Start wird vom Installer
  deaktiviert. Produktiv ist LightDM + `LXDE-pi-labwc` + XDG-Autostart.
- OpenClaw 2026.9.4 und Node.js 24 waren auf dem untersuchten Pi vorhanden,
  gehören aber nicht zur Anwendung und werden nicht installiert.
- Die Demosignale sind standardmäßig aktiv. Für reale Messwerte
  `DAB_ENABLE_SIMULATOR=0` setzen und `config/topics.yaml` anpassen.

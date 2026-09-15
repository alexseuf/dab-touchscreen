# Überführung des bisherigen Pi-Stands

Diese Zuordnung dokumentiert, welche im bisherigen Projekt erstellten oder
veränderten Bestandteile in das eigenständige Repository übernommen, ersetzt
oder bewusst ausgeschlossen wurden.

## Direkt übernommen und bereinigt

- `src/`: komplette Qt-Anwendung, Datenmodell, SQLite-Historie, MQTT-Client,
  NetworkManager-Service und UI
- `config/app.yaml`, `config/topics.yaml`: Laufzeit- und Topic-Konfiguration
- `scripts/mqtt_simulator.py`: optionaler externer MQTT-Demopublisher
- `scripts/dab-wayland-app.sh`: Wayland-Start, 180°-Rotation und App-Start
- `tests/`: Datenmodell- und Ethernet-Konfigurationstests
- `docs/images/`: Designreferenzen aus dem GitHub-Projektstand

## In `install.sh` konsolidiert

Die bisherigen Skripte `flash_and_provision_ssd.sh`, `install_target.sh`,
`provision_attached_ssd.sh`, `install_autonomous_firstboot.sh`, `run_stage.sh`,
`target_smoke_test.sh`, `commissioning_check.py`,
`autonomous_commissioning.py` und `dab-deploy` waren für Image-Erstellung,
Offline-Chroot, OpenClaw-Reporting oder die schrittweise Erstinbetriebnahme
zuständig. Ihre dauerhaft notwendigen Ergebnisse sind jetzt idempotent in
`install.sh` enthalten:

- Pakete installieren
- Benutzer/Gruppen einrichten
- Anwendung nach `/opt` synchronisieren
- Berechtigungen setzen
- LightDM/labwc-Autostart installieren
- Squeekboard/Wayland-Komponenten installieren
- NetworkManager-Polkit installieren
- Mosquitto sicher konfigurieren
- Simulator-Service einrichten
- Tests ausführen und Dienste aktivieren

Die alten Skripte werden nicht benötigt und deshalb nicht mitinstalliert.

## Display, Touch und Kiosk

- Die produktive Sitzung ist LightDM + `LXDE-pi-labwc`.
- `system/lightdm-dab-touchscreen.conf` ersetzt die früheren manuellen
  Änderungen in `/etc/lightdm/lightdm.conf`.
- `system/dab-touchscreen.desktop` ersetzt benutzerspezifische Autostart-Dateien.
- `scripts/dab-wayland-app.sh` dreht alle erkannten Ausgänge um 180°.
- `autotouch` übernimmt die korrespondierende Touch-Zuordnung.
- `system/40-dab-touchscreen-rotate.conf` bleibt als X11-Fallback erhalten.
- Der historische `dab-kiosk-session.sh`/Openbox-X11-Pfad und
  `dab-touchscreen.service` werden nicht installiert.

## Netzwerk und WLAN

- NetworkManager bleibt alleinige Netzwerkschnittstelle.
- `system/49-dab-networkmanager.rules` erlaubt NetworkManager-Aktionen nur dem
  lokal aktiven Benutzer `dab`.
- Keine Datei aus `/etc/NetworkManager/system-connections` wurde gelesen oder
  übernommen.
- WLAN-Zugangsdaten werden erst durch den Benutzer in der HMI bzw. in
  NetworkManager angelegt.

## MQTT

- `system/mosquitto-dab.conf` ist eine Vorlage für den Installer.
- Ohne Secrets ist der Broker nur lokal und anonym erreichbar.
- Bei LAN-Freigabe erzwingt der Installer Benutzername und Passwort.
- `systemd/dab-mqtt-simulator.service` kann über `DAB_ENABLE_SIMULATOR`
  aktiviert oder deaktiviert werden.

## Bewusst ausgeschlossen

- OpenClaw, Node.js, OpenClaw-Reporting und OpenClaw-spezifische sudo-Helfer
- Image-Dateien und SSD-Flash-Werkzeuge
- private SSH-Schlüssel und `authorized_keys`
- NetworkManager-WLAN-Profile und WLAN-Schlüssel
- Passwörter, Tokens, API-Keys, Zertifikatschlüssel
- generierte Logs, SQLite-Datenbanken, Python-Caches und Laufzeitstatus

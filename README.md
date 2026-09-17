# DAB Touchscreen – Raspberry-Pi-HMI für 3‑Phasen-PFC + DAB

Touch-HMI für Raspberry Pi 4 mit offiziellem 7-Zoll-Raspberry-Pi-Touchdisplay. Verbindliche Referenzauflösung: **800×480 Pixel im Querformat**. Das System visualisiert dreiphasige PFC, Zwischenkreis und DAB, empfängt Betriebsdaten über MQTT und stellt einen lokalen MQTT-Broker bereit.

## Hauptnavigation

Die tatsächlich implementierte und verbindliche Hauptnavigation lautet:

`Übersicht | Verläufe | MQTT Explorer | ⚙ Einstellungen`

Beim Öffnen von **⚙ Einstellungen** wird die Hauptleiste ersetzt durch:

`Netzwerk (LAN) | WLAN | System | ← Zurück`

Die beiden Navigationsebenen werden nicht gleichzeitig angezeigt.

### Übersicht

Schematischer Energiefluss Netz → PFC → Zwischenkreis → DAB → DC-Ausgang sowie Messwerte und Temperaturen.

![Übersicht](docs/images/01_overview.svg)

### Verläufe

Zeitreihen mit Touch-Zoom/Pan und auswählbaren Zeitbereichen.

![Verläufe](docs/images/02_charts.svg)

### MQTT Explorer

Topic-Baum und MQTT-Nachrichten einschließlich Payload, Zeitstempel, QoS und Retain.

![MQTT Explorer](docs/images/05_mqtt.svg)

### ⚙ Einstellungen

**Netzwerk (LAN):** Ethernet-Konfiguration und lokaler MQTT-Broker.

![LAN und MQTT](docs/images/03_lan.svg)

**WLAN:** SSID-Scan, Verbindung, Signalstärke und IP-Adresse.

![WLAN](docs/images/04_wlan.svg)

**System:** CPU-Auslastung, Arbeitsspeicher, CPU-Temperatur, Datenträgerbelegung, Laufzeit, Hostname, Betriebssystem und aktive IP-Adressen. Neustart und Ausschalten nur nach Sicherheitsabfrage.

## Echtzeituhr (RTC)

Für einen zuverlässigen Betrieb ohne Netzwerk bzw. NTP soll eine batteriegepufferte **DS3231-RTC** über I²C verwendet werden. Bevorzugt wird ein DS3231-Modul für **3,3-V-Betrieb** mit Backup-Batterie. Die Standard-I²C-Adresse des DS3231 ist **0x68**.

Anschluss am 40-poligen GPIO-Header des Raspberry Pi 4:

| DS3231 | Kabelfarbe am vorhandenen Modul | Raspberry Pi 4 |
|---|---|---|
| VCC | Rot | Pin 1 – 3,3 V |
| SDA | Grün | Pin 3 – GPIO2 / SDA1 |
| SCL | Violett | Pin 5 – GPIO3 / SCL1 |
| GND | Schwarz | Pin 6 – GND |

Die Anschlüsse **32K** und **SQW** werden für die RTC-Grundfunktion nicht benötigt und bleiben frei. Das Modul nicht über 5 V anschließen, wenn die I²C-Pull-ups des verwendeten Moduls dadurch auf 5 V liegen könnten; für dieses Projekt wird VCC an 3,3 V betrieben.

Ziel für die spätere Softwareunterstützung: Beim Booten steht die Zeit auch ohne Netzwerk zur Verfügung. Sobald NTP verfügbar ist, kann die Systemzeit synchronisiert und anschließend die RTC auf die korrigierte Zeit aktualisiert werden.

## UI-Technik

Empfohlene/reale Zielarchitektur: Python mit PySide6 oder PyQt6; PyQtGraph für Verläufe. Styling über QSS. Die SVG-Dateien in `docs/images/` sind Design-Mock-ups und keine Screenshots eines anderen Frameworks. Deshalb können sie glatter/eleganter wirken als die derzeitige reale GUI. Ziel ist, die reale Qt-Oberfläche optisch an die Mock-ups anzunähern, ohne Seiteninhalte zu verändern.

Die Mock-ups wurden überwiegend mit `Arial`/`sans-serif` beschrieben. Für die reale Raspberry-Pi-GUI wird in `UI_SPEC.md` eine auf dem System verfügbare Qt/Linux-Schriftfamilie samt Fallback festgelegt, damit Mock-up und reale Darstellung reproduzierbar zusammenpassen.

## Wichtige Vorgaben

- 800×480 ist die verbindliche Referenz; 1024×600 ist keine Designgrundlage mehr.
- Bestehende Seiteninhalte nicht allein wegen der Auflösungsanpassung verändern.
- Haupt-/Untermenüstruktur entspricht der realen Implementierung.
- MQTT-Topics zentral mappen.
- MQTT-/Netzwerkoperationen dürfen die GUI nicht blockieren.
- NetworkManager für Netzwerkänderungen verwenden.
- Secrets ausschließlich lokal speichern und niemals in Git committen.
- Bildschirmtastatur darf das aktive Eingabefeld nicht verdecken.

Weitere Details: [`UI_SPEC.md`](UI_SPEC.md), [`ARCHITECTURE.md`](ARCHITECTURE.md), [`PROJECT_PROMPT.md`](PROJECT_PROMPT.md), [`COMMISSIONING.md`](COMMISSIONING.md).

## Raspberry-Pi-Implementierung und Wiederherstellung

Die eigenständig installierbare, auf dem Zielgerät geprüfte Implementierung liegt
unter [`raspberry-pi/`](raspberry-pi/). Sie enthält Anwendung, Konfiguration,
Installations-, Aktualisierungs- und Deinstallationsskripte sowie die benötigten
systemd-, Display-, Touch-, Kiosk-, Netzwerk- und MQTT-Dateien.

- Installation auf einem frischen Raspberry Pi OS:
  [`raspberry-pi/README.md`](raspberry-pi/README.md)
- Arbeiten mit GitHub, Aktualisierung und Wiederherstellung bekannter Stände:
  [`raspberry-pi/GIT_WORKFLOW.md`](raspberry-pi/GIT_WORKFLOW.md)
- Ungefährliche Vorlage für lokale Zugangsdaten:
  [`raspberry-pi/secrets.env.example`](raspberry-pi/secrets.env.example)

Normales Update nach einem Merge in `main`:

```bash
cd ~/dab-touchscreen && git pull --ff-only origin main && sudo ./raspberry-pi/update.sh
```

`update.sh` überspringt die Installation von Systempaketen. Weist eine Version
neue oder geänderte Paketabhängigkeiten aus, ist stattdessen
`sudo ./raspberry-pi/install.sh` auszuführen. Die bestehende Trennung von
Repository, lokalen Secrets und Laufzeitdaten bleibt als Grundlage für einen
späteren versionsbewussten Firmware-Updater mit Sicherung und Rollback erhalten;
ein solches Menü wird in diesem Pull Request noch nicht implementiert.

Echte Laufzeitdaten und Zugangsdaten bleiben lokal und werden durch die
Ignore-Regeln ausgeschlossen. Historische, inzwischen abgelöste
Migrationshelfer sind nur zur Nachvollziehbarkeit unter
[`archive/legacy-runtime/`](archive/legacy-runtime/) abgelegt.

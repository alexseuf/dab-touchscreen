# Architektur

## Ziel

Die Anwendung läuft auf einem Raspberry Pi 4 mit Raspberry Pi OS Bookworm und einem 7-Zoll-Touchdisplay. Sie soll beim Booten automatisch starten, Betriebsdaten über MQTT empfangen, diese darstellen und gleichzeitig einen lokalen MQTT-Broker bereitstellen.

## Empfohlener Software-Stack

- Raspberry Pi OS Bookworm 64-bit
- Mosquitto als lokaler MQTT-Broker
- Python 3.11+
- PySide6 oder PyQt6 für die Touch-GUI
- PyQtGraph für performante Zeitreihen
- paho-mqtt für MQTT
- NetworkManager / nmcli für LAN- und WLAN-Konfiguration
- SQLite für optionale lokale Historisierung
- systemd für Autostart und Recovery

## Komponenten

```text
Leistungsteil / Messsystem
        |
        | MQTT Publish
        v
+-----------------------------+
| Raspberry Pi 4              |
|                             |
|  +-----------------------+  |
|  | Mosquitto Broker      |  |
|  +-----------+-----------+  |
|              |              |
|              v              |
|  +-----------------------+  |
|  | Dashboard Service     |  |
|  | - MQTT Client         |  |
|  | - Topic Mapping       |  |
|  | - Data Cache          |  |
|  | - Data Quality        |  |
|  | - History Buffer      |  |
|  +-----------+-----------+  |
|              |              |
|              v              |
|  +-----------------------+  |
|  | Touch GUI             |  |
|  | Hauptnavigation       |  |
|  | 1 Übersicht           |  |
|  | 2 Verläufe            |  |
|  | 3 MQTT Explorer       |  |
|  | 4 Einstellungen       |  |
|  |   - Netzwerk (LAN)    |  |
|  |   - WLAN              |  |
|  |   - System            |  |
|  |   - Zurück            |  |
|  +-----------------------+  |
|                             |
|  NetworkManager   SQLite    |
+-----------------------------+
        |
        +-- Ethernet
        +-- WLAN
        +-- USB SSD 100 GB
```

## Datenfluss

1. Externe Geräte publizieren Messwerte an den lokalen Broker.
2. Der MQTT-Client der Anwendung subscribed auf die konfigurierten Topics.
3. Eine zentrale Datenmodell-Schicht normalisiert Werte, Einheiten, Zeitstempel und Qualitätsstatus.
4. Die GUI liest ausschließlich aus diesem Datenmodell und greift nicht direkt auf MQTT zu.
5. Zeitreihen werden in einem Ringpuffer gehalten; optional werden sie zusätzlich auf SSD persistiert.
6. Der MQTT-Explorer kann unabhängig vom festen Mapping alle eingehenden Topics anzeigen.

## Verzeichnisstruktur

```text
dab-touchscreen/
├── README.md
├── PROJECT_PROMPT.md
├── REQUIREMENTS.md
├── UI_SPEC.md
├── ARCHITECTURE.md
├── MQTT.md
├── OPEN_QUESTIONS.md
├── docs/
│   └── images/
│       ├── 01_overview.svg
│       ├── 02_charts.svg
│       ├── 03_lan.svg
│       ├── 04_wlan.svg
│       ├── 05_mqtt.svg
│       └── architecture.svg
├── src/
│   ├── main.py
│   ├── app.py
│   ├── config/
│   │   ├── settings.py
│   │   └── topic_mapping.py
│   ├── mqtt/
│   │   ├── client.py
│   │   ├── broker_status.py
│   │   └── explorer_model.py
│   ├── data/
│   │   ├── model.py
│   │   ├── quality.py
│   │   └── history.py
│   ├── network/
│   │   ├── ethernet.py
│   │   └── wifi.py
│   ├── ui/
│   │   ├── main_window.py
│   │   ├── overview_page.py
│   │   ├── charts_page.py
│   │   ├── lan_page.py
│   │   ├── wifi_page.py
│   │   └── mqtt_page.py
│   └── utils/
├── config/
│   ├── app.yaml
│   └── topics.yaml
├── systemd/
│   └── dab-touchscreen.service
├── scripts/
│   ├── install.sh
│   ├── update.sh
│   └── mqtt_simulator.py
└── tests/
```

## Zuständigkeiten

### MQTT Client
- automatischer Reconnect
- Last-Will/Status optional
- Subscription zentral verwalten
- QoS 0/1 unterstützen
- retained Messages korrekt verarbeiten
- Empfangszeitpunkt lokal erfassen

### Data Model
Jeder Messwert sollte mindestens besitzen:
- logischer Name
- aktueller Wert
- Einheit
- letzter Zeitstempel
- MQTT-Topic
- Qualitätsstatus: `valid`, `stale`, `missing`, `invalid`

Ein Wert gilt nach konfigurierbarer Zeit ohne Update als `stale` und darf in der GUI nicht wie ein aktueller Messwert aussehen.

### GUI
Die GUI darf nicht blockieren. MQTT, WLAN-Scan, Netzwerkkonfiguration und Datenbankzugriffe müssen asynchron oder in Worker-Threads erfolgen. Touch-Ziele sollten mindestens ungefähr 44×44 px groß sein.

## Netzwerk

NetworkManager ist die bevorzugte Schnittstelle. Die Anwendung soll keine Dateien unter `/etc/network/interfaces` direkt manipulieren.

Für Ethernet:
- DHCP
- feste IPv4-Adresse
- Netzmaske bzw. Prefix
- Gateway
- DNS
- Validierung vor Übernahme
- Rückfallmöglichkeit bei ungültiger Konfiguration

Für WLAN:
- Scan
- SSID-Auswahl
- WPA2/WPA3-Passwort
- Bildschirmtastatur
- Verbindungsstatus
- Signalstärke in dBm und Balken
- aktuelle IPv4-Adresse

## MQTT Broker

Mosquitto soll als systemd-Dienst laufen. Für den ersten lokalen Aufbau:
- TCP Port 1883
- unverschlüsselt
- optional Benutzername/Passwort
- Zugriff standardmäßig nur aus vertrauenswürdigem LAN/WLAN

Die Anwendung soll Broker-Status, Host, Port und Verbindung anzeigen.

## Historisierung

Für die erste Version genügt ein RAM-Ringpuffer. Optional:
- SQLite auf SSD
- konfigurierbare Aufbewahrungsdauer
- Downsampling für lange Zeiträume
- Begrenzung von Schreibfrequenz und Datenbankgröße

## Autostart und Recovery

Die Anwendung wird als systemd-Service gestartet:
- Start nach Netzwerk und grafischer Sitzung
- automatischer Neustart bei Fehler
- Logging über journald
- keine Endlosschleife bei fehlerhafter Konfiguration

## Testbarkeit

`scripts/mqtt_simulator.py` soll synthetische Werte erzeugen, damit die vollständige GUI ohne angeschlossenen Leistungsteil entwickelt werden kann. Der Simulator soll mindestens Spannungen, Ströme, Leistungen, Temperaturen, Zwischenkreisspannung und DAB-Ausgangswerte publizieren.

## Architekturentscheidungen

1. MQTT-Topic-Namen niemals direkt in Widgets verteilen; zentrales Mapping verwenden.
2. Netzwerkänderungen über eine dedizierte Service-Schicht kapseln.
3. UI und Datenmodell trennen.
4. MQTT Explorer darf unbekannte Topics anzeigen, ohne dass sie im Mapping stehen.
5. Die Anwendung muss auch bei Broker-Ausfall bedienbar bleiben.
6. Fehlende Daten klar kennzeichnen statt alte Werte unbemerkt weiter anzuzeigen.
7. Die exakten realen Topics werden erst im zweiten Projektabschnitt eingetragen.

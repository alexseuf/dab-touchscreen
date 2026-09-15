# DAB Touchscreen – Raspberry-Pi-HMI für 3‑Phasen-PFC + DAB

Dieses Repository beschreibt und implementiert eine Touch-HMI für einen Raspberry Pi 4 mit 7‑Zoll-Display. Das System visualisiert eine dreiphasige PFC mit nachgeschaltetem Dual Active Bridge (DAB), empfängt Betriebsdaten über MQTT und stellt selbst einen lokalen MQTT-Broker bereit.

## Zielhardware

- Raspberry Pi 4
- 7‑Zoll-Touchdisplay, Zielauflösung zunächst 1024×600
- 100‑GB-SSD über USB, später dauerhaft am Raspberry Pi
- Ethernet und WLAN
- lokaler MQTT-Broker

## Schrittweise Inbetriebnahme

Das Projekt ist ausdrücklich so aufgebaut, dass nicht alle Funktionen gleichzeitig aktiviert werden müssen. Die Inbetriebnahme erfolgt in Stufen 0 bis 9. Jede Stufe schaltet nur die Funktionen frei, die für diesen Teststand benötigt werden.

Details: [`COMMISSIONING.md`](COMMISSIONING.md)

Aktuelle Stufe und Feature-Flags: [`config/commissioning.yaml`](config/commissioning.yaml)

Beispiele:

```bash
python3 -m src.main --stage 1
python3 scripts/commissioning_check.py --stage 1
```

Stufenübersicht:

- 0: Raspberry Pi / SSD / Display / Netzwerkhardware
- 1: GUI offline mit Demo-Daten
- 2: lokaler MQTT-Broker und MQTT-Testdaten
- 3: reale MQTT-Daten und Topic-Mapping
- 4: Historie und Diagramme
- 5: schreibende LAN-Konfiguration
- 6: schreibende WLAN-Konfiguration und lokale Credentials
- 7: MQTT-Explorer
- 8: Autostart und Dauerbetrieb
- 9: Produktionsbetrieb

Netzwerk- und Credential-Änderungen sind in frühen Stufen absichtlich gesperrt. Dadurch kann die HMI zunächst gefahrlos getestet werden.

## Systemarchitektur

![Systemarchitektur](docs/images/architecture.svg)

Die detaillierte Architektur, der vorgeschlagene Software-Stack, die Modultrennung und die Ziel-Verzeichnisstruktur stehen in [`ARCHITECTURE.md`](ARCHITECTURE.md).

## Hauptansichten und Einstellungen

Die permanente Hauptleiste enthält nur die vier Einträge
`Übersicht | Verläufe | MQTT Explorer | ⚙ Einstellungen`.
LAN, WLAN und Systemfunktionen liegen in einer zweiten Navigationsebene, damit
die Hauptansichten auf dem 7-Zoll-Display genügend Platz behalten. Nach dem
Öffnen von **⚙ Einstellungen** ersetzt folgende Leiste die Hauptnavigation:
`Netzwerk (LAN) | WLAN | System | ← Zurück`.

### 1. Übersicht / Live-Daten

Schematischer Energiefluss Netz → 3‑Phasen-PFC → Zwischenkreis → DAB → DC-Ausgang sowie die wichtigsten Messwerte und Temperaturen.

![Übersicht](docs/images/01_overview.svg)

### 2. Verläufe

Zeitreihen aller Messwerte, sinnvoll gruppiert auf mehrere Y-Achsen, Touch-Zoom/Pan und auswählbare Zeitbereiche.

![Verläufe](docs/images/02_charts.svg)

### 3. MQTT Explorer

Topic-Baum und eingehende MQTT-Nachrichten möglichst ähnlich zu MQTT Explorer, inklusive Topic, Payload, Zeitstempel, QoS und Retain-Status.

![MQTT Explorer](docs/images/05_mqtt.svg)

### 4. ⚙ Einstellungen

Der Einstellungsbereich besitzt die Unterseiten **Netzwerk (LAN)**, **WLAN**
und **System**. **← Zurück** wechselt wieder zur Hauptnavigation.

#### Netzwerk (LAN)

Ethernet-Konfiguration einschließlich DHCP/fester IPv4-Adresse sowie Konfiguration und Status des lokalen MQTT-Brokers.

![LAN und MQTT](docs/images/03_lan.svg)

#### WLAN

Scan verfügbarer SSIDs, Auswahl per Liste, Passworteingabe über Bildschirmtastatur, Signalstärke und aktuelle WLAN-IP.

![WLAN](docs/images/04_wlan.svg)

#### System

Aktuelle Raspberry-Pi-Systemdaten: CPU-Auslastung, Arbeitsspeicher,
CPU-Temperatur, Datenträgerbelegung, Laufzeit und IP-Adressen. Die Aktionen
**Neustart** und **Ausschalten** benötigen jeweils eine Sicherheitsabfrage.

## Dokumente

- `PROJECT_PROMPT.md` – ausführlicher Arbeitsauftrag für OpenClaw
- `REQUIREMENTS.md` – funktionale und technische Anforderungen
- `MQTT.md` – vorläufiges MQTT-Datenmodell und Vorgehen zur späteren Topic-Zuordnung
- `OPEN_QUESTIONS.md` – noch zu klärende Punkte
- `UI_SPEC.md` – Display- und Bedienkonzept
- `ARCHITECTURE.md` – Softwarearchitektur, Komponenten, Datenfluss und Ziel-Verzeichnisstruktur
- `COMMISSIONING.md` – verbindlicher Stufenplan für Entwicklung und Inbetriebnahme
- `config/commissioning.yaml` – Freigabe der Funktionen je Inbetriebnahmestand
- `scripts/commissioning_check.py` – Diagnose- und Abnahmetest für die aktive Stufe
- `src/main.py` – stufenfähiger Anwendungseinstieg
- `docs/images/*.svg` – visuelle Referenzen der Ansichten und der Systemarchitektur

## Wichtige Architekturvorgaben

- MQTT-Topics zentral mappen und nicht direkt in der GUI verteilen.
- Empfang, Datenmodell und Darstellung voneinander trennen.
- Fehlende oder zu alte Werte als `missing` bzw. `stale` kennzeichnen.
- MQTT-Reconnect und Broker-Ausfall dürfen die Touch-Oberfläche nicht blockieren.
- Netzwerkkonfiguration über NetworkManager kapseln.
- Anwendung und Broker über systemd starten und überwachen.
- Einen MQTT-Simulator für die Entwicklung ohne angeschlossenen Leistungsteil vorsehen.
- Schreibende Funktionen erst in der zugehörigen Inbetriebnahmestufe aktivieren.
- Zugangsdaten ausschließlich lokal speichern und niemals in Git committen.

Die exakten MQTT-Topic-Namen und Payload-Formate werden in einem zweiten Schritt anhand der realen MQTT-Explorer-Darstellung festgelegt. Die Software soll deshalb Topic-Mappings konfigurierbar halten und nicht hart in der GUI verteilen.

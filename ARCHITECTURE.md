# Architektur

## Ziel

Die Anwendung läuft auf einem Raspberry Pi 4 mit Raspberry Pi OS Bookworm und dem offiziellen 7-Zoll-Touchdisplay mit 800×480 Pixeln. Sie soll beim Booten automatisch starten, Betriebsdaten über MQTT empfangen, diese darstellen und gleichzeitig einen lokalen MQTT-Broker bereitstellen.

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
```

Die Hauptnavigation enthält ausschließlich `Übersicht | Verläufe | MQTT Explorer | ⚙ Einstellungen`. Beim Öffnen von Einstellungen wird diese Leiste vollständig durch `Netzwerk (LAN) | WLAN | System | ← Zurück` ersetzt. Beide Ebenen werden niemals gleichzeitig angezeigt.

## Datenfluss

1. Externe Geräte publizieren Messwerte an den lokalen Broker.
2. Der MQTT-Client subscribed auf die konfigurierten Topics.
3. Eine zentrale Datenmodell-Schicht normalisiert Werte, Einheiten, Zeitstempel und Qualitätsstatus.
4. Die GUI liest ausschließlich aus diesem Datenmodell.
5. Zeitreihen werden in einem Ringpuffer gehalten und optional auf SSD persistiert.
6. Der MQTT-Explorer kann unabhängig vom festen Mapping alle eingehenden Topics anzeigen.

## GUI und Bedienung

Die GUI darf nicht blockieren. MQTT, WLAN-Scan, Netzwerkkonfiguration und Datenbankzugriffe müssen asynchron oder in Worker-Threads erfolgen. Die reale Referenzauflösung ist 800×480. Touch-Ziele sollen ungefähr 44–48 px oder größer sein. Höhere Auflösungen dürfen zusätzlichen Platz nutzen, aber keine Funktion darf mehr als 800×480 voraussetzen.

Die Implementierung soll mit PySide6/PyQt6 und QSS so gestaltet werden, dass sie den SVG-Referenzentwürfen möglichst nahekommt. Die SVGs sind Design-Mock-ups und keine Screenshots eines separaten Frameworks. Schriftart, Abstände, Rundungen, Kontraste und Widget-Höhen werden in UI_SPEC.md verbindlich dokumentiert.

## Einstellungen – System

Die System-Unterseite zeigt CPU-Auslastung, Arbeitsspeicher, CPU-Temperatur, Datenträgerbelegung, Laufzeit, Hostname, Betriebssystem und aktive IP-Adressen. Neustart und Ausschalten sind als große Touch-Aktionen vorhanden und benötigen jeweils eine eindeutige Sicherheitsabfrage.

## Netzwerk

NetworkManager ist die bevorzugte Schnittstelle. Die Anwendung soll keine Dateien unter `/etc/network/interfaces` direkt manipulieren. Ethernet unterstützt DHCP/feste IPv4, Prefix, Gateway, DNS, Validierung und Recovery. WLAN unterstützt Scan, SSID-Auswahl, WPA2/WPA3, Bildschirmtastatur, Status, Signalstärke und IPv4-Adresse.

## MQTT Broker

Mosquitto läuft als systemd-Dienst. Für den ersten lokalen Aufbau: TCP 1883, unverschlüsselt, optional Benutzername/Passwort, Zugriff nur aus vertrauenswürdigem LAN/WLAN. Die GUI zeigt Broker-Status, Host, Port und Verbindung.

## Historisierung

Für die erste Version genügt ein RAM-Ringpuffer. Optional SQLite auf SSD mit konfigurierbarer Aufbewahrung, Downsampling und begrenzter Schreibfrequenz/Datenbankgröße.

## Autostart und Recovery

Die Anwendung wird als systemd-Service gestartet: nach Netzwerk und grafischer Sitzung, automatischer Neustart bei Fehler, Logging über journald, keine Endlosschleife bei fehlerhafter Konfiguration.

## Testbarkeit

`scripts/mqtt_simulator.py` erzeugt synthetische Werte für die vollständige GUI ohne angeschlossenen Leistungsteil.

## Architekturentscheidungen

1. MQTT-Topic-Namen niemals direkt in Widgets verteilen; zentrales Mapping verwenden.
2. Netzwerkänderungen über eine dedizierte Service-Schicht kapseln.
3. UI und Datenmodell trennen.
4. MQTT Explorer darf unbekannte Topics anzeigen.
5. Anwendung muss auch bei Broker-Ausfall bedienbar bleiben.
6. Fehlende Daten klar kennzeichnen.
7. Exakte reale Topics werden erst anhand der realen Anlage eingetragen.
8. Die reale Displayreferenz ist 800×480.
9. Einstellungen sind eine zweite Navigationsebene und keine separaten Hauptreiter.

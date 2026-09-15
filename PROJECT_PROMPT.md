# Arbeitsauftrag für OpenClaw

## Ziel

Baue und pflege auf Raspberry Pi 4 mit offiziellem 7-Zoll-Touchdisplay eine lokale HMI/Monitoring-Oberfläche für dreiphasige PFC, DC-Zwischenkreis und Dual Active Bridge (DAB). Die verbindliche Referenzauflösung des Displays ist **800×480 Pixel im Querformat**.

Das Zielsystem stellt einen lokalen MQTT-Broker bereit, visualisiert MQTT-Daten, unterstützt Ethernet/WLAN, startet automatisch fullscreen und bleibt bei fehlenden/stale Daten bedienbar. Konfiguration, Topic-Mapping und GUI-Logik bleiben getrennt. Zugangsdaten niemals in Git, Screenshots oder normalen Logs speichern.

## Touch-Bedienung

Alle Eingaben müssen über Touch möglich sein. Sobald die Bildschirmtastatur erscheint, muss das fokussierte Eingabefeld vollständig sichtbar bleiben; die GUI verschiebt/scrollt den Inhalt generisch. Nach Schließen der Tastatur kehrt die Ansicht sinnvoll zurück.

## Hauptnavigation und Einstellungs-Untermenü

Die Hauptnavigation enthält ausschließlich:

`Übersicht | Verläufe | MQTT Explorer | ⚙ Einstellungen`

Beim Öffnen von **⚙ Einstellungen** wird sie vollständig ersetzt durch:

`Netzwerk (LAN) | WLAN | System | ← Zurück`

Beide Navigationsebenen dürfen niemals gleichzeitig Platz beanspruchen. **← Zurück** stellt die Hauptnavigation wieder her. Diese Struktur entspricht der real implementierten Oberfläche und ist verbindlich.

## Übersicht / Live-Daten

Zeige `3~ Netz → PFC → DC-Zwischenkreis → DAB → DC-Ausgang` sowie Effektivspannungen/-ströme L1-L3, Netzfrequenz, Eingangsleistung, Zwischenkreisspannung, Ausgangsspannung/-strom/-leistung und Temperaturen von PFC, DAB primär/sekundär, Drossel und Trafo. MQTT-Verbindung, Datenalter und Betriebsbereitschaft anzeigen; stale Werte eindeutig kennzeichnen.

## Verläufe

Zeitreihen mit Touch-Zoom/Pan, Reset, wählbaren Zeitfenstern, sinnvollen Skalen für Spannung/Strom/Leistung/Temperatur und ein-/ausblendbaren Kurven. Historie nach GUI-Neustart erhalten, sofern Logging aktiv.

## MQTT Explorer

Hierarchischer Topic-Baum, dynamische Topics, letzter Payload, Zeitstempel/Alter, QoS, Retain, Roh-Payload, JSON-Formatierung und Filterfunktion. Hohe Nachrichtenrate darf UI nicht blockieren.

## Einstellungen – Netzwerk (LAN) und MQTT

DHCP/feste IPv4, Prefix, Gateway, DNS und aktuelle Ethernet-IP. Lokaler MQTT-Broker standardmäßig Port 1883, Brokerstatus, sinnvolle Bindung und optional Authentifizierung. Änderungen validieren und Recovery-Weg vorsehen.

## Einstellungen – WLAN

SSID-Scan, Auswahl, Touch-Passworteingabe, Verbinden/Trennen, Signalstärke, IPv4 und Status. Vorhandene sichere NetworkManager-Profile für das bekannte Hausnetz bevorzugt übernehmen; Secrets niemals in Git oder Logs.

## Einstellungen – System

CPU-Auslastung, Arbeitsspeicher, CPU-Temperatur, Datenträgerbelegung, Laufzeit, Hostname, Betriebssystem und aktive IP-Adressen live anzeigen. Systemdaten asynchron aktualisieren. Große Touch-Schaltflächen für Neustart und Ausschalten; beide Aktionen nur nach eindeutiger Sicherheitsabfrage, Standardaktion Abbrechen.

## GUI-Technik und visuelle Referenz

Bevorzugter Stack: Python 3.11+, PySide6 oder PyQt6, PyQtGraph, paho-mqtt, NetworkManager/nmcli, Mosquitto, optional SQLite und systemd. Die SVG-Dateien unter `docs/images/` sind Design-Mock-ups und keine Screenshots eines anderen GUI-Frameworks. Die reale PySide6/PyQt6-Oberfläche soll mittels QSS möglichst nah an diesen Referenzen umgesetzt werden. Verbindliche Details zu Font, Abständen, Touchgrößen und 800×480 stehen in `UI_SPEC.md`.

Die Referenzbilder dürfen bei der Umstellung auf 800×480 **inhaltlich nicht verändert** werden. Menüstruktur wird jedoch an die tatsächlich implementierte Haupt-/Einstellungsnavigation synchronisiert. Funktionale Inhalte einer Seite bleiben erhalten.

## MQTT-Topics

Keine realen Topic-Namen erfinden. Zentrales konfigurierbares Mapping verwenden und reale Topics anhand der Anlage eintragen.

## Zugangsdaten und Wartbarkeit

Benötigte Credentials lokal und geschützt speichern, z. B. NetworkManager-Profile, systemd Credentials oder dedizierte Secret-Datei mit restriktiven Rechten. Nie in Git. OpenClaw muss dokumentieren, wo lokale Credentials für spätere Wartung liegen, ohne deren Werte offenzulegen.

## Abnahmekriterien

1. Anwendung startet fullscreen auf 800×480.
2. Hauptnavigation besitzt exakt Übersicht, Verläufe, MQTT Explorer, Einstellungen.
3. Einstellungen besitzt exakt Netzwerk (LAN), WLAN, System und Zurück.
4. Lokaler MQTT-Broker läuft.
5. Simulierte MQTT-Daten speisen Live-Anzeigen und Diagramme.
6. Netzwerkstatus/-parameter funktionieren mit Validierung.
7. MQTT Explorer verarbeitet unbekannte Topics dynamisch.
8. Systemseite zeigt die realen Pi-Daten.
9. Neustart/Ausschalten verlangen Sicherheitsabfrage.
10. Bildschirmtastatur verdeckt kein aktives Feld.
11. GUI bleibt bei Broker-/Datenfehlern bedienbar.
12. Secrets gelangen nicht in Git.
13. Jede Haupt-/Unteransicht wird auf realen 800×480 geprüft.

## Vorgehensweise

Arbeite reproduzierbar und in nachvollziehbaren Schritten. Bestehende, bereits funktionierende Seiteninhalte nicht ohne ausdrücklichen Auftrag umgestalten. Änderungen an Navigation, Auflösung und Styling gegen die reale Hardware prüfen und dokumentieren.

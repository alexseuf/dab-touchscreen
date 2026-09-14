# Arbeitsauftrag für OpenClaw

## Ziel

Baue auf der angeschlossenen 100‑GB-USB-SSD ein möglichst vollständig vorbereitetes System, das später an einem Raspberry Pi 4 mit 7‑Zoll-Touchdisplay betrieben wird. Das System dient als lokale HMI/Monitoring-Oberfläche für einen Leistungselektronik-Aufbau aus dreiphasiger PFC, DC-Zwischenkreis und nachgeschaltetem Dual Active Bridge (DAB).

Arbeite reproduzierbar, dokumentiere alle Installations- und Konfigurationsschritte im Repository und vermeide unnötige Abhängigkeiten von Cloud-Diensten. Das Zielsystem soll nach dem Umstecken der SSD auf den Raspberry Pi möglichst einfach in Betrieb genommen werden können.

## Architektur

Das Zielsystem muss:

- einen lokalen MQTT-Broker bereitstellen, vorzugsweise Mosquitto;
- MQTT-Daten lokal abonnieren und visualisieren;
- Ethernet und WLAN unterstützen;
- vollständig per 7‑Zoll-Touchdisplay bedienbar sein;
- nach dem Boot automatisch in die HMI starten (Kiosk/Fullscreen);
- bei Ausfall einzelner MQTT-Werte weiterlaufen und fehlende/stale Werte klar kennzeichnen;
- Konfiguration und Topic-Mapping von der GUI-Logik trennen;
- Logs und Diagnoseinformationen lokal bereitstellen;
- möglichst robust gegen Stromausfall und fehlerhafte MQTT-Nachrichten sein.

## Reiter 1 – Übersicht / Live-Daten

Zeige schematisch:

`3~ Netz → PFC → DC-Zwischenkreis → DAB → DC-Ausgang`

Darzustellende Live-Werte:

- Effektivspannung L1, L2, L3
- Effektivstrom L1, L2, L3
- Netzfrequenz
- Eingangsleistung
- Zwischenkreisspannung
- Ausgangsspannung
- Ausgangsstrom
- Ausgangsleistung
- Temperatur PFC-Leistungsteil
- Temperatur primärseitige DAB-Halbbrücke
- Temperatur sekundärseitige DAB-Halbbrücke
- Drosseltemperatur
- Trafotemperatur

Zusätzlich Statusanzeigen vorsehen für MQTT-Verbindung, Datenalter und allgemeine Betriebsbereitschaft. Werte mit veraltetem Timestamp dürfen nicht wie gültige aktuelle Werte erscheinen.

## Reiter 2 – Verläufe

Stelle die Messwerte als Liniendiagramme dar. Anforderungen:

- Touch-Zoom und Pan
- Zoom zurücksetzen
- wählbare Zeitfenster
- mehrere Y-Achsen bzw. sinnvoll getrennte Skalen für Spannung, Strom, Leistung und Temperatur
- Legende zum Ein-/Ausblenden einzelner Kurven
- keine unlesbare Überlagerung sehr unterschiedlicher Größen
- Historie auch nach GUI-Neustart verfügbar, sofern lokales Logging aktiviert ist

## Reiter 3 – Ethernet und MQTT

Ethernet-Konfiguration über Touch:

- DHCP oder feste IPv4-Adresse
- IP-Adresse
- Subnetzmaske/Prefix
- Gateway
- DNS
- aktuelle Ethernet-IP anzeigen

MQTT-Broker:

- lokaler Broker auf dem Raspberry Pi
- Standard-Port 1883 für unverschlüsseltes MQTT
- Brokerstatus anzeigen
- Bind-Adresse/Interfaces sinnvoll konfigurieren
- optional Benutzername/Passwort vorbereiten
- Änderungen sicher anwenden, validieren und bei ungültigen Netzwerkdaten nicht übernehmen

Netzwerkänderungen dürfen die Oberfläche nicht dauerhaft unbedienbar machen. Vor dem Anwenden validieren und einen Recovery-Weg dokumentieren.

## Reiter 4 – WLAN

- verfügbare SSIDs scannen und anzeigen
- SSID auswählen
- WLAN-Passwort über Touch-Bildschirmtastatur eingeben
- Verbinden/Trennen
- Signalstärke in dBm und grafisch anzeigen
- zugewiesene IPv4-Adresse anzeigen
- Verbindungsstatus anzeigen
- Passwörter nicht im Klartext in Logs oder GUI anzeigen

## Reiter 5 – MQTT Explorer

Wenn auf 7 Zoll sinnvoll bedienbar, implementiere eine MQTT-Explorer-ähnliche Ansicht:

- hierarchischer Topic-Baum
- eingehende Topics automatisch ergänzen
- letzter Payload pro Topic
- Zeitstempel/Alter
- QoS
- Retain-Flag
- Roh-Payload
- JSON formatiert darstellen, wenn Payload valides JSON ist
- Such-/Filterfunktion
- Aktualisierungen sichtbar, aber UI nicht durch hohe Nachrichtenrate blockieren

## MQTT-Topics

Die exakten Topic-Namen sind noch nicht bekannt. Baue deshalb zunächst ein konfigurierbares Mapping. In einem zweiten Schritt werden anhand einer MQTT-Explorer-Aufnahme die realen Topics und Payloads eingetragen. Siehe `MQTT.md`.

## Technischer Vorschlag

Bevorzuge eine robuste Raspberry-Pi-native Lösung. Geeignet ist z. B. Python mit PySide6/PyQtGraph oder eine vergleichbar touch-taugliche GUI. Für Netzwerkänderungen sollen vorhandene Linux/Raspberry-Pi-Mechanismen genutzt werden, nicht selbst geschriebene fragile Shell-Hacks. MQTT-Broker vorzugsweise Mosquitto. Für lokale Historie eine ressourcenschonende persistente Speicherung vorsehen, z. B. SQLite mit Retention/Downsampling.

Treffe begründete technische Entscheidungen selbstständig, dokumentiere sie und halte Komponenten austauschbar.

## Abnahmekriterien

Das Projekt gilt für die erste Stufe als erfolgreich, wenn:

1. die Anwendung auf Raspberry Pi 4 startet und automatisch fullscreen angezeigt wird;
2. alle fünf Reiter vorhanden und touch-bedienbar sind;
3. ein lokaler MQTT-Broker läuft;
4. simulierte MQTT-Testdaten alle Live-Anzeigen und Diagramme speisen können;
5. Topic-Mappings ohne Quellcodeänderung angepasst werden können;
6. Ethernet- und WLAN-Status korrekt angezeigt werden;
7. Netzwerkparameter mit Validierung konfigurierbar sind;
8. MQTT-Explorer-Ansicht unbekannte Topics dynamisch anzeigen kann;
9. Neustart, Broker-Ausfall und fehlende MQTT-Daten die GUI nicht zum Absturz bringen;
10. Installation, Autostart, Backup/Restore und Recovery dokumentiert sind.

## Vorgehensweise

Arbeite in nachvollziehbaren Schritten. Lege zuerst Architektur, Verzeichnisstruktur, Konfigurationsformat, Mock-Daten und UI-Grundgerüst an. Implementiere danach MQTT, Live-Ansicht, Historie, Netzwerkseiten und MQTT Explorer. Verwende für Entwicklung ohne reale PFC/DAB einen MQTT-Simulator. Führe am Ende einen lokalen Funktionstest durch und dokumentiere offene Punkte.

Keine realen Topic-Namen erfinden: Platzhalter deutlich kennzeichnen, bis die MQTT-Explorer-Daten vorliegen.

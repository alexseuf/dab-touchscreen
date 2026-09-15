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

## Touch-Bedienung und Bildschirmtastatur

Alle Eingaben müssen vollständig über das 7‑Zoll-Touchdisplay möglich sein.

Besonders wichtig: Sobald für ein Eingabefeld die Bildschirmtastatur geöffnet wird, darf die Tastatur das aktive Eingabefeld nicht verdecken. Die GUI muss den sichtbaren Inhalt automatisch so verschieben bzw. scrollen, dass das fokussierte Eingabefeld vollständig oberhalb der Bildschirmtastatur sichtbar bleibt. Nach dem Schließen der Tastatur soll die Ansicht sinnvoll in die vorherige Position zurückkehren.

Dies gilt insbesondere für:

- IPv4-Adresse
- Netzmaske/Prefix
- Gateway
- DNS
- MQTT-Port
- MQTT-Benutzername und Passwort
- WLAN-SSID, falls manuelle Eingabe erforderlich ist
- WLAN-Passwort
- spätere Konfigurationsfelder

Die Lösung soll generisch implementiert werden und nicht als Sonderfall für einzelne Felder.

## Zugangsdaten und dauerhafte Wartbarkeit durch OpenClaw

OpenClaw soll das System auch Monate später noch selbstständig warten und ändern können. Dafür müssen alle für Wartung und Administration benötigten Benutzernamen, Zugangsdaten und Passwörter auf dem Zielsystem dauerhaft verfügbar sein.

WICHTIG: Zugangsdaten niemals im GitHub-Repository, in Markdown-Dateien, Quellcode, Screenshots oder normalen Logs im Klartext speichern.

Vorgabe für die Umsetzung:

- Zugangsdaten ausschließlich lokal auf dem Raspberry Pi bzw. der System-SSD speichern;
- bevorzugt vorhandene sichere Mechanismen verwenden, z. B. NetworkManager-Verbindungsprofile, systemd Credentials, Secret Service/Keyring oder eine dedizierte lokale Secret-Datei mit restriktiven Dateirechten;
- falls eine lokale Secret-Datei erforderlich ist: Eigentümer root bzw. der Dienstbenutzer und Dateirechte maximal `0600`;
- Secret-Dateien müssen über `.gitignore` ausdrücklich vom Repository ausgeschlossen sein;
- OpenClaw muss dokumentieren, wo die lokalen Credentials liegen und wie sie für spätere Wartungsarbeiten gelesen bzw. geändert werden;
- Passwörter niemals in Debug-Ausgaben oder normalen Applikationslogs ausgeben;
- GUI-Passwortfelder standardmäßig maskieren;
- Backup/Restore-Konzept für lokale Credentials dokumentieren, ohne die Secrets in Git zu übertragen.

OpenClaw soll sich damit die erforderlichen Zugangsdaten auf dem Zielsystem dauerhaft merken können, ohne sie öffentlich oder ungeschützt abzulegen.

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

## Hauptnavigation und Einstellungs-Untermenü

Die Hauptnavigation enthält ausschließlich:

`Übersicht | Verläufe | MQTT Explorer | ⚙ Einstellungen`

Beim Öffnen von **⚙ Einstellungen** wird sie durch folgende zweite Ebene ersetzt:

`Netzwerk (LAN) | WLAN | System | ← Zurück`

**← Zurück** stellt die Hauptnavigation wieder her. Beide Ebenen dürfen auf dem
kleinen Display nicht gleichzeitig Platz beanspruchen.

## Einstellungen – Netzwerk (LAN) und MQTT

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

## Einstellungen – WLAN

- verfügbare SSIDs scannen und anzeigen
- SSID auswählen
- WLAN-Passwort über Touch-Bildschirmtastatur eingeben
- Verbinden/Trennen
- Signalstärke in dBm und grafisch anzeigen
- zugewiesene IPv4-Adresse anzeigen
- Verbindungsstatus anzeigen
- Passwörter nicht im Klartext in Logs oder GUI anzeigen

### Default-WLAN / Hausnetz

Als Voreinstellung soll das bereits bekannte Haus-WLAN verwendet werden.

OpenClaw soll bei der Einrichtung prüfen, ob auf dem System bereits ein funktionierendes NetworkManager-WLAN-Profil bzw. bekannte Zugangsdaten für das Hausnetz vorhanden sind. Wenn ja:

- diese SSID automatisch als Default in der WLAN-Seite vorauswählen;
- das dazugehörige Passwort sicher aus dem vorhandenen lokalen Verbindungsprofil bzw. Secret-Speicher übernehmen;
- die Verbindung beim ersten Start automatisch herstellen, sofern technisch möglich;
- das Passwort nicht in GitHub, Markdown oder Logs kopieren;
- die WLAN-Seite trotzdem so auslegen, dass SSID und Passwort später über Touch geändert werden können.

Falls beim Provisionieren noch kein bekanntes Hausnetz vorhanden ist, müssen SSID und Passwort einmalig lokal eingegeben bzw. bereitgestellt werden. Danach sollen sie sicher auf dem Zielsystem gespeichert bleiben.

## Einstellungen – System

- CPU-Auslastung, Arbeitsspeicher, CPU-Temperatur und Datenträgerbelegung live anzeigen
- Laufzeit, Hostname, Betriebssystem und aktive IP-Adressen anzeigen
- Systemdaten asynchron aktualisieren; die Touch-Oberfläche darf nicht blockieren
- je eine Touch-Schaltfläche für Neustart und Ausschalten bereitstellen
- beide Aktionen nur nach eindeutiger Sicherheitsabfrage ausführen

## Hauptreiter – MQTT Explorer

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

Für WLAN und Ethernet bevorzugt NetworkManager verwenden. Vorhandene NetworkManager-Verbindungsprofile sollen soweit möglich weitergenutzt werden, insbesondere das bekannte Haus-WLAN.

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
10. Installation, Autostart, Backup/Restore und Recovery dokumentiert sind;
11. beim Öffnen der Bildschirmtastatur das aktive Eingabefeld immer sichtbar bleibt;
12. vorhandene Haus-WLAN-Zugangsdaten sicher als Default übernommen werden können;
13. für spätere OpenClaw-Wartung benötigte lokale Credentials sicher erhalten bleiben und nicht in Git gelangen.

## Vorgehensweise

Arbeite in nachvollziehbaren Schritten. Lege zuerst Architektur, Verzeichnisstruktur, Konfigurationsformat, Mock-Daten und UI-Grundgerüst an. Implementiere danach MQTT, Live-Ansicht, Historie, Netzwerkseiten und MQTT Explorer. Verwende für Entwicklung ohne reale PFC/DAB einen MQTT-Simulator. Führe am Ende einen lokalen Funktionstest durch und dokumentiere offene Punkte.

Keine realen Topic-Namen erfinden: Platzhalter deutlich kennzeichnen, bis die MQTT-Explorer-Daten vorliegen.

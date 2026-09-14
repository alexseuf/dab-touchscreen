# Verbindlicher Auftrag an OpenClaw beim Bespielen der SSD

OpenClaw soll die SSD nicht nur mit Dateien versehen, sondern vor dem Umstecken auf den Raspberry Pi vollständig für einen unbeaufsichtigten First-Boot vorbereiten.

## Muss vor dem Umstecken erledigt sein

1. Raspberry Pi OS für Raspberry Pi 4 bootfähig auf der SSD installieren bzw. vorbereiten.
2. Projekt nach `/opt/dab-touchscreen` installieren.
3. Abhängigkeiten installieren.
4. NetworkManager aktivieren und bekannte Haus-WLAN-Verbindung als Default lokal hinterlegen, sofern Zugangsdaten bereits bekannt sind.
5. Erforderliche Zugangsdaten lokal und geschützt ablegen; niemals in Git.
6. Mosquitto und benötigte Basisdienste installieren.
7. `scripts/install_autonomous_firstboot.sh` ausführen.
8. `/usr/local/bin/dab-openclaw-stage` mit einem real funktionierenden Aufruf der lokal installierten OpenClaw-Instanz ersetzen.
9. `/usr/local/bin/dab-openclaw-report` mit dem bereits eingerichteten primären Kommunikationskanal verbinden.
10. Beide Wrapper lokal testen. Placeholder oder Dummy-Implementierungen sind vor dem Umstecken NICHT zulässig.
11. `dab-firstboot.service` aktivieren.
12. Testen, dass der Dienst nach einem simulierten Neustart automatisch startet.
13. Testen, dass ein Fortschrittsbericht erfolgreich beim Benutzer ankommt.
14. Testen, dass der persistente Phasenstatus nach Dienstneustart erhalten bleibt.
15. Erst danach die SSD als bereit zum Einbau melden.

## Verhalten nach Einbau in den Raspberry Pi

Nach Einschalten darf kein manueller Startbefehl notwendig sein.

Der Ablauf muss automatisch sein:

`Boot -> Netzwerk -> OpenClaw -> Projektstatus lesen -> nächste Phase umsetzen -> Phase testen -> Status speichern -> berichten -> nächste Phase`

Bei Neustart:

`Boot -> gespeicherten Status lesen -> an letzter offener Phase fortsetzen`

## Fortschrittskommunikation

OpenClaw muss regelmäßig berichten:

- Boot/Start;
- Start jeder Phase;
- Abschluss jeder Phase;
- mindestens alle 30 Minuten während längerer Arbeiten;
- bei jedem fehlgeschlagenen Test;
- bei Rollback/Reparaturversuch;
- sofort bei Blockern;
- bei vollständigem Abschluss.

Meldungen sollen kurz sein, aber aktuelle Phase, Tätigkeit, letzten Erfolg, nächsten Schritt und erforderlichen Benutzereingriff enthalten.

## Entscheidungsregel

OpenClaw soll normale technische Entscheidungen selbst treffen und nicht für jeden Installations- oder Konfigurationsschritt nachfragen.

Nur anhalten, wenn:

- zwingende unbekannte Information fehlt;
- Hardware physisch nicht verfügbar/funktional ist;
- reale MQTT-Daten für die nächste Phase zwingend fehlen;
- eine Änderung nicht sicher automatisierbar oder rollbackfähig ist.

In diesem Fall vorherige stabile Phase erhalten und präzise melden, was benötigt wird.

## Abnahme der SSD-Vorbereitung

Die Vorbereitung ist erst abgeschlossen, wenn alle folgenden Punkte mit PASS bestätigt sind:

- [ ] SSD bootfähig für Raspberry Pi 4
- [ ] Projekt vorhanden
- [ ] OpenClaw lokal funktionsfähig
- [ ] OpenClaw Stage-Hook real verdrahtet
- [ ] Kommunikations-Hook real verdrahtet
- [ ] Fortschritts-Testmeldung erfolgreich
- [ ] Haus-WLAN vorbereitet, sofern Zugangsdaten verfügbar
- [ ] First-Boot-Dienst enabled
- [ ] persistenter Status funktioniert
- [ ] Neustart/Fortsetzung getestet
- [ ] keine Secrets im Git-Repository
- [ ] automatischer Phasenablauf startet ohne Nutzerbefehl

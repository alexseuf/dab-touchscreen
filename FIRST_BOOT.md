# Autonomer First-Boot und selbstständige Projektumsetzung

## Ziel

Die SSD wird so vorbereitet, dass sie anschließend an den Raspberry Pi 4 angeschlossen werden kann und das System danach ohne manuellen Startbefehl selbstständig mit der phasenweisen Umsetzung und Inbetriebnahme beginnt.

Der Raspberry Pi soll nach jedem Neustart erkennen, welche Phase bereits erfolgreich abgeschlossen wurde, dort fortsetzen und nur bei einem echten Blocker anhalten.

## Grundprinzip

1. Raspberry Pi bootet von SSD.
2. `dab-firstboot.service` startet automatisch.
3. Der Orchestrator liest `/var/lib/dab-touchscreen/commissioning-state.json`.
4. Bereits erfolgreich abgeschlossene Phasen werden nicht erneut ausgeführt.
5. Die nächste offene Phase wird vorbereitet, umgesetzt und getestet.
6. Erst nach erfolgreichem Test wird die Phase als abgeschlossen gespeichert.
7. Danach wird automatisch mit der nächsten Phase fortgefahren.
8. Bei Fehlern erfolgen definierte Wiederholungsversuche.
9. Bei einem nicht automatisch lösbaren Fehler wird angehalten, der Fehler vollständig protokolliert und an den Benutzer gemeldet.
10. Nach Reboot wird automatisch an derselben Stelle fortgesetzt.

## Unbeaufsichtigter Betrieb

Die Umsetzung soll so weit wie technisch vertretbar ohne Nutzerinteraktion erfolgen. OpenClaw darf bekannte und bereits freigegebene lokale Zugangsdaten verwenden, Pakete installieren, Konfigurationsdateien erzeugen, Dienste aktivieren, Tests durchführen und Projektdateien ändern.

Keine Nutzerinteraktion soll für Routineaufgaben erforderlich sein.

Eine Rückfrage ist nur zulässig, wenn tatsächlich eine Information fehlt, die nicht lokal ermittelt werden kann oder wenn eine Änderung ein erhebliches Risiko birgt und nicht zuverlässig automatisch rückgängig gemacht werden kann.

## Persistenter Zustand

Statusdatei:

`/var/lib/dab-touchscreen/commissioning-state.json`

Beispiel:

```json
{
  "mode": "automatic",
  "current_stage": 3,
  "last_completed_stage": 2,
  "completed": [0, 1, 2],
  "failed": [],
  "retry_count": 0,
  "status": "running",
  "last_action": "mqtt mapping test",
  "updated_at": "2026-09-14T23:55:00+02:00"
}
```

Die Datei darf nicht im Git-Repository liegen.

## Fortschrittsmeldungen

OpenClaw soll den Benutzer regelmäßig über den Fortschritt informieren.

Pflichtmeldungen:

- beim ersten Start des Raspberry Pi;
- beim Beginn jeder Phase;
- beim erfolgreichen Abschluss jeder Phase;
- bei automatischen Reparaturversuchen;
- sofort bei einem Fehler oder Blocker;
- nach einem Reboot mit Angabe, an welcher Phase fortgesetzt wird;
- nach vollständigem Abschluss des Projekts.

Während eine Phase länger läuft, soll zusätzlich regelmäßig ein kurzer Fortschrittsbericht gesendet werden. Standard: alle 30 Minuten während aktiver Umsetzung. Der Zeitraum soll konfigurierbar sein.

Ein Fortschrittsbericht enthält mindestens:

- aktuelle Phase;
- aktuelle Tätigkeit;
- zuletzt erfolgreich abgeschlossener Schritt;
- Anzahl bisheriger Fehler/Wiederholungen;
- nächster geplanter Schritt;
- ob Benutzereingriff erforderlich ist.

Beispiel:

```text
DAB Touchscreen – Fortschritt
Phase 4/9: Historie und Diagramme
Status: läuft
Aktuell: SQLite-Persistenztest
Zuletzt erfolgreich: MQTT Live-Daten
Nächster Schritt: Touch-Zoom testen
Benutzereingriff: nein
```

## Meldekanäle

Primär soll OpenClaw den bereits eingerichteten Kommunikationskanal verwenden, über den der Benutzer OpenClaw normalerweise erreicht.

Zusätzlich lokal:

- Journal: `journalctl -u dab-firstboot.service`
- Datei: `/var/log/dab-touchscreen/commissioning.log`
- Statusdatei: `/var/lib/dab-touchscreen/commissioning-state.json`

Optional zusätzlich MQTT-Statuspublikation:

- `dab-touchscreen/status/commissioning`
- `dab-touchscreen/status/stage`
- `dab-touchscreen/status/progress`
- `dab-touchscreen/status/error`

Retained Messages sind für den letzten Gesamtstatus sinnvoll.

## Fehlerbehandlung

Fehler werden in drei Klassen eingeteilt:

### transient
Beispiele: Netzwerk kurz nicht verfügbar, apt mirror nicht erreichbar, MQTT noch nicht gestartet.

- automatisch wiederholen;
- exponentielles Backoff;
- standardmäßig maximal 5 Versuche.

### recoverable
Beispiele: fehlerhafte Konfiguration, Dienst startet nach Änderung nicht.

- letzte Änderung rückgängig machen;
- vorherige funktionierende Konfiguration wiederherstellen;
- erneut testen;
- Fehler melden.

### blocker
Beispiele: Hardware fehlt, unbekanntes reales MQTT-Datenformat, zwingend benötigte Zugangsdaten fehlen.

- Phase stoppen;
- vorherige stabile Phase weiter funktionsfähig halten;
- Fehler und benötigte Information eindeutig melden;
- nicht blind mit späteren Phasen fortfahren.

## Rollback

Vor jeder riskanten Systemänderung:

- betroffene Konfigurationsdatei sichern;
- vorhandene Netzwerkkonfiguration sichern;
- funktionierende Anwendungsversion markieren;
- danach Änderung durchführen und testen.

Bei Fehlschlag automatischer Rollback.

## Abschluss

Nach erfolgreichem Abschluss aller Phasen:

- `commissioning_mode` auf `false` setzen;
- Produktionsdienste aktivieren;
- First-Boot-Orchestrator deaktivieren;
- Abschlussbericht senden;
- Diagnose- und Wartungsfunktionen weiterhin verfügbar lassen.

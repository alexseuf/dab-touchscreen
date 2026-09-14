# Schrittweise Inbetriebnahme

Die Anwendung muss so aufgebaut werden, dass jede Funktion separat getestet und freigegeben werden kann. Eine fehlerhafte spätere Stufe darf bereits geprüfte Grundfunktionen nicht unbrauchbar machen.

## Grundprinzip

Jede Stufe besitzt:

- klar definierte Voraussetzungen;
- einen eigenen Start-/Testmodus;
- sichtbare Diagnoseinformationen;
- eindeutige Abnahmekriterien;
- einen dokumentierten Rückfall auf die vorherige Stufe.

Die aktive Stufe wird über `config/commissioning.yaml` festgelegt. Nicht freigegebene Funktionen bleiben deaktiviert bzw. werden in der GUI eindeutig als `noch nicht in Betrieb` angezeigt.

## Stufe 0 – Betriebssystem / Hardware

Ziel:

- Raspberry Pi startet zuverlässig von der vorgesehenen SSD;
- Displayauflösung und Touch funktionieren;
- Ethernet/WLAN-Interfaces werden erkannt;
- Uhrzeit/Zeitzone stimmen;
- freier SSD-Speicher wird erkannt.

Test:

```bash
python3 scripts/commissioning_check.py --stage 0
```

Keine MQTT- oder HMI-Funktion ist für diese Stufe erforderlich.

## Stufe 1 – GUI offline

Ziel:

- GUI startet fullscreen;
- alle fünf Reiter sind erreichbar;
- Touch funktioniert;
- Bildschirmtastatur funktioniert;
- aktives Eingabefeld bleibt bei eingeblendeter Tastatur sichtbar;
- alle Messwerte werden zunächst aus lokalen Demo-Daten gespeist.

MQTT, Netzwerkänderungen und Datenbankzugriff können deaktiviert bleiben.

Start:

```bash
python3 -m src.main --stage 1
```

## Stufe 2 – Lokaler MQTT-Broker

Ziel:

- Mosquitto läuft lokal;
- GUI kann `localhost:1883` verbinden;
- MQTT-Simulator veröffentlicht Testwerte;
- Live-Anzeige reagiert auf MQTT-Testdaten;
- Broker-Ausfall führt nicht zum GUI-Absturz.

Zusätzlicher Test:

```bash
python3 scripts/commissioning_check.py --stage 2
```

## Stufe 3 – Reale MQTT-Daten

Ziel:

- reale PFC/DAB-Topics werden anhand MQTT Explorer zugeordnet;
- Topic-Mapping liegt ausschließlich in Konfiguration;
- Werte, Einheit, Datentyp und Datenalter werden geprüft;
- fehlende Topics werden als `nicht verfügbar` dargestellt;
- keine erfundenen Ersatzwerte.

Erst nach erfolgreicher Prüfung werden die jeweiligen Kanäle in der Live-Ansicht als freigegeben markiert.

## Stufe 4 – Historie / Diagramme

Ziel:

- lokale Speicherung funktioniert;
- Retention/Downsampling geprüft;
- Diagramme zeigen Live- und historische Daten;
- Zoom, Pan und Reset funktionieren auf Touch;
- Neustart der GUI verliert gespeicherte Historie nicht.

## Stufe 5 – LAN-Konfiguration

Ziel:

- aktuelle Ethernet-Konfiguration zunächst nur lesen und anzeigen;
- anschließend DHCP-Umschaltung testen;
- erst danach feste IPv4-Adresse, Gateway und DNS freigeben;
- Eingaben validieren;
- bei fehlerhaften Einstellungen Recovery ermöglichen.

Wichtig: Schreibender Netzwerkzugriff wird erst in dieser Stufe aktiviert.

## Stufe 6 – WLAN-Konfiguration

Ziel:

- verfügbare SSIDs scannen;
- vorhandenes bekanntes Haus-WLAN als Default verwenden;
- WLAN-Verbindung lesen/anzeigen;
- anschließend Verbinden/Trennen und Änderung von Zugangsdaten testen;
- Passwörter ausschließlich lokal sicher speichern;
- Touch-Tastatur darf das Passwortfeld nicht verdecken.

## Stufe 7 – MQTT Explorer

Ziel:

- Topic-Baum dynamisch aufbauen;
- Payload/QoS/Retain/Timestamp anzeigen;
- hohe Nachrichtenrate darf GUI nicht blockieren;
- Such-/Filterfunktion prüfen.

## Stufe 8 – Autostart / Dauerbetrieb

Ziel:

- systemd-Dienst startet Broker und GUI automatisch;
- definierte Startreihenfolge;
- automatischer Reconnect;
- Verhalten nach Stromausfall testen;
- Logs rotieren;
- mindestens ein mehrstündiger Dauerlauftest.

## Stufe 9 – Produktionsbetrieb

Erst nach Freigabe aller benötigten Stufen:

- `commissioning_mode: false`
- alle freigegebenen Funktionen aktiv
- Diagnosebanner ausblenden
- Wartungs-/Diagnosemenü weiterhin erreichbar

## Freigabeprinzip

OpenClaw darf eine Stufe erst als abgeschlossen markieren, wenn deren Prüfpunkte erfolgreich getestet wurden. Der Status soll in einer lokalen Datei, z. B. `/var/lib/dab-touchscreen/commissioning-state.json`, gespeichert werden.

Beispiel:

```json
{
  "last_completed_stage": 3,
  "completed": [0, 1, 2, 3],
  "failed": [],
  "updated_at": "2026-09-14T23:00:00+02:00"
}
```

Dieser Laufzeitstatus gehört nicht ins Git-Repository.

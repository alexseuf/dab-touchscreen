# MQTT-Konzept

## Grundsatz

Die realen Topic-Namen und Payload-Formate werden später anhand der tatsächlichen MQTT-Explorer-Darstellung festgelegt. Bis dahin keine vermeintlich realen Topics fest in die Anwendung codieren.

## Mapping

Die GUI soll intern mit stabilen Signal-IDs arbeiten, zum Beispiel:

```yaml
signals:
  grid_voltage_l1:
    topic: "TODO"
    unit: "V"
    value_path: null
  grid_current_l1:
    topic: "TODO"
    unit: "A"
    value_path: null
  dc_link_voltage:
    topic: "TODO"
    unit: "V"
    value_path: null
  output_voltage:
    topic: "TODO"
    unit: "V"
    value_path: null
```

`value_path` kann später verwendet werden, falls ein MQTT-Payload mehrere Werte als JSON enthält.

## Zu erfassende Metadaten

Für jede empfangene Nachricht soweit verfügbar speichern/anzeigen:

- Topic
- Payload roh
- Empfangszeit
- QoS
- Retain
- dekodierter Wert/JSON
- Parse-Status

## Robustheit

- Broker-Reconnect automatisch
- Wildcard-Abonnement für Explorer-Ansicht getrennt von Signal-Mappings behandeln
- Nachrichtenverarbeitung nicht im GUI-Thread blockieren
- maximale Payload-Größe definieren
- hohe Topic-/Nachrichtenrate begrenzen bzw. UI-seitig drosseln
- unbekannte Topics dürfen nicht zum Fehler führen

## Broker

Vorläufig:

- Mosquitto lokal
- TCP Port 1883
- unverschlüsseltes MQTT im lokalen Netz gewünscht
- spätere Entscheidung zu Benutzername/Passwort und erlaubten Interfaces

## Zweiter Projektschritt

Benötigt werden Screenshots/Export aus MQTT Explorer mit:

1. vollständigem relevanten Topic-Baum,
2. Beispiel-Payload jedes benötigten Signals,
3. Information, ob Werte retained sind,
4. typischer Aktualisierungsrate,
5. ggf. QoS,
6. Quelle/Gerät der Topics.

Danach wird das Mapping vervollständigt und die Mock-Daten werden an die reale Struktur angepasst.

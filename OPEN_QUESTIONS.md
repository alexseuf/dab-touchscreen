# Offene Punkte / Lücken

Diese Punkte sollten vor bzw. während der Implementierung geklärt werden. Sie blockieren nicht zwingend den Aufbau eines Mockups.

- Exaktes 7"-Display-Modell und tatsächliche Auflösung/Touch-Treiber
- Raspberry-Pi-OS-Version und gewünschte Desktop-/Kiosk-Basis
- Reale MQTT-Topic-Namen und Payload-Formate
- Aktualisierungsrate der einzelnen Messwerte
- Sind Zeitstempel bereits im Payload enthalten oder gilt Empfangszeit?
- Gewünschte Historiedauer: Stunden, Tage, Wochen?
- Gewünschte Abtastrate/Downsampling der Historie
- Alarm-/Warnschwellen für Spannung, Strom und Temperaturen
- Sollen Grenzwertverletzungen nur angezeigt oder auch per MQTT publiziert werden?
- MQTT-Zugriff nur LAN/WLAN lokal oder auch über andere Netze?
- Broker anonym erreichbar oder Benutzer/Passwort?
- Muss TLS später unterstützt werden?
- Feste Ethernet-IP: konkrete Default-IP, Netzmaske, Gateway und DNS
- Soll WLAN parallel zu Ethernet aktiv bleiben?
- Priorität/Routing, wenn Ethernet und WLAN gleichzeitig verbunden sind
- Wie soll Recovery erfolgen, wenn eine falsche feste IP konfiguriert wurde?
- Soll die GUI selbst Netzwerkparameter ändern dürfen (erfordert privilegierten Helper) oder soll dies über einen getrennten Systemdienst erfolgen?
- Maximale erwartete Anzahl MQTT-Topics und Nachrichtenrate für Explorer-Ansicht
- Soll MQTT Explorer nur live anzeigen oder Nachrichtenhistorie pro Topic speichern?
- Gewünschte Zahlenformate/Nachkommastellen je Messgröße
- Gewünschte Sprache ausschließlich Deutsch?
- Soll es Benutzerrollen/PIN-Schutz für Netzwerk- und MQTT-Einstellungen geben?
- Verhalten bei Stromausfall und Bedarf an Read-only-/Overlay-Dateisystem
- Bedarf für Export von Logs/Historie auf USB oder über Netzwerk
- Remote-Wartung, z. B. SSH, gewünscht?

## Empfehlung

Für die erste Implementierung mit Mock-Daten sollten sichere Defaults verwendet und alle unbekannten Punkte als Konfiguration statt als fest verdrahtete Annahmen umgesetzt werden.

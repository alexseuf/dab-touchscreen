# UI-Spezifikation – 7" Touchdisplay

## Allgemein

Zielauflösung vorläufig 1024×600 im Querformat. Dark-Theme, hohe Kontraste, große Touch-Flächen. Oben permanent eine Tab-Leiste:

`Übersicht | Verläufe | Netzwerk (LAN) | WLAN | MQTT Explorer`

Statusleiste unten oder kompakt im Header: Brokerstatus, Ethernet/WLAN, Datenalter, Uhrzeit.

## 1. Übersicht

Zentrale schematische Darstellung:

```text
  3~ Netz              PFC             Zwischenkreis             DAB              DC-Ausgang
┌──────────┐       ┌──────────┐          ┌─────┐             ┌──────────┐        ┌──────────┐
│ L1 L2 L3 │ ────▶ │ 3~ → DC  │ ───────▶ │ Cdc │ ──────────▶ │ DC ↔ DC  │ ─────▶ │ U / I / P│
└──────────┘       └──────────┘          └─────┘             └──────────┘        └──────────┘
 U1 U2 U3           Pin / T_PFC            Udc                Tpri / Tsec         Uout Iout Pout
 I1 I2 I3                                                                 
 f
```

Unterer Bereich: Temperaturkarten für PFC, Drossel, DAB primär, DAB sekundär und Trafo. Ungültige/veraltete Werte grau oder eindeutig markiert; Alarmfarben erst verwenden, wenn Grenzwerte definiert sind.

## 2. Verläufe

- Plotfläche maximal groß
- Zeitachse horizontal
- auswählbare Kurven
- gruppierte Skalen: Spannung, Strom, Leistung, Temperatur
- Touch-Gesten für Zoom/Pan
- Buttons `1 min`, `10 min`, `1 h`, `6 h`, `24 h`, `Reset`
- Tooltip/Cursor für Werte an einem Zeitpunkt, sofern touch-tauglich

## 3. LAN / MQTT

Linke Hälfte: Ethernet. Rechte Hälfte: Broker.

Ethernet: DHCP/Fest, IP, Prefix/Netzmaske, Gateway, DNS, aktuelle Adresse, Linkstatus.

Broker: läuft/gestoppt, Port, Authentifizierung, Anzahl verbundener Clients sofern leicht verfügbar. Einstellungen mit `Übernehmen` und klarer Fehlerausgabe.

## 4. WLAN

Dreispaltig oder zweispaltig:

- Liste gescannter SSIDs mit Signalstärke
- Zugangsdaten/Verbinden
- aktueller Status mit SSID, RSSI, IP-Adresse

Passwortfeld standardmäßig verdeckt, optional kurz sichtbar schaltbar.

## 5. MQTT Explorer

Für 1024×600 bevorzugt Split-View:

- links ca. 40 %: scrollbarer Topic-Baum
- rechts ca. 60 %: Details des selektierten Topics

Detailbereich: Topic, letzter Payload, Zeitstempel/Alter, QoS, Retain, Rohansicht und formatierte JSON-Ansicht. Oben Suchfeld. Bei sehr vielen Updates Detailansicht begrenzen/drosseln.

## Responsivität

Die Anwendung soll nicht auf exakt 1024×600 fest codiert werden. Layouts müssen bei abweichender Displayauflösung skalieren. Mindestschriftgröße und Touch-Zielgröße sollen auf dem realen Display geprüft werden.

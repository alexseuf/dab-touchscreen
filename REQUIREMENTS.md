# Anforderungen

## Zielplattform

- Raspberry Pi 4
- Raspberry Pi OS 64 Bit, sofern keine spätere Randbedingung dagegen spricht
- 7" Touchdisplay, vorläufig 1024×600 Pixel
- USB-SSD 100 GB
- Ethernet + WLAN
- Bedienung ohne externe Tastatur/Maus im Normalbetrieb

## Messwerte

| Signal | Einheit | Darstellung |
|---|---:|---|
| Netzspannung L1/L2/L3 RMS | V | Live + Verlauf |
| Netzstrom L1/L2/L3 RMS | A | Live + Verlauf |
| Netzfrequenz | Hz | Live + Verlauf |
| Eingangsleistung | W/kW | Live + Verlauf |
| Zwischenkreisspannung | V | Live + Verlauf |
| Ausgangsspannung | V | Live + Verlauf |
| Ausgangsstrom | A | Live + Verlauf |
| Ausgangsleistung | W/kW | Live + Verlauf |
| Temperatur PFC | °C | Live + Verlauf |
| Temperatur DAB primär | °C | Live + Verlauf |
| Temperatur DAB sekundär | °C | Live + Verlauf |
| Drosseltemperatur | °C | Live + Verlauf |
| Trafotemperatur | °C | Live + Verlauf |

## Qualitätsanforderungen

- GUI darf durch MQTT-Reconnects oder ungültige Payloads nicht blockieren.
- Daten benötigen einen Status: gültig, veraltet/stale, ungültig, noch nie empfangen.
- Update der sichtbaren GUI entkoppelt von MQTT-Nachrichtenrate; keine unnötigen Repaints pro Nachricht.
- Konfigurationsänderungen atomar speichern.
- Logs mit Rotation, damit die SSD nicht vollläuft.
- Historiedaten mit definierbarer Retention und optionalem Downsampling.
- Passwörter/Secrets nicht in Git committen.
- Service-Autostart über systemd.
- Watchdog/Restart-Policy für Broker und HMI vorsehen.
- Systemzeit und Zeitzone sauber behandeln; intern möglichst Zeitstempel eindeutig speichern.

## Bedienung

- Touch-Ziele ausreichend groß für 7".
- Dark-Theme bevorzugt für technische HMI.
- Kopfzeile mit fünf Reitern.
- Kritische Zustände klar sichtbar, aber keine Alarmgrenzen erfinden.
- Virtuelle Tastatur für IP-, Passwort- und Texteingaben.
- Netzwerkänderungen nur nach Plausibilitätsprüfung.

## Testbarkeit

Ein MQTT-Testpublisher muss realistische synthetische Daten erzeugen können, damit die komplette Oberfläche ohne angeschlossene Leistungselektronik getestet werden kann. Der Simulator soll dieselbe Mapping-Schicht wie spätere reale Topics verwenden.

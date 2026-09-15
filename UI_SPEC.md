# UI-Spezifikation – offizielles 7" Raspberry-Pi-Touchdisplay

## Verbindliche Zielauflösung

Die reale Zielhardware ist das offizielle 7-Zoll-Raspberry-Pi-Touchdisplay der ersten Generation mit **800×480 Pixeln im Querformat**. Alle Referenzbilder, Layouts und Abnahmetests werden primär für 800×480 ausgelegt. 1024×600 darf nicht mehr als Designgrundlage verwendet werden.

## Verbindliche Navigation

Hauptnavigation:

`Übersicht | Verläufe | MQTT Explorer | ⚙ Einstellungen`

Beim Öffnen von **⚙ Einstellungen** ersetzt folgende zweite Ebene die Hauptnavigation vollständig:

`Netzwerk (LAN) | WLAN | System | ← Zurück`

Beide Ebenen werden niemals gleichzeitig angezeigt. **← Zurück** kehrt zur Hauptnavigation zurück.

## Inhaltstreue der Referenzbilder

Die vorhandenen Seiteninhalte dürfen beim Umstellen der Referenzgrafiken auf 800×480 **nicht inhaltlich verändert werden**. Werte, Funktionen, Felder und Informationsumfang bleiben erhalten. Zulässig sind Skalierung, Positionierung, Abstände, Schriftgrößen und andere rein visuelle Anpassungen, die erforderlich sind, um denselben Inhalt auf 800×480 darzustellen. Die Navigation selbst wird an die tatsächlich implementierte Haupt-/Einstellungsstruktur angepasst.

## Framework und Styling

Ziel-Framework ist **PySide6 oder PyQt6 (Qt)**, Diagramme vorzugsweise **PyQtGraph**. Die SVG-Dateien unter `docs/images/` sind direkt gestaltete Design-Mock-ups; sie stammen nicht aus einem anderen GUI-Framework. Deshalb können Kanten, Abstände und Typografie in den SVGs zunächst eleganter wirken als in der laufenden Qt-Anwendung.

Die bisherigen SVG-Mock-ups verwenden überwiegend `Arial` bzw. `Arial, sans-serif`, für technische Baum-/Rohdaten teilweise `monospace`. Arial ist auf Raspberry Pi OS nicht zuverlässig als identische Systemschrift vorhanden. Für die reale Qt-Oberfläche ist deshalb **DejaVu Sans** als reproduzierbarer primärer Font vorgesehen, mit `sans-serif` als Fallback. Technische Rohdaten können **DejaVu Sans Mono** verwenden. Wird auf dem Zielsystem nachweislich ein anderer bereits installierter Font verwendet, muss er dokumentiert und Mock-up/Qt gemeinsam darauf umgestellt werden; keine stillen Font-Unterschiede.

QSS soll die reale GUI an die SVG-Referenzen angleichen: Dark-Theme, klare blaue Navigation, dezente Rahmen, konsistente Innenabstände und ausgewogene Typografie. Keine rein dekorative Änderung darf Funktion oder Seiteninhalt verändern.

## Größen für 800×480

Touch-Ziele bevorzugt mindestens 44–48 px hoch/breit. Normale UI-Schrift etwa 16–20 px, Überschriften/Werte entsprechend größer. Diese Werte sind Richtwerte; entscheidend ist der Test auf dem realen Display. Lange Beschriftungen nicht durch extrem kleine Schrift erzwingen.

## 1. Übersicht

Energiefluss Netz → PFC → Zwischenkreis → DAB → DC-Ausgang mit den vorhandenen Live-Werten und Temperaturen. Inhalt nicht reduzieren; Layout auf 800×480 anpassen.

## 2. Verläufe

Vorhandene Plot-Inhalte, Zeitbereiche, Kurven und Funktionen beibehalten. Plotfläche bei 800×480 maximal nutzen. Zoom/Pan per Touch.

## 3. MQTT Explorer

Vorhandenen Topic-Baum, Filter und Detailinhalt beibehalten. Split-View für 800×480 optimieren, ohne Informationen aus dem Referenzbild zu entfernen.

## 4. Einstellungen

### 4.1 Netzwerk (LAN)

Vorhandene Ethernet-/Brokerinformationen und Eingabefelder beibehalten. Bildschirmtastatur darf aktives Feld nicht verdecken.

### 4.2 WLAN

Vorhandene SSID-, Verbindungs-, Passwort-, Signal- und IP-Inhalte beibehalten. Bildschirmtastatur verschiebt/scrollt das aktive Feld sichtbar.

### 4.3 System

CPU-Auslastung, Arbeitsspeicher, CPU-Temperatur, Datenträgerbelegung, Hostname, Betriebssystem/Laufzeit und Netzwerkadressen darstellen. Neustart und Ausschalten als große Touch-Schaltflächen; beide Aktionen mit Sicherheitsabfrage.

### 4.4 Zurück

Stellt die Hauptnavigation wieder her.

## Responsivität und Abnahme

Jede Haupt- und Einstellungsansicht muss auf einem echten 800×480-Framebuffer bzw. mit einem exakt 800×480 großen Referenz-SVG geprüft werden. Kein horizontaler Scrollbalken in Hauptansichten. Wesentliche Bedienelemente müssen touch-tauglich sein. Die Bildschirmtastatur darf das aktive Feld nicht verdecken. Höhere Auflösungen dürfen zusätzlichen Raum nutzen, aber keine Funktion darf mehr als 800×480 voraussetzen.

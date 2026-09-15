# UI-Spezifikation – offizielles 7" Raspberry-Pi-Touchdisplay

## Verbindliche Zielauflösung

Die reale Zielhardware ist das offizielle 7-Zoll-Raspberry-Pi-Touchdisplay der ersten Generation mit **800×480 Pixeln im Querformat**. Alle Referenzbilder, Layouts und Abnahmetests müssen deshalb primär für **800×480** entworfen werden. 1024×600 darf nicht mehr als Designgrundlage verwendet werden.

Dark-Theme, hohe Kontraste, große Touch-Flächen. Keine Referenzgrafik darf mehr Informationen zeigen, als bei 800×480 sinnvoll lesbar und bedienbar umgesetzt werden können. Mindest-Touchziel ca. 48×48 px, normale UI-Schrift bevorzugt 16–20 px, wichtige Werte größer. Lange Beschriftungen kürzen statt Schrift unlesbar klein zu skalieren.

Oben permanent eine kompakte Tab-Leiste:

`Übersicht | Verläufe | LAN/MQTT | WLAN | MQTT`

Status kompakt im Header oder Footer: Brokerstatus, Ethernet/WLAN, Datenalter, Uhrzeit. Vertikalen Platz sparsam verwenden.

## 1. Übersicht

Energiefluss Netz → PFC → Zwischenkreis → DAB → DC-Ausgang. Nur die wichtigsten Live-Werte gleichzeitig zeigen. Temperaturen kompakt in einer unteren Zeile bzw. Karten. Detailwerte über Touch aufrufen statt die Hauptseite zu überladen.

## 2. Verläufe

Plotfläche maximal groß. Zeitbereich über große Touch-Schaltflächen; Kurvenauswahl ggf. über Dialog. Zoom/Pan per Touch. Achsenbeschriftungen auf 800×480 reduzieren. Legende kompakt.

## 3. LAN / MQTT

Bei 800×480 keine überladene Desktop-Zweispaltenansicht. Ethernet und Broker in zwei klaren Bereichen mit nur den unmittelbar relevanten Feldern. Erweiterte Einstellungen können über Unterdialoge geöffnet werden. Bildschirmtastatur muss das aktive Eingabefeld sichtbar lassen; Inhalt bei Bedarf nach oben verschieben/scrollen.

## 4. WLAN

Zweispaltig: links SSID-Liste, rechts Verbindung/Status. Zeilen und Buttons touch-tauglich. Passwortfeld verdeckt, optional sichtbar. Bei Bildschirmtastatur muss das aktive Feld oberhalb der Tastatur sichtbar bleiben.

## 5. MQTT Explorer

Bei 800×480 Split-View ungefähr 38/62 %. Links Topic-Baum, rechts selektiertes Topic/Payload. Detailinformationen priorisieren; QoS/Retain/Zeit kompakt. Roh-/JSON-Ansicht darf scrollen. Suchfeld ggf. als aufklappbare Funktion, damit nicht dauerhaft wertvolle Höhe verloren geht.

## Responsivität und Abnahme

800×480 ist die verbindliche Referenz. Höhere Auflösungen dürfen zusätzlichen Raum nutzen, aber keine Funktion darf 1024×600 voraussetzen. Jede Hauptansicht muss mit einem echten 800×480-Screenshot bzw. einem exakt 800×480 großen Referenz-SVG geprüft werden. Kein horizontaler Scrollbalken in Hauptansichten; wesentliche Bedienelemente müssen ohne Scrollen erreichbar sein. Touch-Tastatur darf das bearbeitete Feld nicht verdecken.

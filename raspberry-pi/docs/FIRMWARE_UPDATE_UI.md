# Firmware-Update und Firmware-Menü

## Ziel

Der DAB-Touchscreen erhält unter **Einstellungen → Firmware** eine eigene Seite zur Anzeige und späteren Verwaltung der installierten Softwareversion. Die Entwicklung erfolgt zunächst ausschließlich auf `feature/firmware-update-ui`; `main` bleibt bis zu einem geprüften Pull Request unverändert.

## Bedienoberfläche

Die Firmware-Seite soll sechs klar getrennte Bereiche enthalten:

1. **Datenquelle**
   - Umschaltung zwischen realen MQTT-Daten und Demomodus.
   - Aktiver Modus muss eindeutig sichtbar sein.

2. **GitHub-Projekt**
   - Anzeige des verwendeten Repositorys `alexseuf/dab-touchscreen`.
   - Architektur so auslegen, dass das Repository später konfigurierbar sein kann.

3. **Firmware-Versionen**
   - Installierte Firmware-Version anzeigen.
   - Schaltfläche **Auf Updates prüfen**.
   - Neueste auf GitHub verfügbare Version anzeigen.
   - Eindeutige Anzeige, wenn eine neuere Version verfügbar ist.

4. **Zielversion**
   - Verfügbare Firmware-Version auswählen.
   - Sowohl Update als auch Downgrade ermöglichen.
   - Aktuell installierte Version in der Auswahl eindeutig kennzeichnen.

5. **Update/Downgrade starten**
   - Gewählte Version erst nach bewusster Benutzeraktion installieren.
   - Während des Vorgangs Fortschritt und Status anzeigen.
   - Mehrfaches paralleles Starten verhindern.

6. **Hinweise und Status**
   - Internet-/GitHub-Erreichbarkeit anzeigen.
   - Über automatischen Neustart informieren.
   - Status, Fehler und Rollback-Ergebnis verständlich anzeigen.
   - Lokale Konfiguration und Secrets dürfen bei Firmwarewechseln nicht verloren gehen.

## Sicherheits- und Update-Anforderungen

Der Updater darf nicht lediglich blind `git pull` ausführen. Vor einer Änderung muss er den aktuellen funktionsfähigen Stand identifizieren und eine Rückkehr dorthin ermöglichen.

Vorgesehener Ablauf:

1. Erreichbarkeit von GitHub und Repository prüfen.
2. Installierte Version und verfügbaren Zielstand bestimmen.
3. Prüfen, ob der Arbeitsbaum bzw. die Installation einen sicheren Wechsel zulässt.
4. Aktuellen funktionsfähigen Git-Stand als Rollback-Referenz sichern.
5. Lokale Secrets und persistente Laufzeitdaten außerhalb des austauschbaren Quellstands belassen.
6. Abhängigkeiten der Zielversion prüfen.
7. Bei unveränderten Systempaketen den normalen Updatepfad verwenden.
8. Bei neuen oder geänderten Systempaketen den vollständigen Installer ausführen.
9. Compile-/Integritätsprüfung und vorhandene Tests ausführen.
10. Dienste bzw. grafische Sitzung kontrolliert neu starten.
11. Nach dem Start einen Health-Check durchführen.
12. Bei fehlgeschlagenem Update auf den zuvor gesicherten Stand zurückkehren und den Fehler anzeigen.

## Bestehende Grundlage

Der aktuelle Stand trennt bereits:

- Git-Repository/Quellcode,
- installierte Anwendung unter `/opt/dab-touchscreen`,
- lokale Konfiguration und Secrets unter `/etc/dab-touchscreen`,
- persistente Laufzeitdaten unter `/var/lib/dab-touchscreen`.

`raspberry-pi/update.sh` verwendet derzeit den idempotenten Installer mit `--no-apt`. Wenn eine Version neue oder geänderte Systempakete benötigt, ist der vollständige `raspberry-pi/install.sh` erforderlich. Der zukünftige Updater soll diese Entscheidung automatisieren.

## Versionsmodell

Für die eigentliche Implementierung soll ein eindeutiges Versionsmodell eingeführt werden. Bevorzugt werden Git-Tags/Releases im Format `vMAJOR.MINOR.PATCH`, beispielsweise `v1.3.0`. Die Anwendung soll zusätzlich den tatsächlich installierten Git-Commit erfassen können, damit auch Entwicklungsstände eindeutig diagnostizierbar bleiben.

Ein Downgrade darf nur auf Versionen angeboten werden, die als unterstützte Firmware-Version erkannt werden.

## Nicht Bestandteil des ersten Implementierungsschritts

Zunächst werden UI, Versionsanzeige und GitHub-Abfrage getrennt vom eigentlichen privilegierten Installationsvorgang implementiert und getestet. Ein Firmwarewechsel darf erst aktiviert werden, wenn Backup/Rollback, Abhängigkeitsprüfung und Health-Check vorhanden sind.

## Akzeptanzkriterien

- Firmware-Reiter ist auf dem 7-Zoll-Touchscreen vollständig bedienbar.
- Reale MQTT-Daten und Demomodus sind umschaltbar.
- Repository, installierte Version und neueste verfügbare Version werden angezeigt.
- Versionsabfrage verändert das System nicht.
- Update und Downgrade verwenden nur validierte Zielversionen.
- Lokale Secrets und Laufzeitdaten bleiben erhalten.
- Neue Paketabhängigkeiten werden erkannt und korrekt behandelt.
- Fehlgeschlagene Installation kann automatisch auf den letzten funktionsfähigen Stand zurückgesetzt werden.
- Benutzer erhält während des gesamten Vorgangs verständliche Statusmeldungen.
- Keine Änderung an `main`, bevor die Funktion über einen separaten Pull Request geprüft wurde.

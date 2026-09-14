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
12. SSH vollständig vorbereiten und das vorgesehene Administrationskonto prüfen:
    - Benutzer existiert;
    - Benutzer ist **nicht gesperrt** (`passwd -S <user>` darf keinen Status `L` liefern);
    - Home-Verzeichnis und `~/.ssh` besitzen korrekte Eigentümer/Rechte;
    - der öffentliche OpenClaw-SSH-Key steht in `~/.ssh/authorized_keys`;
    - `sshd` ist aktiviert und startet beim Boot;
    - Passwort-Login darf deaktiviert bleiben, sobald Public-Key-Login funktionsfähig vorbereitet ist.
13. Falls das Konto nach dem Image-/Provisioning-Schritt gesperrt ist, muss OpenClaw es **vor dem ersten Boot** entsperren. Dabei kein leeres Passwort erzeugen. Entweder ein bereits lokal geschütztes Passwort/Hash setzen oder einen vorhandenen gültigen Hash verwenden und danach Public-Key-Login sicherstellen.
14. Display- und Touch-Ausrichtung als Systemparameter vorbereiten. Für dieses Projekt ist die Sollausrichtung **180°**. Display und Touch müssen gemeinsam gedreht werden, damit Anzeige und Touch-Koordinaten übereinstimmen.
15. Testen, dass der First-Boot-Dienst nach einem simulierten Neustart automatisch startet.
16. Testen, dass ein Fortschrittsbericht erfolgreich beim Benutzer ankommt.
17. Testen, dass der persistente Phasenstatus nach Dienstneustart erhalten bleibt.
18. Erst danach die SSD als bereit zum Einbau melden.

## Verbindlicher SSH-Preflight

Vor dem Aushängen der SSD muss OpenClaw mindestens folgende Prüfungen durchführen und protokollieren:

```text
PASS user_exists
PASS account_unlocked
PASS sshd_enabled
PASS authorized_keys_present
PASS ssh_permissions
PASS display_rotation_180_configured
PASS touch_rotation_180_configured
```

Ein vorhandener Benutzer allein gilt **nicht** als ausreichend. Ein gesperrtes Konto führt bei OpenSSH je nach PAM-/sshd-Konfiguration dazu, dass auch ein korrekter Public Key abgewiesen wird. Deshalb ist `account_unlocked` ein eigener Pflicht-Test.

Empfohlene Offline-Prüfung am gemounteten Root-Dateisystem:

```bash
chroot /mnt/dab-root getent passwd <user>
chroot /mnt/dab-root passwd -S <user>
chroot /mnt/dab-root systemctl is-enabled ssh
stat /mnt/dab-root/home/<user>/.ssh
stat /mnt/dab-root/home/<user>/.ssh/authorized_keys
```

Falls `passwd -S <user>` den Status `L` meldet, darf die SSD nicht als fertig gemeldet werden. Die sichere Reparatur ist in `docs/SSH_BLACK_SCREEN_RECOVERY.md` beschrieben.

## Verhalten nach Einbau in den Raspberry Pi

Nach Einschalten darf kein manueller Startbefehl notwendig sein.

Der Ablauf muss automatisch sein:

`Boot -> Netzwerk -> SSH/Remotezugriff prüfen -> OpenClaw -> Projektstatus lesen -> nächste Phase umsetzen -> Phase testen -> Status speichern -> berichten -> nächste Phase`

Bei Neustart:

`Boot -> gespeicherten Status lesen -> an letzter offener Phase fortsetzen`

Der Hostname `dab-touchscreen.local` ist für die Administration zu bevorzugen. Eine per DHCP vergebene IPv4-Adresse darf zusätzlich erkannt und gemeldet werden, darf aber nicht hart als dauerhaft feste Adresse vorausgesetzt werden.

## Remote-Diagnose nach dem ersten Boot

Sobald Netzwerk verfügbar ist, führt OpenClaw zuerst einen Remote-Preflight aus:

1. Hostname per mDNS und aktuelle IPv4 ermitteln.
2. Ping bzw. Erreichbarkeit prüfen.
3. TCP/22 prüfen.
4. Einen **echten SSH-Login mit dem vorgesehenen Schlüssel** testen.
5. Erst wenn Schritt 4 erfolgreich ist, das System als remote wartbar markieren.
6. Danach Display/Kiosk-Zustand prüfen (`systemctl`, `journalctl`, grafische Session, Anwendung/Kiosk-Prozess).

Nur `Ping OK` und `Port 22 offen` gelten ausdrücklich **nicht** als erfolgreicher SSH-Test.

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
- [ ] SSH-Benutzer vorhanden
- [ ] SSH-Benutzer **nicht gesperrt**
- [ ] OpenClaw Public Key in `authorized_keys`
- [ ] SSH-Dateirechte/Eigentümer korrekt
- [ ] `ssh.service` enabled
- [ ] Display auf 180° vorbereitet
- [ ] Touch auf 180° vorbereitet
- [ ] First-Boot-Dienst enabled
- [ ] persistenter Status funktioniert
- [ ] Neustart/Fortsetzung getestet
- [ ] keine Secrets im Git-Repository
- [ ] automatischer Phasenablauf startet ohne Nutzerbefehl

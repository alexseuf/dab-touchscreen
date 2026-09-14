# Verbindlicher Auftrag an OpenClaw beim Bespielen der SSD

OpenClaw soll die SSD nicht nur mit Dateien versehen, sondern vor dem Umstecken auf den Raspberry Pi vollständig für einen unbeaufsichtigten First-Boot vorbereiten.

## Muss vor dem Umstecken erledigt sein

1. Raspberry Pi OS für Raspberry Pi 4 bootfähig auf der SSD installieren bzw. vorbereiten.
2. Projekt nach `/opt/dab-touchscreen` installieren.
3. Abhängigkeiten installieren.
4. NetworkManager aktivieren und bekannte Haus-WLAN-Verbindung als Default lokal hinterlegen, sofern Zugangsdaten bereits bekannt sind.
5. Erforderliche Zugangsdaten lokal und geschützt ablegen; niemals in Git.
6. Deutsche Lokalisierung vollständig vorkonfigurieren, sodass beim ersten Boot keine Benutzereingabe erforderlich ist:
    - Zeitzone: `Europe/Berlin`;
    - Systemsprache/Locale: Deutsch (Deutschland), `de_DE.UTF-8`;
    - Tastaturlayout: Deutsch (`de`);
    - falls eine grafische Desktop-/Kiosk-Umgebung eigene Sprachparameter besitzt, ebenfalls Deutsch als Standard setzen;
    - NTP/automatische Zeitsynchronisation aktivieren.
7. Mosquitto und benötigte Basisdienste installieren.
8. `scripts/install_autonomous_firstboot.sh` ausführen.
9. `/usr/local/bin/dab-openclaw-stage` mit einem real funktionierenden Aufruf der lokal installierten OpenClaw-Instanz ersetzen.
10. `/usr/local/bin/dab-openclaw-report` mit dem bereits eingerichteten primären Kommunikationskanal verbinden.
11. Beide Wrapper lokal testen. Placeholder oder Dummy-Implementierungen sind vor dem Umstecken NICHT zulässig.
12. `dab-firstboot.service` aktivieren.
13. SSH vollständig vorbereiten und das vorgesehene Administrationskonto prüfen:
    - Benutzer existiert;
    - Benutzer ist **nicht gesperrt** (`passwd -S <user>` darf keinen Status `L` liefern);
    - Home-Verzeichnis und `~/.ssh` besitzen korrekte Eigentümer/Rechte;
    - der öffentliche OpenClaw-SSH-Key steht in `~/.ssh/authorized_keys`;
    - `sshd` ist aktiviert und startet beim Boot;
    - Passwort-Login darf deaktiviert bleiben, sobald Public-Key-Login funktionsfähig vorbereitet ist.
14. Falls das Konto nach dem Image-/Provisioning-Schritt gesperrt ist, muss OpenClaw es **vor dem ersten Boot** entsperren. Dabei kein leeres Passwort erzeugen. Entweder ein bereits lokal geschütztes Passwort/Hash setzen oder einen vorhandenen gültigen Hash verwenden und danach Public-Key-Login sicherstellen.
15. Den root-eigenen, eng begrenzten Wartungshelfer `/usr/local/sbin/dab-deploy` installieren und für den OpenClaw-Administrationsbenutzer über eine eigene Datei unter `/etc/sudoers.d/` **passwortlos ausschließlich für diesen Helper** freigeben. Allgemeines `NOPASSWD: ALL` ist ausdrücklich verboten.
16. Den Wartungshelfer noch während der SSD-Provisionierung nicht-interaktiv testen: `sudo -n /usr/local/sbin/dab-deploy check` muss als OpenClaw-Administrationsbenutzer erfolgreich sein. Ein später benötigtes, nicht gespeichertes Wartungspasswort gilt als Provisionierungsfehler.
17. Display- und Touch-Ausrichtung als Systemparameter vorbereiten. Für dieses Projekt ist die Sollausrichtung **180°**. Display und Touch müssen gemeinsam gedreht werden, damit Anzeige und Touch-Koordinaten übereinstimmen.
18. Testen, dass der First-Boot-Dienst nach einem simulierten Neustart automatisch startet.
19. Testen, dass ein Fortschrittsbericht erfolgreich beim Benutzer ankommt.
20. Testen, dass der persistente Phasenstatus nach Dienstneustart erhalten bleibt.
21. Erst danach die SSD als bereit zum Einbau melden.

## Verbindlicher autonomer Root-/Deploy-Zugriff

Der Zielzustand ist: OpenClaw kann spätere DAB-Änderungen ohne Benutzerpasswort durchführen, besitzt aber **kein allgemeines passwortloses Root-Recht**.

Dafür ist bereits beim Bespielen der SSD der mit dem Repository gelieferte Helper `scripts/dab-deploy` root-eigen nach `/usr/local/sbin/dab-deploy` zu installieren. Die Sudo-Regel darf nur genau diesen Helper erlauben. Der Helper selbst begrenzt die privilegierten Aktionen auf:

- Deployment des DAB-Projekts nach `/opt/dab-touchscreen`;
- Status und Neustart einer festen Allowlist von DAB-Diensten;
- einen nicht verändernden `check`-Preflight.

Die Datei `/usr/local/sbin/dab-deploy` muss `root:root` gehören und darf für den OpenClaw-Benutzer nicht beschreibbar sein. Auch die Datei unter `/etc/sudoers.d/` muss `root:root`, Modus `0440`, besitzen und mit `visudo -cf` validiert werden.

Pflichttest vor dem Aushängen der SSD:

```bash
sudo -u openclaw sudo -n /usr/local/sbin/dab-deploy check
```

Erwartet:

```text
PASS dab_deploy_root_helper
PASS dab_deploy_target_/opt/dab-touchscreen
PASS dab_deploy_service_allowlist
```

Falls der konkrete Administrationsbenutzer anders heißt, muss `OPENCLAW_ADMIN_USER` beim Installationsskript gesetzt und der Test mit diesem Benutzer ausgeführt werden.

**Wichtig:** Ein zufällig gesetztes Wartungspasswort darf nicht die einzige Möglichkeit für spätere Änderungen unter `/opt`, `systemctl restart` oder andere projektbezogene Wartung sein. OpenClaw soll dieses Passwort weder kennen noch speichern müssen. Der eingeschränkte Helper ist der vorgesehene autonome Wartungsweg.

Wenn später weitere DAB-Dienste benötigt werden, muss deren exakter Unit-Name bereits während einer privilegierten Provisionierungs-/Update-Phase in die Allowlist des Helpers aufgenommen werden. Wildcards für beliebige Systemdienste sind nicht zulässig.

## Verbindlicher Locale-/Zeit-Preflight

Vor dem Aushängen der SSD muss OpenClaw prüfen, dass die Lokalisierung bereits vollständig gesetzt ist. Der Benutzer darf beim ersten Start nicht nach Sprache, Tastatur oder Zeitzone gefragt werden.

```text
PASS timezone_Europe_Berlin
PASS locale_de_DE_UTF-8
PASS keyboard_layout_de
PASS ntp_enabled
```

Nach dem ersten Boot sind mindestens `timedatectl`, `localectl` und die effektive Locale zu prüfen. Abweichungen sollen OpenClaw automatisch korrigieren.

## Verbindlicher SSH-Preflight

Vor dem Aushängen der SSD muss OpenClaw mindestens folgende Prüfungen durchführen und protokollieren:

```text
PASS user_exists
PASS account_unlocked
PASS sshd_enabled
PASS authorized_keys_present
PASS ssh_permissions
PASS dab_deploy_noninteractive
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

`Boot -> Netzwerk -> Locale/Zeit prüfen -> SSH/Remotezugriff prüfen -> OpenClaw -> privilegierten DAB-Helper prüfen -> Projektstatus lesen -> nächste Phase umsetzen -> Phase testen -> Status speichern -> berichten -> nächste Phase`

Bei Neustart:

`Boot -> gespeicherten Status lesen -> an letzter offener Phase fortsetzen`

Der Hostname `dab-touchscreen.local` ist für die Administration zu bevorzugen. Eine per DHCP vergebene IPv4-Adresse darf zusätzlich erkannt und gemeldet werden, darf aber nicht hart als dauerhaft feste Adresse vorausgesetzt werden.

## Remote-Diagnose nach dem ersten Boot

Sobald Netzwerk verfügbar ist, führt OpenClaw zuerst einen Remote-Preflight aus:

1. Hostname per mDNS und aktuelle IPv4 ermitteln.
2. Ping bzw. Erreichbarkeit prüfen.
3. TCP/22 prüfen.
4. Einen **echten SSH-Login mit dem vorgesehenen Schlüssel** testen.
5. `sudo -n /usr/local/sbin/dab-deploy check` ausführen und sicherstellen, dass keine Passwortabfrage erscheint.
6. Zeitzone, Uhrzeit/NTP, deutsche Locale und deutsches Tastaturlayout verifizieren und bei Bedarf automatisch korrigieren.
7. Erst wenn SSH-Login und DAB-Helper-Test erfolgreich sind, das System als vollständig remote wartbar markieren.
8. Danach Display/Kiosk-Zustand prüfen (`systemctl`, `journalctl`, grafische Session, Anwendung/Kiosk-Prozess).

Nur `Ping OK` und `Port 22 offen` gelten ausdrücklich **nicht** als erfolgreicher SSH-Test. Ebenso gilt ein funktionierender SSH-Login allein nicht als ausreichende autonome Wartbarkeit, wenn projektbezogene Root-Schritte später wieder an einer Passwortabfrage hängen bleiben.

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

Ein fehlender `sudo`-Zugang für reguläre DAB-Projektpflege darf **nach abgeschlossener SSD-Provisionierung nicht mehr als normaler Blocker auftreten**. Dieser Fall muss vorher durch Installation und Test des eingeschränkten `dab-deploy`-Helpers verhindert werden.

In einem echten Blocker vorherige stabile Phase erhalten und präzise melden, was benötigt wird.

## Abnahme der SSD-Vorbereitung

Die Vorbereitung ist erst abgeschlossen, wenn alle folgenden Punkte mit PASS bestätigt sind:

- [ ] SSD bootfähig für Raspberry Pi 4
- [ ] Projekt vorhanden
- [ ] OpenClaw lokal funktionsfähig
- [ ] OpenClaw Stage-Hook real verdrahtet
- [ ] Kommunikations-Hook real verdrahtet
- [ ] Fortschritts-Testmeldung erfolgreich
- [ ] Haus-WLAN vorbereitet, sofern Zugangsdaten verfügbar
- [ ] Zeitzone `Europe/Berlin`
- [ ] Systemsprache/Locale `de_DE.UTF-8`
- [ ] deutsches Tastaturlayout
- [ ] automatische Zeitsynchronisation/NTP aktiv
- [ ] SSH-Benutzer vorhanden
- [ ] SSH-Benutzer **nicht gesperrt**
- [ ] OpenClaw Public Key in `authorized_keys`
- [ ] SSH-Dateirechte/Eigentümer korrekt
- [ ] `ssh.service` enabled
- [ ] `/usr/local/sbin/dab-deploy` root-eigen installiert
- [ ] sudoers-Regel ausschließlich für `dab-deploy`, kein `NOPASSWD: ALL`
- [ ] `visudo -cf` für die DAB-sudoers-Datei erfolgreich
- [ ] `sudo -n /usr/local/sbin/dab-deploy check` als OpenClaw-Benutzer erfolgreich
- [ ] DAB-Dienst-Allowlist für GUI/Topics/Simulator vollständig
- [ ] Display auf 180° vorbereitet
- [ ] Touch auf 180° vorbereitet
- [ ] First-Boot-Dienst enabled
- [ ] persistenter Status funktioniert
- [ ] Neustart/Fortsetzung getestet
- [ ] keine Secrets im Git-Repository
- [ ] automatischer Phasenablauf startet ohne Nutzerbefehl

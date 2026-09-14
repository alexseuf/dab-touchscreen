# Verbindlicher Auftrag an OpenClaw beim Bespielen der SSD

OpenClaw soll die SSD nicht nur mit Dateien versehen, sondern vor dem Umstecken auf den Raspberry Pi vollständig für einen unbeaufsichtigten First-Boot vorbereiten.

## Muss vor dem Umstecken erledigt sein

1. Raspberry Pi OS für Raspberry Pi 4 bootfähig auf der SSD installieren bzw. vorbereiten.
2. Projekt nach `/opt/dab-touchscreen` installieren.
3. Abhängigkeiten installieren.
4. NetworkManager aktivieren und bekannte Haus-WLAN-Verbindung als Default lokal hinterlegen, sofern Zugangsdaten bereits bekannt sind.
5. Erforderliche Zugangsdaten lokal und geschützt ablegen; niemals in Git.
6. Deutsche Lokalisierung vollständig vorkonfigurieren, sodass beim ersten Boot keine Benutzereingabe erforderlich ist: Zeitzone `Europe/Berlin`, Locale `de_DE.UTF-8`, Tastatur `de`, NTP aktiv.
7. Mosquitto und benötigte Basisdienste installieren.
8. `scripts/install_autonomous_firstboot.sh` ausführen.
9. `/usr/local/bin/dab-openclaw-stage` und `/usr/local/bin/dab-openclaw-report` real verdrahten und testen; Placeholder sind unzulässig.
10. `dab-firstboot.service` aktivieren.
11. SSH-Benutzer, Entsperrung, Public Key, Dateirechte und `sshd` vollständig prüfen.
12. Den root-eigenen, eng begrenzten Wartungshelfer `/usr/local/sbin/dab-deploy` installieren und für den OpenClaw-Administrationsbenutzer über `/etc/sudoers.d/` passwortlos ausschließlich für diesen Helper freigeben. Allgemeines `NOPASSWD: ALL` ist verboten.
13. `sudo -n /usr/local/sbin/dab-deploy check` als OpenClaw-Administrationsbenutzer muss erfolgreich sein.
14. **Zusätzlich einen echten Deploy-/Update-Durchlauf einschließlich aller Benutzerwechsel und Post-Deploy-Prüfungen ausführen.** Ein bloßer `check` des Helpers reicht nicht.
15. Display und Touch gemeinsam auf 180° vorbereiten.
16. First-Boot, Fortschrittsbericht, persistente Phasen und Neustart/Fortsetzung testen.
17. Erst danach die SSD als bereit melden.

## Verbindlicher autonomer Root-/Deploy-Zugriff

Der Zielzustand ist: OpenClaw kann spätere DAB-Änderungen ohne Benutzerpasswort durchführen, besitzt aber kein allgemeines passwortloses Root-Recht. `/usr/local/sbin/dab-deploy` muss `root:root` gehören, nicht durch den OpenClaw-Benutzer beschreibbar sein; die sudoers-Datei muss `root:root`, Modus `0440`, sein und mit `visudo -cf` validiert werden.

Pflichttest:

```bash
sudo -u openclaw sudo -n /usr/local/sbin/dab-deploy check
```

Erwartet:

```text
PASS dab_deploy_root_helper
PASS dab_deploy_target_/opt/dab-touchscreen
PASS dab_deploy_service_allowlist
```

### Verbindlicher Laufzeit-/Berechtigungs-Preflight

Der `check`-Befehl allein ist ausdrücklich **nicht ausreichend**. Beim ersten autonomen Lauf trat ein zweiter Fehler auf: Der Helper installierte Dateien als root korrekt, wechselte für die anschließende Python-/Projektprüfung jedoch zum Laufzeitbenutzer `dab`. Dabei waren Python-Cache-Verzeichnisse bzw. beim Root-Schritt erzeugte Laufzeit-Artefakte root-eigen. Die Prüfung brach mit `PermissionError` ab, bevor die vorgesehenen Dienst-Neustarts erreicht wurden. Dadurch war erneut ein manueller privilegierter Austausch des root-eigenen Helpers erforderlich.

Dieser Fehler muss künftig bereits während Provisionierung und Helper-Updates verhindert werden:

1. Der Helper darf keine root-eigenen Cache-, Bytecode-, Build-, State- oder temporären Dateien in Verzeichnissen hinterlassen, die anschließend vom Benutzer `dab` gelesen, geschrieben oder gelöscht werden müssen.
2. Python-Prüfungen unter `dab` sollen nach Möglichkeit ohne beschreibbaren Bytecode-Cache laufen (`PYTHONDONTWRITEBYTECODE=1`) oder einen explizit für `dab` beschreibbaren Cache/Temp-Pfad verwenden.
3. Vor jedem Wechsel von root zu `dab` müssen Eigentümer und Rechte aller für den Test benötigten Projekt-, Cache-, State- und Temp-Pfade geprüft bzw. korrigiert werden. Es darf kein pauschales rekursives `chmod 777` verwendet werden.
4. Der Provisionierungs-Test muss einen **echten vollständigen Helper-Durchlauf** mit denselben Benutzerwechseln wie im späteren Betrieb ausführen: Dateien installieren/aktualisieren -> als `dab` Python-/Projektprüfung ausführen -> Dienststatus prüfen -> die erlaubten DAB-Dienste neu starten -> Status danach erneut prüfen.
5. Der Test muss mit einem bereits vorhandenen root-eigenen Python-Cache bzw. einem künstlich erzeugten entsprechenden Konflikt wiederholt werden. Der Helper muss diesen Zustand sicher behandeln, ohne `PermissionError` und ohne manuellen Eingriff.
6. Erst wenn der vollständige Durchlauf inklusive Dienst-Neustarts erfolgreich ist, gilt `dab-deploy` als autonom betriebsbereit.
7. Wird der root-eigene Helper selbst aktualisiert, muss das Update atomar erfolgen und danach sofort derselbe vollständige Laufzeit-Preflight ausgeführt werden. Ein Update, das nur als Datei vorbereitet wird, aber wegen fehlender Rechte nicht nach `/usr/local/sbin/dab-deploy` gelangt, darf nicht als abgeschlossen gemeldet werden.

Zusätzliche erwartete PASS-Marker:

```text
PASS dab_deploy_runtime_user_dab
PASS dab_deploy_python_cache_permissions
PASS dab_deploy_project_validation_as_dab
PASS dab_deploy_service_restart
PASS dab_deploy_post_restart_status
PASS dab_deploy_full_autonomous_cycle
```

Ein zufällig gesetztes oder später nicht verfügbares Wartungspasswort darf nicht die einzige Möglichkeit für Änderungen unter `/opt`, Helper-Updates oder `systemctl restart` sein. Wenn weitere DAB-Dienste benötigt werden, müssen deren exakte Unit-Namen privilegiert in die feste Allowlist aufgenommen werden; keine Wildcards.

## Verbindlicher Locale-/Zeit-Preflight

Vor dem Aushängen müssen mindestens folgende Prüfungen PASS sein:

```text
PASS timezone_Europe_Berlin
PASS locale_de_DE_UTF-8
PASS keyboard_layout_de
PASS ntp_enabled
```

## Verbindlicher SSH-/Autonomie-Preflight

```text
PASS user_exists
PASS account_unlocked
PASS sshd_enabled
PASS authorized_keys_present
PASS ssh_permissions
PASS dab_deploy_noninteractive
PASS dab_deploy_full_autonomous_cycle
PASS display_rotation_180_configured
PASS touch_rotation_180_configured
```

Ein vorhandener Benutzer allein reicht nicht. Ein gesperrtes Konto oder ein Helper, der zwar `check` besteht, aber beim realen Benutzerwechsel/Deploy scheitert, führt zur Abnahme `FAIL`.

## Verhalten nach Einbau

Ohne manuellen Startbefehl:

`Boot -> Netzwerk -> Locale/Zeit -> SSH -> dab-deploy check -> vollständigen Deploy-Laufzeitpfad verifizieren -> Projektstatus -> nächste Phase -> testen -> Status speichern -> berichten -> nächste Phase`

Bei Neustart wird am letzten offenen Phasenstatus fortgesetzt. `dab-touchscreen.local` ist für Administration zu bevorzugen; DHCP-IP darf erkannt/gemeldet, aber nicht hart vorausgesetzt werden.

## Remote-Diagnose nach dem ersten Boot

OpenClaw prüft mDNS/IP, TCP/22, echten SSH-Key-Login, `sudo -n /usr/local/sbin/dab-deploy check` und den vollständigen DAB-Laufzeitpfad. Erst wenn SSH, Helper-Check **und ein realer Deploy-/Validierungs-/Restart-Zyklus** funktionieren, darf das System als vollständig remote wartbar gelten. Danach Display/Kiosk und DAB-Dienste prüfen.

## Fortschrittskommunikation und Entscheidungsregel

OpenClaw berichtet bei Boot/Start, Start/Abschluss jeder Phase, mindestens alle 30 Minuten bei längeren Arbeiten, bei Tests, Reparatur/Rollback, Blockern und Abschluss. Normale technische Entscheidungen selbst treffen. Ein fehlender sudo-Zugang oder ein `PermissionError` durch root-eigene Laufzeit-/Python-Cache-Dateien darf nach abgeschlossener Provisionierung nicht mehr als normaler Blocker auftreten.

## Abnahme der SSD-Vorbereitung

Die SSD ist erst fertig, wenn u. a. folgende Punkte PASS sind:

- bootfähig; Projekt und OpenClaw vorhanden;
- Stage-/Kommunikations-Hooks real getestet;
- WLAN, deutsche Locale/Zeitzone/Tastatur und NTP vorbereitet;
- SSH-Konto entsperrt, Public Key und Rechte korrekt, SSH enabled;
- `/usr/local/sbin/dab-deploy` root-eigen installiert;
- sudoers nur für `dab-deploy`, `visudo -cf` erfolgreich, kein `NOPASSWD: ALL`;
- `sudo -n /usr/local/sbin/dab-deploy check` erfolgreich;
- **vollständiger autonomer Deploy-Zyklus einschließlich Prüfung als `dab` und Dienst-Neustarts erfolgreich**;
- **Test mit root-eigenem Python-Cache-/Runtime-Artefakt ohne `PermissionError` bestanden**;
- DAB-Dienst-Allowlist für GUI/Topics/Simulator vollständig;
- Display/Touch 180°, First-Boot, persistenter Status und Neustart/Fortsetzung getestet;
- keine Secrets im Git;
- automatischer Phasenablauf startet ohne Nutzerbefehl.

## Autonome Verwaltung angeschlossener Datenträger auf dem OpenClaw-Host

Der **OpenClaw-Management-Raspberry selbst** soll zusätzlich angeschlossene SSDs, USB-Sticks und andere Blockgeräte ohne Passwort- oder Freigaberückfrage vorbereiten können. Diese Funktion gehört auf den OpenClaw-Host, nicht in die Root-Rechte des DAB-Zielsystems.

Dafür ist `scripts/openclaw-storage` als root-eigener Helper nach `/usr/local/sbin/openclaw-storage` zu installieren. Die Installation erfolgt mit:

```bash
sudo OPENCLAW_ADMIN_USER=openclaw ./scripts/install_openclaw_storage_helper.sh
```

Die sudoers-Regel darf ausschließlich diesen Helper freigeben; allgemeines `NOPASSWD: ALL` bleibt verboten. Der Helper muss die physischen Datenträger hinter `/`, `/boot` und `/boot/firmware` automatisch erkennen und **jede verändernde oder destruktive Operation auf diesen System-/Boot-Datenträgern verweigern**. Wenn der Systemdatenträger nicht eindeutig ermittelt werden kann, muss die Operation fehlschlagen statt zu raten.

Der Helper unterstützt insbesondere Erkennen/Info, Mount/Unmount, Löschen von Dateisystemsignaturen, GPT-Neuanlage, Formatierung, Schreiben kompletter Images sowie kontrollierte Dateioperationen innerhalb verwalteter Mounts. Details und Betriebsregeln stehen in `docs/OPENCLAW_STORAGE_AUTONOMY.md`.

Verbindlicher Preflight auf dem OpenClaw-Host:

```text
PASS openclaw_storage_root_helper
PASS protected_system_disk=<device>
PASS openclaw_storage_mount_root=/mnt/openclaw-storage
PASS openclaw_storage_noninteractive
```

Mit einem entbehrlichen externen Testdatenträger muss mindestens einmal vollständig geprüft werden:

`list -> info -> wipe -> partition-gpt -> format -> mount -> copy-in -> remove -> unmount`

Erst danach darf OpenClaw die Datenträgerverwaltung als autonom betriebsbereit betrachten. Bei mehreren externen Datenträgern muss OpenClaw das Ziel anhand von Modell, Seriennummer, Größe und Transportart eindeutig bestimmen; bei Mehrdeutigkeit darf nicht geraten werden.

# Recovery: Raspberry erreichbar, SSH-Key abgewiesen, Bildschirm schwarz

## Symptom

Typischer Fehlerfall nach dem ersten Boot:

- Raspberry ist per Netzwerk erreichbar;
- `dab-touchscreen.local` und/oder die DHCP-IP antworten;
- TCP-Port 22 ist offen;
- SSH mit dem vorgesehenen Schlüssel wird trotzdem abgewiesen;
- Bildschirm bleibt schwarz;
- Remote-Diagnose des Kiosk-/Display-Dienstes ist deshalb nicht möglich.

Dieser Zustand deutet insbesondere dann auf ein **gesperrtes Benutzerkonto** hin, wenn der Benutzer beim Provisionieren zwar angelegt wurde, sein Shadow-Eintrag aber noch als locked markiert ist. Ein offener SSH-Port beweist nur, dass `sshd` läuft – nicht, dass der vorgesehene Account sich anmelden kann.

## Ziel

Die SSD wird am OpenClaw-Rechner offline repariert. Danach soll der Raspberry ohne weitere lokale Eingriffe booten und über SSH administrierbar sein.

## Sicherheitsregeln

- Keine Passwörter, privaten Schlüssel oder WLAN-Secrets in Git schreiben.
- Kein leeres Passwort erzeugen.
- Vor Änderungen `/etc/passwd`, `/etc/shadow`, `/etc/ssh/sshd_config*` und relevante Display-/Kiosk-Konfiguration sichern.
- Root-Dateisystem sauber mounten und am Ende synchronisieren/aushängen.
- Die tatsächliche Root-Partition dynamisch ermitteln; Gerätenamen wie `/dev/sda2` nicht blind voraussetzen.

## Offline-Recovery – Ablauf

### 1. SSD erkennen und Root-Dateisystem mounten

Beispiel:

```bash
lsblk -f
sudo mkdir -p /mnt/dab-root
sudo mount /dev/<ROOT_PARTITION> /mnt/dab-root
```

Falls `/boot` oder `/boot/firmware` eine separate Partition ist, diese zusätzlich an der passenden Stelle unterhalb von `/mnt/dab-root` mounten.

### 2. Benutzer ermitteln

```bash
awk -F: '$3 >= 1000 && $1 != "nobody" {print $1, $3, $6}' /mnt/dab-root/etc/passwd
```

Danach den vorgesehenen Administrationsbenutzer als `<user>` verwenden.

### 3. Sperrstatus prüfen

```bash
sudo chroot /mnt/dab-root passwd -S <user>
```

Relevant ist das Statusfeld:

- `L` = locked → Fehler beheben;
- `P` = Passwort gesetzt / Account nicht gesperrt;
- andere Zustände einzeln prüfen.

Alternativ Shadow-Eintrag kontrollieren:

```bash
sudo getent -s files shadow <user> --root /mnt/dab-root 2>/dev/null || \
sudo awk -F: -v u="<user>" '$1==u {print $1 ":" $2}' /mnt/dab-root/etc/shadow
```

Ein Passwortfeld, das mit `!` beginnt, kennzeichnet üblicherweise eine Sperre.

### 4. Konto sicher entsperren

Bevorzugt wird ein gültiger, lokal geschützter Passwort-Hash gesetzt, falls OpenClaw die beim Provisionieren vorgesehenen Zugangsdaten bereits sicher kennt. Der Hash darf nicht in Git landen.

Beispiel mit bereits erzeugtem Hash in einer lokalen Shell-Variable:

```bash
sudo chroot /mnt/dab-root usermod -p "$PASSWORD_HASH" <user>
```

Danach prüfen:

```bash
sudo chroot /mnt/dab-root passwd -S <user>
```

Der Status darf nicht mehr `L` sein.

Falls bereits ein gültiger Hash vorhanden ist, der nur mit einem führenden `!` gesperrt wurde, kann die Sperre mit den üblichen Account-Werkzeugen entfernt werden. Dabei anschließend unbedingt kontrollieren, dass kein leeres Passwort entstanden ist.

### 5. SSH-Key und Rechte prüfen

```bash
sudo install -d -m 700 -o <user> -g <user> /mnt/dab-root/home/<user>/.ssh
sudo test -s /mnt/dab-root/home/<user>/.ssh/authorized_keys
sudo chown <user>:<user> /mnt/dab-root/home/<user>/.ssh/authorized_keys
sudo chmod 600 /mnt/dab-root/home/<user>/.ssh/authorized_keys
```

Zusätzlich prüfen, dass der richtige öffentliche Schlüssel enthalten ist.

### 6. SSH-Dienst und Konfiguration prüfen

```bash
sudo chroot /mnt/dab-root systemctl enable ssh
sudo chroot /mnt/dab-root sshd -t
```

`sshd -t` muss ohne Fehler zurückkehren.

Public-Key-Login muss zulässig sein. Passwort-Login kann deaktiviert bleiben, wenn der Schlüssel korrekt eingerichtet und das Konto nicht gesperrt ist.

### 7. Display und Touch auf 180° drehen

Die Implementierung hängt vom tatsächlich verwendeten Grafik-Stack ab. OpenClaw soll daher zuerst erkennen, ob das System Wayland/labwc, X11, KMS/DRM oder eine anwendungsspezifische Rotation verwendet.

Verbindliche Sollbedingung:

```text
Display rotation = 180°
Touch rotation   = 180°
```

Anzeige und Touch müssen gemeinsam gedreht werden. Nur das Bild zu drehen ist nicht ausreichend.

Nach der Konfigurationsänderung soll OpenClaw die betroffenen Dateien und den erkannten Stack im Recovery-Protokoll nennen.

### 8. Kiosk-/Display-Autostart offline prüfen

Mindestens kontrollieren:

- `dab-firstboot.service` enabled;
- eigentlicher Anwendungs-/Kiosk-Dienst enabled;
- keine ungültigen Pfade oder Benutzer in den Unit-Dateien;
- grafisches Target vorhanden;
- Startbefehl verweist auf existierende Anwendung;
- keine offensichtlichen Fehler in persistenten Logs.

Beispiel:

```bash
sudo chroot /mnt/dab-root systemctl is-enabled dab-firstboot.service
sudo find /mnt/dab-root/etc/systemd/system -maxdepth 2 -type f -name '*dab*' -o -name '*kiosk*'
```

Falls persistentes Journal vorhanden ist, kann es offline unter `/mnt/dab-root/var/log/journal` ausgewertet werden.

### 9. Recovery-Preflight vor dem Aushängen

Die SSD darf erst wieder in den Raspberry eingesetzt werden, wenn mindestens diese Punkte PASS sind:

```text
PASS root_filesystem_cleanly_mounted
PASS user_exists
PASS account_unlocked
PASS authorized_keys_present
PASS ssh_permissions
PASS sshd_config_valid
PASS sshd_enabled
PASS display_rotation_180_configured
PASS touch_rotation_180_configured
PASS kiosk_or_display_service_configured
PASS dab_firstboot_enabled
```

### 10. SSD sauber aushängen

```bash
sync
sudo umount -R /mnt/dab-root
```

Erst danach SSD physisch abziehen.

## Verifikation nach erneutem Boot

OpenClaw soll nach dem Wiedereinbau automatisch in dieser Reihenfolge prüfen:

1. `dab-touchscreen.local` per mDNS auflösen;
2. aktuelle IPv4 bestimmen;
3. TCP/22 erreichbar;
4. **echter SSH-Key-Login erfolgreich**;
5. `systemctl --failed` prüfen;
6. Status von First-Boot-, Display-/Kiosk- und Anwendungsdienst prüfen;
7. relevante Journale auswerten;
8. Bildschirm-/Touch-Funktion prüfen bzw. Benutzer nur dann um kurze Sichtkontrolle bitten, wenn sie nicht technisch messbar ist.

Ein erfolgreicher Ping oder ein offener Port 22 allein darf nicht mehr als erfolgreiche Remote-Inbetriebnahme gewertet werden.

## Prävention für künftige Images

Dieser Fehler soll bereits beim SSD-Provisioning verhindert werden. Vor Freigabe der SSD sind deshalb zwingend zu prüfen:

- Benutzer vorhanden;
- Benutzer nicht locked;
- SSH-Key vorhanden und Dateirechte korrekt;
- `sshd -t` erfolgreich;
- SSH-Dienst enabled;
- Display und Touch gemeinsam auf 180° vorbereitet;
- First-Boot-/Kiosk-Dienste enabled.

Damit wird aus dem bisherigen Fehlerfall ein reproduzierbarer Preflight-Test statt eines manuellen Recovery-Schritts.

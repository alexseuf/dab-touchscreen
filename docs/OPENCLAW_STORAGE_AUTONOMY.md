# Autonome Datenträgerverwaltung durch OpenClaw

Ziel: Der OpenClaw-Management-Raspberry darf zusätzlich angeschlossene SSDs, USB-Sticks und andere Blockgeräte ohne Benutzereingabe erkennen, mounten, löschen, partitionieren, formatieren, mit Images beschreiben und Dateien darauf verändern. Der System-/Boot-Datenträger des OpenClaw-Raspberry muss dabei technisch gesperrt bleiben.

## Sicherheitsmodell

Es wird **kein** allgemeines `NOPASSWD: ALL` vergeben. Stattdessen wird der root-eigene Helper

```text
/usr/local/sbin/openclaw-storage
```

installiert. Nur dieser Helper ist über sudo ohne Passwort aufrufbar. Der Helper erkennt die physischen Datenträger hinter `/`, `/boot` und `/boot/firmware` und verweigert auf diesen Geräten sämtliche Speicheroperationen.

Die sudoers-Regel lautet sinngemäß:

```text
openclaw ALL=(root) NOPASSWD: /usr/local/sbin/openclaw-storage *
```

Die Sicherheit hängt deshalb von zwei Punkten ab:

1. `/usr/local/sbin/openclaw-storage` gehört `root:root` und ist für `openclaw` nicht beschreibbar.
2. Der Helper validiert Geräte, Pfade und Kommandos selbst und stellt keinen beliebigen Root-Shell-Aufruf bereit.

## Installation auf dem OpenClaw-Management-Pi

Aus einem Checkout dieses Repositories:

```bash
sudo OPENCLAW_ADMIN_USER=openclaw ./scripts/install_openclaw_storage_helper.sh
```

Der Installer:

- installiert den Helper root-eigen;
- legt `/mnt/openclaw-storage` an;
- erzeugt und validiert `/etc/sudoers.d/openclaw-storage`;
- installiert bei Debian/Raspberry Pi OS bei Bedarf `parted`, `gdisk`, `dosfstools` und `exfatprogs`;
- prüft anschließend `sudo -n /usr/local/sbin/openclaw-storage check` und `list` als OpenClaw-Benutzer.

## Unterstützte Befehle

```bash
sudo -n /usr/local/sbin/openclaw-storage check
sudo -n /usr/local/sbin/openclaw-storage list
sudo -n /usr/local/sbin/openclaw-storage info /dev/sda
sudo -n /usr/local/sbin/openclaw-storage mount /dev/sda1
sudo -n /usr/local/sbin/openclaw-storage unmount /dev/sda1
sudo -n /usr/local/sbin/openclaw-storage wipe /dev/sda
sudo -n /usr/local/sbin/openclaw-storage partition-gpt /dev/sda
sudo -n /usr/local/sbin/openclaw-storage format /dev/sda1 ext4
sudo -n /usr/local/sbin/openclaw-storage image /path/image.img /dev/sda
sudo -n /usr/local/sbin/openclaw-storage copy-in /tmp/file /dev/sda1 etc/example.conf
sudo -n /usr/local/sbin/openclaw-storage mkdir /dev/sda1 opt/mydir
sudo -n /usr/local/sbin/openclaw-storage remove /dev/sda1 var/tmp/oldfile
```

Mounts des Helpers liegen ausschließlich unter:

```text
/mnt/openclaw-storage/<device>
```

`copy-in`, `mkdir` und `remove` akzeptieren nur relative Pfade innerhalb dieses verwalteten Mounts. `..`, absolute Ziele und Pfad-Ausbrüche werden abgewiesen.

## Schutz des Systemdatenträgers

Vor jeder potentiell verändernden Operation wird der physische Datenträger des Zielgeräts mit den physischen Vorfahren der Geräte verglichen, die `/`, `/boot` und `/boot/firmware` tragen.

Ist der Systemdatenträger nicht sicher ermittelbar, gilt **fail closed**: destruktive Operationen werden verweigert.

Damit darf OpenClaw z. B. eine neu angeschlossene USB-SSD `/dev/sda` autonom vorbereiten, jedoch nicht die eigene Root-/Boot-Platte löschen oder überschreiben.

## OpenClaw-Ausführungsfreigabe

Zusätzlich zur Linux-sudo-Regel muss die OpenClaw-Ausführungsrichtlinie so gesetzt sein, dass lokale Befehle auf dem Gateway nicht jedes Mal bestätigt werden müssen. Die konkrete OpenClaw-Konfiguration ist versionsabhängig und muss gegen die installierte Version geprüft werden. Zielzustand ist sinngemäß:

```text
host = gateway
security = full
ask = off
```

Vor Anwendung ist die aktuelle CLI-Hilfe bzw. Dokumentation der installierten OpenClaw-Version maßgeblich. Die Linux-seitige Datenträger-Sicherheit bleibt unabhängig davon durch `openclaw-storage` bestehen.

## Verbindlicher Preflight

Nach Installation müssen mindestens folgende Punkte PASS sein:

```text
PASS openclaw_storage_root_helper
PASS protected_system_disk=<device>
PASS openclaw_storage_mount_root=/mnt/openclaw-storage
PASS openclaw_storage_noninteractive
```

Zusätzlich muss mit einem **nicht-systemrelevanten Testdatenträger** einmal der komplette Ablauf geprüft werden:

```text
list -> info -> wipe -> partition-gpt -> format -> mount -> copy-in -> remove -> unmount
```

Danach ist ein Image-Schreibtest auf einem entbehrlichen Testdatenträger sinnvoll. Der System-/Boot-Datenträger darf für solche Tests niemals verwendet werden.

## Betriebsregel für OpenClaw

Wenn mehrere zusätzliche Datenträger angeschlossen sind und der Benutzer keinen eindeutig identifiziert hat, soll OpenClaw vor einer destruktiven Aktion anhand von Modell, Seriennummer, Größe und Transportart das Ziel eindeutig bestimmen. Ist die Auswahl trotz dieser Daten mehrdeutig, darf OpenClaw nicht raten.

Ist dagegen genau ein klar zusätzlich angeschlossener Datenträger vorhanden und der Auftrag eindeutig (z. B. „bespiele die angeschlossene SSD“), darf OpenClaw den gesamten Vorgang ohne weitere Benutzerbestätigung durchführen.

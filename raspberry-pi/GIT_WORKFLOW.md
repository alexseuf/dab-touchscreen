# Git-/GitHub-Workflow ohne OpenClaw

Dieses Dokument setzt voraus, dass `origin` auf das bestätigte zentrale
GitHub-Repository zeigt. Die Beispiele verwenden den Branch `main`.

## Änderungen direkt auf GitHub durchführen

1. Datei auf GitHub öffnen und **Edit** wählen.
2. Änderung auf einem neuen Branch speichern.
3. Pull Request anlegen und prüfen.
4. Pull Request nach `main` mergen.
5. Auf dem Raspberry anschließend den Stand holen und installieren:

```bash
cd ~/dab-touchscreen
git pull --ff-only origin main
sudo ./raspberry-pi/update.sh
```

`--ff-only` verhindert einen unbeabsichtigten lokalen Merge-Commit.
`update.sh` installiert den aktuellen Anwendungsstand, überspringt aber bewusst
`apt-get`. Wenn eine Firmware-Version neue oder geänderte Systempakete benötigt,
muss nach dem Pull stattdessen `sudo ./raspberry-pi/install.sh` ausgeführt werden.

## Lokale Änderungen committen und pushen

```bash
cd ~/dab-touchscreen
git status
git pull --rebase origin main
# Dateien bearbeiten und testen
python3 -m unittest discover -s raspberry-pi/tests -v
git add <dateien>
git commit -m "Kurze Beschreibung"
git push origin main
```

Secrets niemals mit `git add -f` erzwingen. Vor jedem Push `git status` und
`git diff --cached` prüfen.

## Frischen Raspberry vollständig wiederherstellen

Auf Raspberry Pi OS Bookworm Desktop 64-bit:

```bash
cd ~
git clone https://github.com/alexseuf/dab-touchscreen.git dab-touchscreen
cd dab-touchscreen/raspberry-pi
cp secrets.env.example secrets.env   # nur falls MQTT-Secrets benötigt werden
nano secrets.env                     # echte Werte ausschließlich lokal eintragen
sudo ./install.sh
```

Ohne `secrets.env` wird ein sicherer lokaler MQTT-Broker installiert. WLAN wird
anschließend über die HMI bzw. NetworkManager eingerichtet.

## Lokale und gleichzeitige GitHub-Änderungen

Zuerst lokale Arbeit sichern:

```bash
git status
git add <dateien>
git commit -m "Lokale Zwischenarbeit"
git pull --rebase origin main
```

Bei Konflikten:

```bash
git status
# Konfliktmarkierungen in den genannten Dateien bearbeiten
git add <bereinigte-dateien>
git rebase --continue
```

Falls die Auflösung noch nicht fortgesetzt werden soll:

```bash
git rebase --abort
```

Es sind weder `git reset --hard` noch Force-Push erforderlich. Nach erfolgreichem
Rebase testen und normal mit `git push origin main` übertragen.

## Bekannten funktionierenden Commit wiederherstellen

Commit zunächst ohne Veränderung von `main` prüfen:

```bash
git fetch origin
git switch --detach <COMMIT-SHA>
sudo ./install.sh --no-apt
```

Zurück zum aktuellen Hauptzweig:

```bash
git switch main
git pull --ff-only origin main
sudo ./raspberry-pi/update.sh
```

Soll ein alter Stand dauerhaft weiterentwickelt werden, dafür einen neuen Branch
erstellen, nicht die bestehende Historie überschreiben:

```bash
git switch -c recovery/<name> <COMMIT-SHA>
```

## Absichtlich nicht in Git gespeicherte Daten

- `secrets.env`, `.env` und lokale Varianten
- WLAN-/NetworkManager-Verbindungsprofile (`*.nmconnection`)
- MQTT-Passwörter und andere Credential-Dateien
- SSH-Schlüssel, `authorized_keys`, Schlüssel-/Zertifikatcontainer
- Tokens und API-Schlüssel
- SQLite-Laufzeitdaten, Logs, Python-Caches und virtuelle Umgebungen
- produktive Historie unter `/var/lib/dab-touchscreen`
- installierte Laufzeitvariablen unter `/etc/dab-touchscreen/env`

Ungefährliche Vorlagen dürfen die Endung `.example` tragen. Echte Werte gehören
nur in lokale, ignorierte Dateien und in die vom Installer geschützten Pfade.

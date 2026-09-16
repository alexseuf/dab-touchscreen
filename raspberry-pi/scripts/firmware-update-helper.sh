#!/usr/bin/env bash
set -Eeuo pipefail

INSTALL_DIR=/opt/dab-touchscreen
STATE_DIR=/var/lib/dab-touchscreen
STATUS_FILE="$STATE_DIR/firmware-update-status.json"
BACKUP_ROOT="$STATE_DIR/firmware-backups"
STAGE_ROOT="$STATE_DIR/firmware-staging"
SERVICE_USER=dab
ALLOWED_REPOSITORY=alexseuf/dab-touchscreen

repo=${1:-}
sha=${2:-}
label=${3:-unknown}

[[ $EUID -eq 0 ]] || { echo "root required" >&2; exit 1; }
[[ $repo == "$ALLOWED_REPOSITORY" ]] || { echo "Repository not allowed for privileged install" >&2; exit 2; }
[[ $sha =~ ^[0-9a-fA-F]{40}$ ]] || { echo "Invalid commit SHA" >&2; exit 2; }

install -d -o "$SERVICE_USER" -g "$SERVICE_USER" -m 0750 "$STATE_DIR" "$BACKUP_ROOT" "$STAGE_ROOT"
exec 9>"$STATE_DIR/firmware-update.lock"
flock -n 9 || { echo "Update already running" >&2; exit 3; }

status() {
    local state=$1 message=$2
    python3 - "$STATUS_FILE" "$state" "$message" "$sha" "$label" <<'PY'
import json, os, sys, tempfile, time
path, state, message, sha, label = sys.argv[1:]
data={"state":state,"message":message,"sha":sha,"label":label,"time":int(time.time())}
fd,tmp=tempfile.mkstemp(prefix=".fw-status-",dir=os.path.dirname(path),text=True)
with os.fdopen(fd,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False)
os.chmod(tmp,0o640); os.replace(tmp,path)
PY
    chown "$SERVICE_USER:$SERVICE_USER" "$STATUS_FILE"
}

stamp=$(date +%Y%m%d-%H%M%S)
stage="$STAGE_ROOT/$sha"
backup="$BACKUP_ROOT/$stamp-$sha"
archive="$STAGE_ROOT/$sha.tar.gz"
old_commit=""
[[ -r "$STATE_DIR/firmware-state.json" ]] && old_commit=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("sha",""))' "$STATE_DIR/firmware-state.json" 2>/dev/null || true)

rollback() {
    rc=$?
    trap - ERR
    status rollback "Fehler erkannt – vorherige Installation wird wiederhergestellt"
    if [[ -d $backup ]]; then
        rsync -a --delete "$backup/" "$INSTALL_DIR/"
        chown -R root:root "$INSTALL_DIR"
        systemctl restart lightdm.service || true
        status failed "Update fehlgeschlagen; Rollback durchgeführt"
    else
        status failed "Update fehlgeschlagen; kein Backup verfügbar"
    fi
    exit "$rc"
}
trap rollback ERR

rm -rf "$stage" "$archive"
status download "Commit wird heruntergeladen"
python3 - "$repo" "$sha" "$archive" <<'PY'
import sys, urllib.request
repo,sha,out=sys.argv[1:]
url=f"https://codeload.github.com/{repo}/tar.gz/{sha}"
req=urllib.request.Request(url,headers={"User-Agent":"dab-touchscreen-updater"})
with urllib.request.urlopen(req,timeout=30) as r, open(out,"wb") as f:
    while True:
        b=r.read(1024*1024)
        if not b: break
        f.write(b)
PY
mkdir -p "$stage"
tar -xzf "$archive" -C "$stage" --strip-components=1
rm -f "$archive"

src="$stage/raspberry-pi"
[[ -x "$src/install.sh" || -f "$src/install.sh" ]]
[[ -f "$src/VERSION" && -f "$src/src/main.py" && -d "$src/tests" ]]
chmod 0755 "$src/install.sh"

status verify "Download wird geprüft"
(
    cd "$src"
    PYTHONPATH="$src" python3 -m compileall -q src scripts
    PYTHONPATH="$src" python3 -m unittest discover -s tests -v
)

status backup "Backup der aktuellen Installation wird erstellt"
mkdir -p "$backup"
rsync -a "$INSTALL_DIR/" "$backup/"

status install "Version wird installiert"
"$src/install.sh" --no-apt --no-restart

status health "Installierte Version wird geprüft"
(
    cd "$INSTALL_DIR"
    PYTHONPATH="$INSTALL_DIR" python3 -m compileall -q src scripts
    PYTHONPATH="$INSTALL_DIR" python3 -m unittest discover -s tests -v
)

python3 - "$STATE_DIR/firmware-state.json" "$repo" "$sha" "$label" "$old_commit" <<'PY'
import json,sys,time,os
path,repo,sha,label,previous=sys.argv[1:]
with open(path,"w",encoding="utf-8") as f:
    json.dump({"repository":repo,"sha":sha,"label":label,"previous_sha":previous,"installed_at":int(time.time())},f,ensure_ascii=False,indent=2)
os.chmod(path,0o640)
PY
chown "$SERVICE_USER:$SERVICE_USER" "$STATE_DIR/firmware-state.json"

status restart "Oberfläche wird neu gestartet"
systemctl restart lightdm.service
sleep 8
pgrep -u "$SERVICE_USER" -f '/usr/bin/python3 -m src.main' >/dev/null
status success "Update erfolgreich installiert"

# Keep only the five newest backups.
ls -1dt "$BACKUP_ROOT"/* 2>/dev/null | tail -n +6 | xargs -r rm -rf
rm -rf "$stage"
trap - ERR

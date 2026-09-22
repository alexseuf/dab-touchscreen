#!/usr/bin/env bash
set -Eeuo pipefail
INSTALL_DIR=/opt/dab-touchscreen
STATE_DIR=/var/lib/dab-touchscreen
STATUS_FILE="$STATE_DIR/firmware-update-status.json"
BACKUP_ROOT="$STATE_DIR/firmware-backups"
STAGE_ROOT="$STATE_DIR/firmware-staging"
NETWORK_STATE="$STATE_DIR/network-before-update.json"
WIFI_RADIO_STATE="$STATE_DIR/wifi-radio-before-update"
SERVICE_USER=dab
ALLOWED_REPOSITORY=alexseuf/dab-touchscreen
CURRENT_PHASE=start
repo=${1:-}; sha=${2:-}; label=${3:-unknown}
[[ $EUID -eq 0 ]] || { echo "root required" >&2; exit 1; }
[[ $repo == "$ALLOWED_REPOSITORY" ]] || { echo "Repository not allowed for privileged install" >&2; exit 2; }
[[ $sha =~ ^[0-9a-fA-F]{40}$ ]] || { echo "Invalid commit SHA" >&2; exit 2; }
install -d -o "$SERVICE_USER" -g "$SERVICE_USER" -m 0750 "$STATE_DIR" "$BACKUP_ROOT" "$STAGE_ROOT"
exec 9>"$STATE_DIR/firmware-update.lock"; flock -n 9 || { echo "Update already running" >&2; exit 3; }
status() {
 local state=$1 message=$2
 python3 - "$STATUS_FILE" "$state" "$message" "$sha" "$label" <<'PY'
import json,os,sys,tempfile,time
path,state,message,sha,label=sys.argv[1:]; data={"state":state,"message":message,"sha":sha,"label":label,"time":int(time.time())}
fd,tmp=tempfile.mkstemp(prefix=".fw-status-",dir=os.path.dirname(path),text=True)
with os.fdopen(fd,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False)
os.chmod(tmp,0o640); os.replace(tmp,path)
PY
 chown "$SERVICE_USER:$SERVICE_USER" "$STATUS_FILE"
}
save_wifi_radio_state() {
 local state
 state=$(nmcli -t -f WIFI general 2>/dev/null | head -n1 | tr -d "\r") || state=""
 case "$state" in enabled|aktiviert) printf "enabled\n" >"$WIFI_RADIO_STATE" ;; disabled|deaktiviert) printf "disabled\n" >"$WIFI_RADIO_STATE" ;; *) rm -f "$WIFI_RADIO_STATE" ;; esac
}
restore_wifi_radio_state() {
 [[ -r "$WIFI_RADIO_STATE" ]] || return 0
 case "$(cat "$WIFI_RADIO_STATE")" in enabled) nmcli radio wifi on ;; disabled) nmcli radio wifi off ;; esac
}
save_network_state() {
 # NetworkManager profiles are persistent system state outside the application
 # directory. Firmware installation does not replace them.
 nmcli -f NAME,UUID,TYPE,DEVICE connection show >"$NETWORK_STATE" 2>/dev/null || true
 [[ ! -e "$NETWORK_STATE" ]] || chown root:root "$NETWORK_STATE"
}
restore_network_state() {
 # Intentionally preserve NetworkManager state exactly as it is. Re-applying
 # eth0 IPv4 settings is invalid when eth0 is a br0 bridge port.
 return 0
}

package_signature() {
 python3 - "$1" <<'PY'
import re,sys
try: text=open(sys.argv[1],encoding='utf-8').read()
except OSError: raise SystemExit(1)
m=re.search(r'^PACKAGES=\(\n(.*?)^\)',text,re.M|re.S)
if not m: raise SystemExit(1)
items=[]
for line in m.group(1).splitlines(): line=line.split('#',1)[0].strip(); items.extend(line.split())
print('\n'.join(sorted(set(items))))
PY
}
stamp=$(date +%Y%m%d-%H%M%S); stage="$STAGE_ROOT/$sha"; backup="$BACKUP_ROOT/$stamp-$sha"; archive="$STAGE_ROOT/$sha.tar.gz"; old_commit=""
[[ -r "$STATE_DIR/firmware-state.json" ]] && old_commit=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("sha",""))' "$STATE_DIR/firmware-state.json" 2>/dev/null || true)
rm -rf "$stage" "$archive"; CURRENT_PHASE=download; status download "Commit wird heruntergeladen"
if ! python3 - "$repo" "$sha" "$archive" <<'PY'
import sys,urllib.error,urllib.request
repo,sha,out=sys.argv[1:]; req=urllib.request.Request(f'https://codeload.github.com/{repo}/tar.gz/{sha}',headers={'User-Agent':'dab-touchscreen-updater'})
try:
 with urllib.request.urlopen(req,timeout=30) as r,open(out,'wb') as f:
  while True:
   b=r.read(1024*1024)
   if not b: break
   f.write(b)
except urllib.error.HTTPError as exc: print(f'GitHub HTTP {exc.code}',file=sys.stderr); raise SystemExit(20)
except (urllib.error.URLError,TimeoutError,OSError) as exc: print(f'Download nicht möglich: {exc}',file=sys.stderr); raise SystemExit(21)
PY
then rm -f "$archive"; status failed "Update fehlgeschlagen: Download"; exit 20; fi
mkdir -p "$stage"
if ! tar -xzf "$archive" -C "$stage" --strip-components=1; then rm -rf "$stage" "$archive"; status failed "Update fehlgeschlagen: Firmware-Archiv ungültig"; exit 22; fi
rm -f "$archive"; src="$stage/raspberry-pi"
if [[ ! -f "$src/install.sh" || ! -f "$src/VERSION" || ! -f "$src/src/main.py" || ! -d "$src/tests" ]]; then rm -rf "$stage"; status failed "Update fehlgeschlagen: Projektstruktur ungültig"; exit 23; fi
chmod 0755 "$src/install.sh"; CURRENT_PHASE=verify; status verify "Download wird geprüft"
if ! (cd "$src"; PYTHONPATH="$src" python3 -m compileall -q src scripts; PYTHONPATH="$src" python3 -m unittest discover -s tests -v); then rm -rf "$stage"; status failed "Update fehlgeschlagen: Vorabprüfung"; exit 24; fi
run_apt=0; candidate_packages=$(package_signature "$src/install.sh" 2>/dev/null || true); installed_packages=$(package_signature "$INSTALL_DIR/install.sh" 2>/dev/null || true)
if [[ -z $candidate_packages || -z $installed_packages || $candidate_packages != "$installed_packages" ]]; then run_apt=1; fi
rollback() {
 rc=$?; failed_command=${BASH_COMMAND:-unbekannt}; trap - ERR; status rollback "Fehler in $CURRENT_PHASE (Exit $rc) – Rollback läuft"
 if [[ -d $backup ]]; then rsync -a --delete "$backup/" "$INSTALL_DIR/" || true; chown -R root:root "$INSTALL_DIR" || true; restore_network_state || true; restore_wifi_radio_state || true; systemctl restart lightdm.service || true; status failed "Update fehlgeschlagen: $CURRENT_PHASE · Exit $rc · Rollback erfolgreich"; else status failed "Update fehlgeschlagen: $CURRENT_PHASE · Exit $rc · kein Backup"; fi
 logger -t dab-firmware "Update $sha fehlgeschlagen: Phase=$CURRENT_PHASE Exit=$rc Befehl=$failed_command"; exit "$rc"
}
trap rollback ERR
CURRENT_PHASE=backup; status backup "Installation und Netzwerkeinstellungen werden gesichert"; mkdir -p "$backup"; rsync -a "$INSTALL_DIR/" "$backup/"; rm -f "$NETWORK_STATE" "$WIFI_RADIO_STATE"; save_network_state; save_wifi_radio_state
CURRENT_PHASE=install
if (( run_apt )); then status install "Abhängigkeiten geändert – vollständige Installation"; "$src/install.sh" --no-restart; else status install "Version wird installiert"; "$src/install.sh" --no-apt --no-restart; fi
# Old images may still contain this commissioning unit although its script is no longer part of the application.
# Stop the resulting 30-second restart loop after a successful application install.
if [[ ! -f "$INSTALL_DIR/scripts/autonomous_commissioning.py" ]]; then systemctl disable --now dab-firstboot.service 2>/dev/null || true; fi
CURRENT_PHASE=network; status network "Netzwerk-Konfiguration wird wiederhergestellt"; restore_network_state; restore_wifi_radio_state
CURRENT_PHASE=health; status health "Installierte Version wird geprüft"; (cd "$INSTALL_DIR"; PYTHONPATH="$INSTALL_DIR" python3 -m compileall -q src scripts; PYTHONPATH="$INSTALL_DIR" python3 -m unittest discover -s tests -v)
python3 - "$STATE_DIR/firmware-state.json" "$repo" "$sha" "$label" "$old_commit" <<'PY'
import json,sys,time,os
path,repo,sha,label,previous=sys.argv[1:]
with open(path,'w',encoding='utf-8') as f: json.dump({'repository':repo,'sha':sha,'label':label,'previous_sha':previous,'installed_at':int(time.time())},f,ensure_ascii=False,indent=2)
os.chmod(path,0o640)
PY
chown "$SERVICE_USER:$SERVICE_USER" "$STATE_DIR/firmware-state.json"
# Mark the exact commit as installed before restarting the graphical session.
# systemctl restart lightdm can terminate the updater's calling GUI/session, so
# no critical state write may depend on execution continuing after this point.
CURRENT_PHASE=done; status success "Update erfolgreich installiert"
CURRENT_PHASE=restart; systemctl restart lightdm.service
# Best-effort health observation only: the new GUI may need a few seconds, but
# failure here must not roll back an otherwise verified and installed update.
sleep 8
if ! pgrep -u "$SERVICE_USER" -f 'python3 .*src\.main|python3 -m src\.main' >/dev/null; then
 logger -t dab-firmware "Update $sha installiert, GUI-Prozess nach Neustart noch nicht sichtbar"
fi ls -1dt "$BACKUP_ROOT"/* 2>/dev/null | tail -n +6 | xargs -r rm -rf; rm -rf "$stage"; trap - ERR

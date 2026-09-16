#!/bin/sh
set -eu

SOURCE=/home/openclaw/dab-update
TARGET=/opt/dab-touchscreen
BACKUP=/var/backups/dab-touchscreen-wayland

test "$(id -u)" -eq 0
for package in labwc wf-panel-pi wfplug-squeek squeekboard qtwayland5 wlr-randr autotouch; do
    dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q 'install ok installed'
done
test -f "$SOURCE/app.py"
test -f "$SOURCE/main_window.py"
test -f "$SOURCE/dab-wayland-app.sh"
test -f "$SOURCE/dab-touchscreen-wayland.desktop"
test -f "$SOURCE/dab-use-x11"

mkdir -p "$BACKUP"
cp -a /etc/lightdm/lightdm.conf "$BACKUP/lightdm.conf.x11"
cp -a /etc/lightdm/lightdm.conf.d/50-dab-touchscreen.conf "$BACKUP/50-dab-touchscreen.conf.x11"

install -o root -g root -m 0644 "$SOURCE/app.py" "$TARGET/src/app.py"
install -o root -g root -m 0644 "$SOURCE/main_window.py" "$TARGET/src/ui/main_window.py"
install -o root -g root -m 0755 "$SOURCE/dab-wayland-app.sh" "$TARGET/scripts/dab-wayland-app.sh"
install -o root -g root -m 0755 "$SOURCE/dab-use-x11" /usr/local/sbin/dab-use-x11
install -d -o dab -g dab -m 0755 /home/dab/.config/autostart
install -o dab -g dab -m 0644 "$SOURCE/dab-touchscreen-wayland.desktop" /home/dab/.config/autostart/dab-touchscreen.desktop

for file in /etc/lightdm/lightdm.conf /etc/lightdm/lightdm.conf.d/50-dab-touchscreen.conf; do
    sed -i \
        -e 's/^user-session=.*/user-session=LXDE-pi-labwc/' \
        -e 's/^autologin-session=.*/autologin-session=LXDE-pi-labwc/' \
        "$file"
done

/usr/bin/python3 -m compileall -q "$TARGET/src"
echo DAB_WAYLAND_SQUEEKBOARD_PASS
systemctl restart lightdm.service

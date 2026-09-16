# Historische Laufzeithelfer

Dieses Verzeichnis bewahrt drei exklusive Dateien aus dem früheren Branch
`feature/interactive-chart-focus` auf. Sie dokumentieren den Übergang zwischen
X11 und Wayland/Squeekboard, gehören aber nicht zum aktuellen Installer unter
`raspberry-pi/` und dürfen nicht parallel zu dessen Kiosk-Konfiguration
installiert werden.

Quelle: Commit `e4ddbff` des genannten Feature-Branches.

- `scripts/dab-use-x11`: Rückschaltung auf X11
- `scripts/install-wayland-squeekboard.sh`: früherer Wayland-/Squeekboard-Installer
- `system/dab-touchscreen-wayland.desktop`: frühere Wayland-Autostartdatei

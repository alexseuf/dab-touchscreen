from __future__ import annotations

import html
import json
import os
import re
import subprocess
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

from PyQt5 import QtCore, QtWidgets

from src.ui.main_window import MainWindow

DEFAULT_REPOSITORY = "alexseuf/dab-touchscreen"
ROOT = Path(__file__).resolve().parents[2]


class FirmwareMainWindow(MainWindow):
    """Touch-optimised firmware page with stable/main/test discovery."""

    data_mode_changed = QtCore.pyqtSignal(bool)

    def __init__(self, model, config, history=None):
        self._firmware_busy = False
        self._available_versions = []
        self._settings = QtCore.QSettings("dab-touchscreen", "dab-touchscreen")
        super().__init__(model, config, history)
        self.settings_tabs.insertTab(3, self._firmware_page(), "Firmware")
        self._refresh_installed_version()

    def _settings_tab_changed(self, index):
        self._hide_touch_keyboard()
        if index == 3:
            self._refresh_installed_version()
        if index == 4:
            self.tabs.blockSignals(True)
            self.tabs.setCurrentIndex(self._main_return_index)
            self.tabs.blockSignals(False)
            self.nav_stack.setCurrentWidget(self.tabs)

    def eventFilter(self, obj, event):
        if obj is getattr(self, "fw_repository", None) and event.type() == QtCore.QEvent.MouseButtonPress:
            QtCore.QTimer.singleShot(0, lambda: self._show_touch_keyboard(self.fw_repository))
        return super().eventFilter(obj, event)

    def _firmware_page(self):
        root = QtWidgets.QWidget()
        outer = QtWidgets.QHBoxLayout(root)
        outer.setContentsMargins(8, 6, 8, 6)
        outer.setSpacing(8)

        left = QtWidgets.QFrame(); left.setObjectName("section")
        left_layout = QtWidgets.QVBoxLayout(left)
        left_layout.setContentsMargins(10, 7, 10, 7); left_layout.setSpacing(5)
        title = QtWidgets.QLabel("Firmware / Update")
        title.setStyleSheet("font-size:18px;font-weight:bold")
        left_layout.addWidget(title)

        grid = QtWidgets.QGridLayout(); grid.setHorizontalSpacing(8); grid.setVerticalSpacing(4)
        grid.setColumnStretch(0, 2); grid.setColumnStretch(1, 5)
        left_layout.addLayout(grid)

        self.fw_current = self._firmware_value()
        self.fw_repository = QtWidgets.QLineEdit(self._settings.value("firmware/repository", DEFAULT_REPOSITORY))
        self.fw_repository.setMinimumHeight(34)
        self.fw_repository.setPlaceholderText("owner/repository")
        self.fw_repository.installEventFilter(self)
        self.fw_repository.editingFinished.connect(self._repository_changed)
        self.fw_last_check = self._firmware_value("Noch nicht geprüft")
        self.fw_latest = self._firmware_value("—")
        self.fw_status = self._firmware_value("Bereit")

        self._add_firmware_row(grid, 0, "Aktuelle Version", self.fw_current)
        self._add_firmware_row(grid, 1, "Repository", self.fw_repository)
        self._add_firmware_row(grid, 2, "Letzte Prüfung", self.fw_last_check)

        latest_row = QtWidgets.QWidget(); latest_layout = QtWidgets.QHBoxLayout(latest_row)
        latest_layout.setContentsMargins(0, 0, 0, 0); latest_layout.setSpacing(5)
        latest_layout.addWidget(self.fw_latest, 3)
        self.fw_check_button = QtWidgets.QPushButton("Jetzt prüfen"); self.fw_check_button.setMinimumHeight(38)
        self.fw_check_button.clicked.connect(self._check_firmware_versions); latest_layout.addWidget(self.fw_check_button, 2)
        self._add_firmware_row(grid, 3, "Neueste Version", latest_row)
        self._add_firmware_row(grid, 4, "Status", self.fw_status)

        separator = QtWidgets.QFrame(); separator.setFrameShape(QtWidgets.QFrame.HLine); separator.setStyleSheet("color:#355364")
        left_layout.addWidget(separator)

        mode_row = QtWidgets.QHBoxLayout(); mode_label = QtWidgets.QLabel("Betriebsmodus"); mode_label.setStyleSheet("font-weight:bold")
        mode_row.addWidget(mode_label, 2)
        self.fw_live_button = QtWidgets.QPushButton("Live (MQTT)"); self.fw_demo_button = QtWidgets.QPushButton("Demo")
        self.fw_live_button.setCheckable(True); self.fw_demo_button.setCheckable(True)
        self.fw_live_button.clicked.connect(lambda: self._set_data_mode(False)); self.fw_demo_button.clicked.connect(lambda: self._set_data_mode(True))
        mode_row.addWidget(self.fw_live_button, 2); mode_row.addWidget(self.fw_demo_button, 1); left_layout.addLayout(mode_row)
        self._show_data_mode(bool(self.config["app"].get("demo_data", True)))

        action_row = QtWidgets.QHBoxLayout()
        self.fw_install_button = QtWidgets.QPushButton("Version installieren")
        self.fw_install_button.setEnabled(False)
        self.fw_install_button.setToolTip("Installation wird nach Backup-/Rollback-Test freigeschaltet")
        self.fw_version_combo = QtWidgets.QComboBox(); self.fw_version_combo.addItem("Version wählen …"); self.fw_version_combo.setEnabled(False)
        action_row.addWidget(self.fw_install_button, 3); action_row.addWidget(self.fw_version_combo, 2); left_layout.addLayout(action_row)

        right = QtWidgets.QFrame(); right.setObjectName("section")
        right_layout = QtWidgets.QVBoxLayout(right); right_layout.setContentsMargins(10, 7, 10, 7); right_layout.setSpacing(6)
        heading = QtWidgets.QLabel("Hinweise"); heading.setStyleSheet("font-size:17px;font-weight:bold"); right_layout.addWidget(heading)
        info = QtWidgets.QLabel(
            "Stable = veröffentlichte Releases. Main = aktueller Hauptstand. TEST = Entwicklungszweige feature/*.\n\n"
            "Das Repository kann links geändert werden. Antippen öffnet die Bildschirmtastatur.\n\n"
            "Vor einer Installation wird der exakte Commit festgehalten und ein Backup erstellt. Bei Problemen wird die vorherige Version wiederhergestellt.\n\n"
            "Die Installation bleibt gesperrt, bis Backup, Rollback und Health-Check auf der Zielhardware getestet sind."
        )
        info.setWordWrap(True); info.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft); right_layout.addWidget(info, 1)
        outer.addWidget(left, 3); outer.addWidget(right, 2)
        return root

    @staticmethod
    def _firmware_value(text="—"):
        label = QtWidgets.QLabel(text); label.setMinimumHeight(34); label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
        label.setStyleSheet("background:#183040;border:1px solid #36596c;border-radius:5px;padding:0 8px")
        return label

    @staticmethod
    def _add_firmware_row(grid, row, title, widget):
        label = QtWidgets.QLabel(title); label.setStyleSheet("font-weight:bold"); grid.addWidget(label, row, 0); grid.addWidget(widget, row, 1)

    def _repository_changed(self):
        repo = self.fw_repository.text().strip().strip("/")
        if repo.startswith("https://github.com/"):
            repo = repo[len("https://github.com/"):].removesuffix(".git").strip("/")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            self.fw_status.setText("Repository: owner/name erwartet")
            return
        self.fw_repository.setText(repo)
        self._settings.setValue("firmware/repository", repo)
        self.fw_status.setText("Repository gespeichert")

    def _installed_version(self):
        version_file = ROOT / "VERSION"
        try:
            value = version_file.read_text(encoding="utf-8").strip()
            if value: return value
        except OSError: pass
        return "Entwicklungsstand"

    def _refresh_installed_version(self):
        if hasattr(self, "fw_current"): self.fw_current.setText(self._installed_version())

    def _set_data_mode(self, demo):
        self.config["app"]["demo_data"] = bool(demo); self._show_data_mode(bool(demo)); self.data_mode_changed.emit(bool(demo))

    def _show_data_mode(self, demo):
        if not hasattr(self, "fw_live_button"): return
        self.fw_demo_button.setChecked(demo); self.fw_live_button.setChecked(not demo)
        active = "background:#1687e8;border:1px solid #55d6ff"
        self.fw_demo_button.setStyleSheet(active if demo else ""); self.fw_live_button.setStyleSheet(active if not demo else "")

    def _check_firmware_versions(self):
        if self._firmware_busy: return
        self._repository_changed()
        repo = self.fw_repository.text().strip()
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo): return
        self._firmware_busy = True; self.fw_check_button.setEnabled(False); self.fw_status.setText("GitHub wird geprüft …")
        worker = _FirmwareDiscoveryWorker(repo); worker.signals.result.connect(self._firmware_check_done); worker.signals.error.connect(self._firmware_check_failed); self.threadpool.start(worker)

    def _firmware_check_done(self, result):
        self._firmware_busy = False; self.fw_check_button.setEnabled(True); self.fw_last_check.setText(datetime.now().strftime("%d.%m.%Y %H:%M"))
        versions = result["versions"]; self._available_versions = versions; self.fw_version_combo.clear(); self.fw_version_combo.addItem("Version wählen …", None)
        for item in versions: self.fw_version_combo.addItem(item["label"], item)
        self.fw_version_combo.setEnabled(bool(versions))
        releases = [v for v in versions if v["kind"] == "stable"]
        main = next((v for v in versions if v["kind"] == "main"), None)
        if releases: self.fw_latest.setText(releases[0]["name"])
        elif main: self.fw_latest.setText("Main " + main["sha"][:7])
        else: self.fw_latest.setText("—")
        tests = sum(1 for v in versions if v["kind"] == "test")
        self.fw_status.setText(f"{len(releases)} Stable · Main · {tests} TEST")

    def _firmware_check_failed(self, message):
        self._firmware_busy = False; self.fw_check_button.setEnabled(True); self.fw_last_check.setText(datetime.now().strftime("%d.%m.%Y %H:%M")); self.fw_latest.setText("—")
        self.fw_status.setText("GitHub-Prüfung fehlgeschlagen"); self.fw_status.setToolTip(message)

    def _wifi_status_finished(self, status):
        """Keep all WLAN status lines readable on the 800x480 display."""
        self._wifi_status_running = False; self.wifi_signal.setValue(status["signal"])
        if status["connected"]:
            dbm = f"{status['dbm']} dBm" if status["dbm"] is not None else "— dBm"
            self.wifi_result.setText(
                f"<span style='color:#34d26b'>●</span> <b>WLAN verbunden</b><br>"
                f"SSID: {html.escape(status['ssid'])}<br>"
                f"Signal: {status['signal']} % · {dbm}<br>"
                f"IPv4: <b>{html.escape(status['ipv4'])}</b>"
            )
            self.wifi_result.setStyleSheet("font-size:13px")
            self.wifi_result.setMinimumHeight(88)
            if not self.wifi_ssid.text(): self.wifi_ssid.setText(status["ssid"])
        else:
            self.wifi_result.setText("<span style='color:#e63946'>●</span> <b>Nicht mit WLAN verbunden</b>")


class _FirmwareSignals(QtCore.QObject):
    result = QtCore.pyqtSignal(object); error = QtCore.pyqtSignal(str)


def _github_json(url):
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "dab-touchscreen"})
    with urllib.request.urlopen(request, timeout=8) as response:
        return json.loads(response.read().decode("utf-8"))


class _FirmwareDiscoveryWorker(QtCore.QRunnable):
    def __init__(self, repository):
        super().__init__(); self.repository = repository; self.signals = _FirmwareSignals()

    @QtCore.pyqtSlot()
    def run(self):
        try:
            base = "https://api.github.com/repos/" + urllib.parse.quote(self.repository, safe="/")
            releases = _github_json(base + "/releases?per_page=20")
            branches = _github_json(base + "/branches?per_page=100")
            versions = []
            for item in releases:
                if item.get("draft"): continue
                tag = (item.get("tag_name") or "").strip()
                if tag:
                    versions.append({"kind": "stable", "name": tag, "ref": tag, "sha": "", "label": "Stable · " + tag})
            branch_map = {item.get("name", ""): item.get("commit", {}).get("sha", "") for item in branches}
            if "main" in branch_map:
                sha = branch_map["main"]
                versions.append({"kind": "main", "name": "main", "ref": "main", "sha": sha, "label": f"Main · {sha[:7]}"})
            for name in sorted(n for n in branch_map if n.startswith("feature/")):
                sha = branch_map[name]
                versions.append({"kind": "test", "name": name, "ref": name, "sha": sha, "label": f"TEST · {name} · {sha[:7]}"})
            self.signals.result.emit({"versions": versions})
        except Exception as exc:
            self.signals.error.emit(str(exc))

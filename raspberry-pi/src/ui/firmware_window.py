from __future__ import annotations

import json
import os
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path

from PyQt5 import QtCore, QtWidgets

from src.ui.main_window import MainWindow


REPOSITORY = "alexseuf/dab-touchscreen"
RELEASES_API = "https://api.github.com/repos/alexseuf/dab-touchscreen/releases"
ROOT = Path(__file__).resolve().parents[2]


class FirmwareMainWindow(MainWindow):
    """Main window with the touch-optimised Firmware settings page.

    Phase 1 deliberately keeps installation disabled.  Version discovery and
    data-source switching are safe/read-only operations; update/downgrade is
    enabled only after rollback and health-check support exists.
    """

    data_mode_changed = QtCore.pyqtSignal(bool)  # True = demo, False = live MQTT

    def __init__(self, model, config, history=None):
        self._firmware_busy = False
        self._available_versions = []
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

    def _firmware_page(self):
        root = QtWidgets.QWidget()
        outer = QtWidgets.QHBoxLayout(root)
        outer.setContentsMargins(8, 6, 8, 6)
        outer.setSpacing(8)

        left = QtWidgets.QFrame()
        left.setObjectName("section")
        left_layout = QtWidgets.QVBoxLayout(left)
        left_layout.setContentsMargins(10, 7, 10, 7)
        left_layout.setSpacing(5)

        title = QtWidgets.QLabel("Firmware / Update")
        title.setStyleSheet("font-size:18px;font-weight:bold")
        left_layout.addWidget(title)

        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(4)
        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 5)
        left_layout.addLayout(grid)

        self.fw_current = self._firmware_value()
        self.fw_repository = self._firmware_value(REPOSITORY)
        self.fw_last_check = self._firmware_value("Noch nicht geprüft")
        self.fw_latest = self._firmware_value("—")
        self.fw_status = self._firmware_value("Bereit")

        self._add_firmware_row(grid, 0, "Aktuelle Version", self.fw_current)
        self._add_firmware_row(grid, 1, "Repository", self.fw_repository)
        self._add_firmware_row(grid, 2, "Letzte Prüfung", self.fw_last_check)

        latest_row = QtWidgets.QWidget()
        latest_layout = QtWidgets.QHBoxLayout(latest_row)
        latest_layout.setContentsMargins(0, 0, 0, 0)
        latest_layout.setSpacing(5)
        latest_layout.addWidget(self.fw_latest, 3)
        self.fw_check_button = QtWidgets.QPushButton("Jetzt prüfen")
        self.fw_check_button.setMinimumHeight(38)
        self.fw_check_button.clicked.connect(self._check_firmware_versions)
        latest_layout.addWidget(self.fw_check_button, 2)
        self._add_firmware_row(grid, 3, "Neueste Version", latest_row)
        self._add_firmware_row(grid, 4, "Status", self.fw_status)

        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setStyleSheet("color:#355364")
        left_layout.addWidget(separator)

        mode_row = QtWidgets.QHBoxLayout()
        mode_label = QtWidgets.QLabel("Betriebsmodus")
        mode_label.setStyleSheet("font-weight:bold")
        mode_row.addWidget(mode_label, 2)
        self.fw_live_button = QtWidgets.QPushButton("Live (MQTT)")
        self.fw_demo_button = QtWidgets.QPushButton("Demo")
        self.fw_live_button.setCheckable(True)
        self.fw_demo_button.setCheckable(True)
        self.fw_live_button.clicked.connect(lambda: self._set_data_mode(False))
        self.fw_demo_button.clicked.connect(lambda: self._set_data_mode(True))
        mode_row.addWidget(self.fw_live_button, 2)
        mode_row.addWidget(self.fw_demo_button, 1)
        left_layout.addLayout(mode_row)
        self._show_data_mode(bool(self.config["app"].get("demo_data", True)))

        action_row = QtWidgets.QHBoxLayout()
        self.fw_install_button = QtWidgets.QPushButton("Update installieren")
        self.fw_install_button.setEnabled(False)
        self.fw_install_button.setToolTip("Wird nach Implementierung von Backup/Rollback aktiviert")
        self.fw_version_combo = QtWidgets.QComboBox()
        self.fw_version_combo.addItem("Version wählen …")
        self.fw_version_combo.setEnabled(False)
        action_row.addWidget(self.fw_install_button, 3)
        action_row.addWidget(self.fw_version_combo, 2)
        left_layout.addLayout(action_row)

        right = QtWidgets.QFrame()
        right.setObjectName("section")
        right_layout = QtWidgets.QVBoxLayout(right)
        right_layout.setContentsMargins(10, 7, 10, 7)
        right_layout.setSpacing(6)
        heading = QtWidgets.QLabel("Hinweise")
        heading.setStyleSheet("font-size:17px;font-weight:bold")
        right_layout.addWidget(heading)
        info = QtWidgets.QLabel(
            "Hier wird die installierte Firmware-Version angezeigt und es kann auf neue Versionen geprüft werden.\n\n"
            "Für das Installieren, Downgraden oder Wiederherstellen einer Version ist eine Internetverbindung erforderlich.\n\n"
            "Vor einem Update wird automatisch ein Backup des aktuellen Stands erstellt. Bei Problemen kann die vorherige Version wiederhergestellt werden.\n\n"
            "Neue oder geänderte Systempakete werden über den vollständigen Installer installiert."
        )
        info.setWordWrap(True)
        info.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        right_layout.addWidget(info, 1)

        outer.addWidget(left, 3)
        outer.addWidget(right, 2)
        return root

    @staticmethod
    def _firmware_value(text="—"):
        label = QtWidgets.QLabel(text)
        label.setMinimumHeight(34)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
        label.setStyleSheet("background:#183040;border:1px solid #36596c;border-radius:5px;padding:0 8px")
        return label

    @staticmethod
    def _add_firmware_row(grid, row, title, widget):
        label = QtWidgets.QLabel(title)
        label.setStyleSheet("font-weight:bold")
        grid.addWidget(label, row, 0)
        grid.addWidget(widget, row, 1)

    def _installed_version(self):
        version_file = ROOT / "VERSION"
        try:
            value = version_file.read_text(encoding="utf-8").strip()
            if value:
                return value
        except OSError:
            pass
        try:
            return subprocess.check_output(
                ["git", "-C", str(ROOT), "describe", "--tags", "--always", "--dirty"],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=2,
            ).strip()
        except (OSError, subprocess.SubprocessError):
            return "Entwicklungsstand"

    def _refresh_installed_version(self):
        if hasattr(self, "fw_current"):
            self.fw_current.setText(self._installed_version())

    def _set_data_mode(self, demo):
        self.config["app"]["demo_data"] = bool(demo)
        self._show_data_mode(bool(demo))
        self.data_mode_changed.emit(bool(demo))

    def _show_data_mode(self, demo):
        if not hasattr(self, "fw_live_button"):
            return
        self.fw_demo_button.setChecked(demo)
        self.fw_live_button.setChecked(not demo)
        active = "background:#1687e8;border:1px solid #55d6ff"
        normal = ""
        self.fw_demo_button.setStyleSheet(active if demo else normal)
        self.fw_live_button.setStyleSheet(active if not demo else normal)

    def _check_firmware_versions(self):
        if self._firmware_busy:
            return
        self._firmware_busy = True
        self.fw_check_button.setEnabled(False)
        self.fw_status.setText("GitHub wird geprüft …")
        worker = _FirmwareReleaseWorker()
        worker.signals.result.connect(self._firmware_check_done)
        worker.signals.error.connect(self._firmware_check_failed)
        self.threadpool.start(worker)

    def _firmware_check_done(self, releases):
        self._firmware_busy = False
        self.fw_check_button.setEnabled(True)
        self.fw_last_check.setText(datetime.now().strftime("%d.%m.%Y %H:%M"))
        self._available_versions = releases
        self.fw_version_combo.clear()
        self.fw_version_combo.addItem("Version wählen …")
        for version in releases:
            self.fw_version_combo.addItem(version)
        self.fw_version_combo.setEnabled(bool(releases))
        latest = releases[0] if releases else "Keine Releases"
        self.fw_latest.setText(latest)
        current = self._installed_version()
        if releases and latest != current:
            self.fw_status.setText("Versionen verfügbar – Installation noch gesperrt")
        elif releases:
            self.fw_status.setText("Firmware ist aktuell.")
        else:
            self.fw_status.setText("Keine Firmware-Releases gefunden.")

    def _firmware_check_failed(self, message):
        self._firmware_busy = False
        self.fw_check_button.setEnabled(True)
        self.fw_last_check.setText(datetime.now().strftime("%d.%m.%Y %H:%M"))
        self.fw_latest.setText("—")
        self.fw_status.setText("GitHub-Prüfung fehlgeschlagen")
        self.fw_status.setToolTip(message)


class _FirmwareSignals(QtCore.QObject):
    result = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(str)


class _FirmwareReleaseWorker(QtCore.QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = _FirmwareSignals()

    @QtCore.pyqtSlot()
    def run(self):
        try:
            request = urllib.request.Request(
                RELEASES_API,
                headers={"Accept": "application/vnd.github+json", "User-Agent": "dab-touchscreen"},
            )
            with urllib.request.urlopen(request, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
            versions = [item.get("tag_name", "").strip() for item in payload if not item.get("draft")]
            self.signals.result.emit([version for version in versions if version])
        except Exception as exc:
            self.signals.error.emit(str(exc))

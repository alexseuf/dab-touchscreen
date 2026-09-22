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
UPDATE_STATUS = Path("/var/lib/dab-touchscreen/firmware-update-status.json")
UPDATE_STATE = Path("/var/lib/dab-touchscreen/firmware-state.json")
UPDATE_HELPER = Path("/opt/dab-touchscreen/scripts/firmware-update-helper.sh")


class FirmwareMainWindow(MainWindow):
    """Touch-optimised firmware page with transactional update support."""

    data_mode_changed = QtCore.pyqtSignal(bool)

    def __init__(self, model, config, history=None):
        self._firmware_busy = False
        self._available_versions = []
        self._settings = QtCore.QSettings("dab-touchscreen", "dab-touchscreen")
        super().__init__(model, config, history)
        self.settings_tabs.insertTab(3, self._firmware_page(), "Firmware")
        self._refresh_installed_version()
        self._refresh_last_update_result()
        self._fw_status_timer = QtCore.QTimer(self)
        self._fw_status_timer.setInterval(1000)
        self._fw_status_timer.timeout.connect(self._poll_update_status)

    def _settings_tab_changed(self, index):
        self._hide_touch_keyboard()
        if index == 3:
            self._refresh_installed_version()
            self._refresh_last_update_result()
        if index == 4:
            self.tabs.blockSignals(True)
            self.tabs.setCurrentIndex(self._main_return_index)
            self.tabs.blockSignals(False)
            self.nav_stack.setCurrentWidget(self.tabs)

    def eventFilter(self, obj, event):
        if obj is getattr(self, "fw_repository", None) and event.type() == QtCore.QEvent.MouseButtonPress:
            QtCore.QTimer.singleShot(0, lambda: self._show_touch_keyboard(self.fw_repository))
        keyboard_fields = tuple(getattr(self, "lan_fields", ())) + tuple(
            field for field in (getattr(self, "wifi_password", None), getattr(self, "fw_repository", None)) if field is not None
        )
        if obj in keyboard_fields and event.type() == QtCore.QEvent.KeyPress and event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            QtCore.QTimer.singleShot(0, self._hide_touch_keyboard)
        return super().eventFilter(obj, event)

    def _firmware_page(self):
        root = QtWidgets.QWidget()
        outer = QtWidgets.QHBoxLayout(root); outer.setContentsMargins(8, 6, 8, 6); outer.setSpacing(8)
        left = QtWidgets.QFrame(); left.setObjectName("section")
        left_layout = QtWidgets.QVBoxLayout(left); left_layout.setContentsMargins(10, 7, 10, 7); left_layout.setSpacing(5)
        title = QtWidgets.QLabel("Firmware / Update"); title.setStyleSheet("font-size:18px;font-weight:bold"); left_layout.addWidget(title)
        grid = QtWidgets.QGridLayout(); grid.setHorizontalSpacing(8); grid.setVerticalSpacing(4); grid.setColumnStretch(0, 2); grid.setColumnStretch(1, 5); left_layout.addLayout(grid)
        self.fw_current = self._firmware_value()
        self.fw_repository = QtWidgets.QLineEdit(self._settings.value("firmware/repository", DEFAULT_REPOSITORY)); self.fw_repository.setMinimumHeight(34); self.fw_repository.setPlaceholderText("owner/repository"); self.fw_repository.installEventFilter(self); self.fw_repository.editingFinished.connect(self._repository_changed)
        self.fw_last_check = self._firmware_value("Noch nicht geprüft"); self.fw_latest = self._firmware_value("—"); self.fw_status = self._firmware_value("Bereit")
        self._add_firmware_row(grid, 0, "Aktuelle Version", self.fw_current); self._add_firmware_row(grid, 1, "Repository", self.fw_repository); self._add_firmware_row(grid, 2, "Letzte Prüfung", self.fw_last_check)
        latest_row = QtWidgets.QWidget(); latest_layout = QtWidgets.QHBoxLayout(latest_row); latest_layout.setContentsMargins(0, 0, 0, 0); latest_layout.setSpacing(5); latest_layout.addWidget(self.fw_latest, 3)
        self.fw_check_button = QtWidgets.QPushButton("Jetzt prüfen"); self.fw_check_button.setMinimumHeight(38); self.fw_check_button.clicked.connect(self._check_firmware_versions); latest_layout.addWidget(self.fw_check_button, 2)
        self._add_firmware_row(grid, 3, "Neueste Version", latest_row); self._add_firmware_row(grid, 4, "Status", self.fw_status)

        action_row = QtWidgets.QHBoxLayout()
        self.fw_version_combo = QtWidgets.QComboBox(); self.fw_version_combo.addItem("Version wählen …"); self.fw_version_combo.setEnabled(False); self.fw_version_combo.currentIndexChanged.connect(self._firmware_selection_changed)
        self.fw_install_button = QtWidgets.QPushButton("Version installieren"); self.fw_install_button.setEnabled(False); self.fw_install_button.clicked.connect(self._install_selected_version)
        action_row.addWidget(self.fw_version_combo, 3); action_row.addWidget(self.fw_install_button, 2); left_layout.addLayout(action_row)

        self._show_data_mode(bool(self.config["app"].get("demo_data", True)))

        right = QtWidgets.QFrame(); right.setObjectName("section"); right_layout = QtWidgets.QVBoxLayout(right); right_layout.setContentsMargins(10, 7, 10, 7); right_layout.setSpacing(6)
        heading = QtWidgets.QLabel("Hinweise"); heading.setStyleSheet("font-size:17px;font-weight:bold"); right_layout.addWidget(heading)
        info = QtWidgets.QLabel("Stable = veröffentlichte Releases. Main = aktueller Hauptstand. TEST = Entwicklungszweige feature/* und development/*.\n\nDas Repository kann links geändert werden. Installiert werden aus Sicherheitsgründen nur Versionen aus alexseuf/dab-touchscreen.\n\nVor der Installation wird der exakte Commit geprüft und ein Backup erstellt. Danach folgen Installation, Health-Check und Neustart.\n\nSchlägt ein Schritt fehl, wird automatisch die vorherige Installation wiederhergestellt.")
        info.setWordWrap(True); info.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft); right_layout.addWidget(info, 1)
        outer.addWidget(left, 3); outer.addWidget(right, 2); return root

    @staticmethod
    def _firmware_value(text="—"):
        label = QtWidgets.QLabel(text); label.setMinimumHeight(34); label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft); label.setStyleSheet("background:#183040;border:1px solid #36596c;border-radius:5px;padding:0 8px"); return label

    @staticmethod
    def _add_firmware_row(grid, row, title, widget):
        label = QtWidgets.QLabel(title); label.setStyleSheet("font-weight:bold"); grid.addWidget(label, row, 0); grid.addWidget(widget, row, 1)

    def _repository_changed(self):
        repo = self.fw_repository.text().strip().strip("/")
        if repo.startswith("https://github.com/"): repo = repo[len("https://github.com/"):].removesuffix(".git").strip("/")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo): self.fw_status.setText("Repository: owner/name erwartet"); return
        self.fw_repository.setText(repo); self._settings.setValue("firmware/repository", repo); self.fw_status.setText("Repository gespeichert"); self._firmware_selection_changed()

    def _installed_version(self):
        version = "Entwicklungsstand"
        try:
            value = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
            if value: version = value
        except OSError:
            pass
        try:
            state = json.loads(UPDATE_STATE.read_text(encoding="utf-8"))
            sha = str(state.get("sha", ""))
            label = str(state.get("label", ""))
            if re.fullmatch(r"[0-9a-fA-F]{40}", sha):
                channel = "TEST" if label.startswith("TEST") else ("Main" if label.startswith("Main") else "Stable")
                return f"{version} · {channel} {sha[:7]}"
        except (OSError, ValueError, TypeError):
            pass
        return version

    def _refresh_installed_version(self):
        if hasattr(self, "fw_current"): self.fw_current.setText(self._installed_version())

    def _installed_sha(self):
        try:
            state = json.loads(UPDATE_STATE.read_text(encoding="utf-8"))
            sha = str(state.get("sha", ""))
            return sha if re.fullmatch(r"[0-9a-fA-F]{40}", sha) else ""
        except (OSError, ValueError, TypeError):
            return ""

    def _refresh_last_update_result(self):
        if not hasattr(self, "fw_status") or not UPDATE_STATUS.exists(): return
        try:
            data = json.loads(UPDATE_STATUS.read_text(encoding="utf-8"))
            state = data.get("state", "")
            sha = str(data.get("sha", ""))
            if state == "success" and re.fullmatch(r"[0-9a-fA-F]{40}", sha):
                self.fw_status.setText(f"Update erfolgreich · {sha[:7]}")
            elif state == "failed":
                self.fw_status.setText(str(data.get("message", "Letztes Update fehlgeschlagen")))
        except (OSError, ValueError, TypeError):
            pass

    def _set_data_mode(self, demo):
        self.config["app"]["demo_data"] = bool(demo); self._show_data_mode(bool(demo)); self.data_mode_changed.emit(bool(demo))

    def _show_data_mode(self, demo):
        if not hasattr(self, "fw_live_button") or not hasattr(self, "fw_demo_button"): return
        self.fw_demo_button.setChecked(demo); self.fw_live_button.setChecked(not demo); active = "background:#1687e8;border:1px solid #55d6ff"; self.fw_demo_button.setStyleSheet(active if demo else ""); self.fw_live_button.setStyleSheet(active if not demo else "")

    def _check_firmware_versions(self):
        if self._firmware_busy: return
        self._repository_changed(); repo = self.fw_repository.text().strip()
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo): return
        self._firmware_busy = True; self.fw_check_button.setEnabled(False); self.fw_install_button.setEnabled(False); self.fw_status.setText("GitHub wird geprüft …")
        worker = _FirmwareDiscoveryWorker(repo); worker.signals.result.connect(self._firmware_check_done); worker.signals.error.connect(self._firmware_check_failed); self.threadpool.start(worker)

    def _firmware_check_done(self, result):
        self._firmware_busy = False; self.fw_check_button.setEnabled(True); self.fw_last_check.setText(datetime.now().strftime("%d.%m.%Y %H:%M")); versions = result["versions"]; self._available_versions = versions; self.fw_version_combo.clear(); self.fw_version_combo.addItem("Version wählen …", None)
        for item in versions: self.fw_version_combo.addItem(item["label"], item)
        saved_ref = str(self._settings.value("firmware/selected_ref", "") or "")
        if saved_ref:
            saved_index = next((i for i in range(1, self.fw_version_combo.count()) if (self.fw_version_combo.itemData(i) or {}).get("ref") == saved_ref), 0)
            if saved_index: self.fw_version_combo.setCurrentIndex(saved_index)
        self.fw_version_combo.setEnabled(bool(versions)); releases = [v for v in versions if v["kind"] == "stable"]; main = next((v for v in versions if v["kind"] == "main"), None); test_versions = [v for v in versions if v["kind"] == "test"]; latest_parts = []; latest_parts.append(("Main " + main["sha"][:7] + " · " + main.get("date","—")) if main else "Main —"); latest_parts.append(("TEST " + test_versions[0]["sha"][:7] + " · " + test_versions[0].get("date","—")) if test_versions else "TEST —"); self.fw_latest.setText(" · ".join(latest_parts))
        installed_sha = self._installed_sha()
        installed = next((v for v in versions if v.get("sha") == installed_sha), None)
        if installed and installed.get("date"):
            self.fw_current.setText(self._installed_version() + " · " + installed["date"])
        tests = len(test_versions); self.fw_status.setText(f"{len(releases)} Stable · Main · {tests} TEST"); self._firmware_selection_changed()

    def _firmware_check_failed(self, message):
        self._firmware_busy = False; self.fw_check_button.setEnabled(True); self.fw_last_check.setText(datetime.now().strftime("%d.%m.%Y %H:%M")); self.fw_latest.setText("—"); self.fw_status.setText("GitHub-Prüfung fehlgeschlagen"); self.fw_status.setToolTip(message)

    def _firmware_selection_changed(self):
        item = self.fw_version_combo.currentData() if hasattr(self, "fw_version_combo") else None
        if item and item.get("ref"):
            self._settings.setValue("firmware/selected_ref", item["ref"])
            self._settings.sync()
        allowed = self.fw_repository.text().strip() == DEFAULT_REPOSITORY if hasattr(self, "fw_repository") else False
        self.fw_install_button.setEnabled(bool(item and item.get("sha") and allowed and not self._firmware_busy)) if hasattr(self, "fw_install_button") else None

    def _install_selected_version(self):
        if self._firmware_busy: return
        item = self.fw_version_combo.currentData(); repo = self.fw_repository.text().strip()
        if not item or not re.fullmatch(r"[0-9a-fA-F]{40}", item.get("sha", "")): self.fw_status.setText("Ungültige Versionsauswahl"); return
        if repo != DEFAULT_REPOSITORY: self.fw_status.setText("Installation nur aus Standard-Repository"); return
        answer = QtWidgets.QMessageBox.question(self, "Firmware installieren", f"{item['label']} installieren?\n\nBackup und automatischer Rollback sind aktiv.", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if answer != QtWidgets.QMessageBox.Yes: return
        self._firmware_busy = True; self.fw_install_button.setEnabled(False); self.fw_check_button.setEnabled(False); self.fw_version_combo.setEnabled(False); self.fw_status.setText("Update wird gestartet …")
        try:
            subprocess.Popen(["pkexec", str(UPDATE_HELPER), repo, item["sha"], item["label"]], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
            self._fw_status_timer.start()
        except Exception as exc:
            self._firmware_busy = False; self.fw_check_button.setEnabled(True); self.fw_version_combo.setEnabled(True); self.fw_status.setText("Updater konnte nicht starten"); self.fw_status.setToolTip(str(exc)); self._firmware_selection_changed()

    def _poll_update_status(self):
        try:
            data = json.loads(UPDATE_STATUS.read_text(encoding="utf-8")); state = data.get("state", ""); message = data.get("message", "Update läuft …"); self.fw_status.setText(message)
        except (OSError, ValueError): return
        if state in {"success", "failed"}:
            self._fw_status_timer.stop(); self._firmware_busy = False; self.fw_check_button.setEnabled(True); self.fw_version_combo.setEnabled(True); self._refresh_installed_version(); self._firmware_selection_changed()

    def _wifi_status_finished(self, status):
        self._wifi_status_running = False; self.wifi_signal.setValue(status["signal"])
        if status["connected"]:
            dbm = f"{status['dbm']} dBm" if status["dbm"] is not None else "— dBm"; self.wifi_result.setText(f"<span style='color:#34d26b'>●</span> <b>WLAN verbunden</b><br>SSID: {html.escape(status['ssid'])}<br>Signal: {status['signal']} % · {dbm}<br>IPv4: <b>{html.escape(status['ipv4'])}</b>"); self.wifi_result.setStyleSheet("font-size:13px"); self.wifi_result.setMinimumHeight(88)
            if not self.wifi_ssid.text(): self.wifi_ssid.setText(status["ssid"])
        else: self.wifi_result.setText("<span style='color:#e63946'>●</span> <b>Nicht mit WLAN verbunden</b>")


class _FirmwareSignals(QtCore.QObject):
    result = QtCore.pyqtSignal(object); error = QtCore.pyqtSignal(str)


def _github_json(url):
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "dab-touchscreen"})
    with urllib.request.urlopen(request, timeout=8) as response: return json.loads(response.read().decode("utf-8"))


class _FirmwareDiscoveryWorker(QtCore.QRunnable):
    def __init__(self, repository): super().__init__(); self.repository = repository; self.signals = _FirmwareSignals()

    @QtCore.pyqtSlot()
    def run(self):
        try:
            base = "https://api.github.com/repos/" + urllib.parse.quote(self.repository, safe="/"); releases = _github_json(base + "/releases?per_page=20"); branches = _github_json(base + "/branches?per_page=100"); versions = []
            for item in releases:
                if item.get("draft"): continue
                tag = (item.get("tag_name") or "").strip()
                if tag:
                    commit = _github_json(base + "/commits/" + urllib.parse.quote(tag, safe="")); sha = commit.get("sha", ""); versions.append({"kind":"stable","name":tag,"ref":tag,"sha":sha,"label":f"Stable · {tag} · {sha[:7]}"})
            branch_map = {item.get("name", ""): item.get("commit", {}).get("sha", "") for item in branches}
            if "main" in branch_map:
                sha = branch_map["main"]; commit = _github_json(base + "/commits/" + sha); date = str(commit.get("commit",{}).get("committer",{}).get("date",""))[:10]; versions.append({"kind":"main","name":"main","ref":"main","sha":sha,"date":date,"label":f"Main · {sha[:7]}"})
            for name in sorted(n for n in branch_map if n.startswith(("feature/","development/"))):
                sha = branch_map[name]; commit = _github_json(base + "/commits/" + sha); date = str(commit.get("commit",{}).get("committer",{}).get("date",""))[:10]; versions.append({"kind":"test","name":name,"ref":name,"sha":sha,"date":date,"label":f"TEST · {name} · {sha[:7]}"})
            self.signals.result.emit({"versions":versions})
        except Exception as exc: self.signals.error.emit(str(exc))

from __future__ import annotations

from PyQt5 import QtCore, QtWidgets

from src.network.service import set_wifi_radio
from src.ui.test_window import TestMainWindow


class WifiMainWindow(TestMainWindow):
    """TEST UI with a global NetworkManager Wi-Fi radio switch."""

    def _wifi(self):
        root = super()._wifi()
        grid = root.layout()
        buttons = {button.text(): button for button in root.findChildren(QtWidgets.QPushButton)}
        self.wifi_connect_button = buttons.get("Verbinden")
        self.wifi_disconnect_button = buttons.get("Trennen")

        # Put connect/disconnect next to each other to free one full row.
        action_row = QtWidgets.QWidget()
        actions = QtWidgets.QHBoxLayout(action_row)
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(5)
        for button in (self.wifi_connect_button, self.wifi_disconnect_button):
            if button is not None:
                grid.removeWidget(button)
                actions.addWidget(button, 1)
        grid.addWidget(action_row, 5, 1)

        # Global radio control. This intentionally does not delete or modify
        # saved NetworkManager connection profiles or WLAN passwords.
        self.wifi_master_button = QtWidgets.QPushButton("WLAN Hauptschalter: …")
        self.wifi_master_button.setCheckable(True)
        self.wifi_master_button.setMinimumHeight(42)
        self.wifi_master_button.setToolTip("WLAN-Funkmodul global ein-/ausschalten; gespeicherte WLAN-Zugänge bleiben erhalten")
        self.wifi_master_button.clicked.connect(self._set_wifi_master)
        grid.addWidget(self.wifi_master_button, 6, 1)
        return root

    def _set_wifi_master(self, enabled):
        self.wifi_master_button.setEnabled(False)
        self.wifi_master_button.setText("WLAN wird eingeschaltet …" if enabled else "WLAN wird ausgeschaltet …")
        self._run_worker(set_wifi_radio, (bool(enabled),), self._wifi_master_finished, self._wifi_master_failed)

    def _wifi_master_finished(self, result):
        self.wifi_master_button.setEnabled(True)
        if result.returncode != 0:
            self.wifi_result.setText("WLAN konnte nicht geschaltet werden: " + (result.stderr or result.stdout).strip())
        QtCore.QTimer.singleShot(300, self._refresh_wifi_status)
        if self.wifi_master_button.isChecked():
            QtCore.QTimer.singleShot(900, self._scan_wifi)

    def _wifi_master_failed(self, error):
        self.wifi_master_button.setEnabled(True)
        self.wifi_result.setText("WLAN konnte nicht geschaltet werden: " + str(error))
        QtCore.QTimer.singleShot(300, self._refresh_wifi_status)

    def _wifi_status_finished(self, status):
        super()._wifi_status_finished(status)
        enabled = bool(status.get("radio_enabled", True))
        self.wifi_master_button.setChecked(enabled)
        self.wifi_master_button.setText("WLAN Hauptschalter: EIN" if enabled else "WLAN Hauptschalter: AUS")
        active_style = "background:#1687e8;border:1px solid #55d6ff" if enabled else "background:#4a2529;border:1px solid #8b2f34"
        self.wifi_master_button.setStyleSheet(active_style)
        for widget in (self.wifi_scan_button, self.wifi_ssid, self.wifi_password, self.wifi_reveal, self.keyboard_button, self.wifi_connect_button, self.wifi_disconnect_button):
            if widget is not None:
                widget.setEnabled(enabled)
        if not enabled:
            self.wifi_list.clear()
            self.wifi_signal.setValue(0)
            self.wifi_result.setText("<span style='color:#e63946'>●</span> <b>WLAN global ausgeschaltet</b><br>Gespeicherte WLAN-Zugänge bleiben erhalten.")

    def _scan_wifi(self):
        if hasattr(self, "wifi_master_button") and not self.wifi_master_button.isChecked():
            self.wifi_result.setText("WLAN ist global ausgeschaltet.")
            return
        super()._scan_wifi()

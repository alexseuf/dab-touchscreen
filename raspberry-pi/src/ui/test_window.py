from __future__ import annotations

import ipaddress
import time

from PyQt5 import QtCore, QtWidgets

from src.ui.firmware_window import FirmwareMainWindow


class TestMainWindow(FirmwareMainWindow):
    """Incremental test UI additions kept isolated from the stable window."""

    def _lan(self):
        root = super()._lan()
        # Stack Ethernet above the local MQTT status. This keeps all IPv4 input
        # fields high enough to remain visible when the Wayland OSK is open.
        layout = root.layout()
        if isinstance(layout, QtWidgets.QBoxLayout):
            layout.setDirection(QtWidgets.QBoxLayout.TopToBottom)
            layout.setStretch(0, 3)
            layout.setStretch(1, 2)

        # Users normally recognise the IPv4 subnet mask more readily than the
        # CIDR prefix length. NetworkManager still receives CIDR internally.
        self.lan_prefix.setPlaceholderText("255.255.255.0")
        for label in root.findChildren(QtWidgets.QLabel):
            if label.text() == "Prefix":
                label.setText("Subnetzmaske")
                break
        self._lan_mode_changed()
        return root

    def _lan_mode_changed(self):
        manual = self.lan_static.isChecked()
        for field in self.lan_fields:
            field.setEnabled(manual)
            field.setReadOnly(not manual)
            field.setFocusPolicy(QtCore.Qt.StrongFocus if manual else QtCore.Qt.NoFocus)
            if not manual:
                field.clearFocus()
        if not manual:
            # A field that had focus before switching to DHCP must not leave
            # the Wayland on-screen keyboard covering the kiosk UI.
            self._hide_touch_keyboard()

    def eventFilter(self, obj, event):
        if obj in getattr(self, "lan_fields", ()) and event.type() == QtCore.QEvent.MouseButtonPress:
            if getattr(self, "lan_dhcp", None) is not None and self.lan_dhcp.isChecked():
                # DHCP fields are display-only: no focus and no OSK.
                obj.clearFocus()
                self._hide_touch_keyboard()
                return True

            # In manual mode preserve the existing value. The normal focus
            # path on the touchscreen can select the complete QLineEdit, which
            # makes the first typed digit replace the whole address. Position
            # the cursor exactly where the user touched instead.
            obj.setFocus(QtCore.Qt.MouseFocusReason)
            obj.deselect()
            obj.setCursorPosition(obj.cursorPositionAt(event.pos()))
            QtCore.QTimer.singleShot(0, lambda field=obj: self._show_touch_keyboard(field))
            return True
        return super().eventFilter(obj, event)

    @staticmethod
    def _prefix_to_netmask(prefix):
        try:
            return str(ipaddress.IPv4Network(f"0.0.0.0/{int(prefix)}").netmask)
        except (ValueError, TypeError):
            return str(prefix or "")

    @staticmethod
    def _netmask_to_prefix(mask):
        value = str(mask or "").strip()
        if "." not in value:
            return value
        try:
            return str(ipaddress.IPv4Network(f"0.0.0.0/{value}").prefixlen)
        except (ValueError, TypeError):
            return value

    def _network_refreshed(self, status):
        shown = dict(status)
        shown["prefix"] = self._prefix_to_netmask(status.get("prefix", "24"))
        super()._network_refreshed(shown)

    def _apply_lan(self):
        # Keep the UI in dotted-decimal notation while passing the existing
        # network service the CIDR prefix it expects (e.g. 255.255.255.0 -> 24).
        shown_mask = self.lan_prefix.text()
        self.lan_prefix.setText(self._netmask_to_prefix(shown_mask))
        try:
            super()._apply_lan()
        finally:
            self.lan_prefix.setText(shown_mask)

    def _mqtt_page(self):
        root = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(root)
        left = QtWidgets.QVBoxLayout()
        toolbar = QtWidgets.QHBoxLayout()
        self.filter = QtWidgets.QLineEdit()
        self.filter.setPlaceholderText("Topic filtern …")
        self.filter.textChanged.connect(self._rebuild_topics)
        clear = QtWidgets.QPushButton("Liste leeren")
        clear.setToolTip("Aktuelle Explorer-Liste leeren; neue MQTT-Nachrichten werden danach wieder angezeigt")
        clear.clicked.connect(self._clear_mqtt_explorer)
        toolbar.addWidget(self.filter, 3)
        toolbar.addWidget(clear, 2)
        left.addLayout(toolbar)
        self.topics = QtWidgets.QTreeWidget()
        self.topics.setHeaderLabel("Topics")
        self.topics.setItemsExpandable(False)
        self.topics.setExpandsOnDoubleClick(False)
        self.topics.itemClicked.connect(self._topic_clicked)
        self.topics.itemSelectionChanged.connect(self._topic_selected)
        left.addWidget(self.topics)
        self.detail = QtWidgets.QPlainTextEdit()
        self.detail.setReadOnly(True)
        layout.addLayout(left, 2)
        layout.addWidget(self.detail, 3)
        return root

    def _clear_mqtt_explorer(self):
        # This intentionally clears only the local observer state. It neither
        # publishes tombstones nor reconnects/resubscribes, so retained broker
        # messages are not modified or replayed by this action.
        self.explorer.clear()
        self.topics.clear()
        self.detail.clear()

    def _refresh(self):
        # Keep the compact bottom status line useful during commissioning: show
        # the configured MQTT broker address only while the client is connected.
        for sid, card in self.cards.items():
            card.set_value(self.model.get(sid))
        for sid, curve in self.curves.items():
            pts = self.samples[sid]
            curve.setData([x for x, _ in pts], [y for _, y in pts])
        connected = bool(self.mqtt and self.mqtt.connected)
        if connected:
            host = str(self.config.get("mqtt", {}).get("host", "")).strip()
            broker = f" {host}" if host else ""
            self.status.setText(f"MQTT: verbunden{broker}   {time.strftime('%H:%M:%S')}")
        else:
            self.status.setText(f"MQTT: nicht verbunden   {time.strftime('%H:%M:%S')}")

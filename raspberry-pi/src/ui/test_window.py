from __future__ import annotations

import html
import ipaddress
import time

from PyQt5 import QtCore, QtWidgets

from src.network.service import broker_status
from src.ui.firmware_window import FirmwareMainWindow


class TestMainWindow(FirmwareMainWindow):
    """Incremental test UI additions kept isolated from the stable window."""

    def _lan(self):
        root = super()._lan()
        layout = root.layout()
        if isinstance(layout, QtWidgets.QBoxLayout):
            layout.setDirection(QtWidgets.QBoxLayout.TopToBottom)
            # Ethernet gets almost all available height; MQTT is a compact row.
            layout.setStretch(0, 6)
            layout.setStretch(1, 1)

        # Move DHCP/static selection into the Ethernet heading row. This frees
        # one complete row for larger input fields and higher action buttons.
        ethernet = self.lan_dhcp.parentWidget()
        form = ethernet.layout() if ethernet is not None else None
        if isinstance(form, QtWidgets.QGridLayout):
            title = None
            for label in ethernet.findChildren(QtWidgets.QLabel):
                if label.text() == "Ethernet / IPv4":
                    title = label
                    break
            if title is not None:
                form.addWidget(title, 0, 0, 1, 2)
            form.addWidget(self.lan_dhcp, 0, 2)
            form.addWidget(self.lan_static, 0, 3)
            form.setRowMinimumHeight(0, 34)
            for row in range(2, 6):
                form.setRowMinimumHeight(row, 42)
            form.setRowStretch(7, 1)

        self.lan_prefix.setPlaceholderText("255.255.255.0")
        for label in root.findChildren(QtWidgets.QLabel):
            if label.text() == "Prefix":
                label.setText("Subnetzmaske")
                break

        # Make the local broker section compact. The dynamic label itself is
        # rendered as three columns: state | broker address | port.
        mqtt_frame = self.lan_mqtt_status.parentWidget()
        mqtt_layout = mqtt_frame.layout() if mqtt_frame is not None else None
        if isinstance(mqtt_layout, QtWidgets.QVBoxLayout):
            for index in reversed(range(mqtt_layout.count())):
                item = mqtt_layout.itemAt(index)
                widget = item.widget()
                if widget is not None and widget is not self.lan_mqtt_status:
                    mqtt_layout.removeWidget(widget)
                    widget.hide()
            title = QtWidgets.QLabel("Lokaler MQTT-Broker")
            title.setStyleSheet("font-size:16px;font-weight:bold")
            mqtt_layout.insertWidget(0, title)
            self.lan_mqtt_status.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
            self.lan_mqtt_status.setMinimumHeight(40)
            self.lan_mqtt_status.setMaximumHeight(46)

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
            self._hide_touch_keyboard()

    def eventFilter(self, obj, event):
        if obj in getattr(self, "lan_fields", ()) and event.type() == QtCore.QEvent.MouseButtonPress:
            if getattr(self, "lan_dhcp", None) is not None and self.lan_dhcp.isChecked():
                obj.clearFocus()
                self._hide_touch_keyboard()
                return True
            # Keep the old address and place the cursor at the touched digit.
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
        self._update_compact_broker_status()

    def _update_compact_broker_status(self):
        broker = broker_status()
        color = "#34d26b" if broker["running"] else "#e63946"
        state = "Läuft" if broker["running"] else "Nicht erreichbar"
        self._broker_host = str(broker["host"])
        self.lan_mqtt_status.setText(
            f"<table width='100%'><tr>"
            f"<td width='28%'><span style='color:{color};font-size:20px'>●</span> <b>{state}</b></td>"
            f"<td width='52%'><b>Broker-Adresse</b>&nbsp; mqtt://{html.escape(self._broker_host)}</td>"
            f"<td width='20%'><b>Port</b>&nbsp; {broker['port']}</td>"
            f"</tr></table>"
        )

    def _apply_lan(self):
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
        self.explorer.clear()
        self.topics.clear()
        self.detail.clear()

    def _refresh(self):
        for sid, card in self.cards.items():
            card.set_value(self.model.get(sid))
        for sid, curve in self.curves.items():
            pts = self.samples[sid]
            curve.setData([x for x, _ in pts], [y for _, y in pts])
        connected = bool(self.mqtt and self.mqtt.connected)
        if connected:
            # Use the same externally reachable broker address that is shown on
            # the LAN page instead of the MQTT client's loopback host 127.0.0.1.
            host = getattr(self, "_broker_host", "")
            if not host:
                host = str(broker_status()["host"])
                self._broker_host = host
            self.status.setText(f"MQTT: verbunden {host}   {time.strftime('%H:%M:%S')}")
        else:
            self.status.setText(f"MQTT: nicht verbunden   {time.strftime('%H:%M:%S')}")

from __future__ import annotations

import html
import ipaddress
import json
import time

from PyQt5 import QtCore, QtWidgets

from src.network.service import broker_status, bridge_status, configure_usb_ethernet_bridge, ethernet_status, set_ethernet
from src.ui.firmware_window import FirmwareMainWindow


class TestMainWindow(FirmwareMainWindow):
    """Incremental test UI additions kept isolated from the stable window."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # QSettings lives in the user's persistent config area, outside
        # /opt/dab-touchscreen, and therefore survives firmware updates.
        saved_demo = self._settings.value("app/demo_data", None)
        if saved_demo is not None:
            demo = str(saved_demo).lower() in ("1", "true", "yes", "on")
            self.config["app"]["demo_data"] = demo
            self._show_data_mode(demo)
        app = QtWidgets.QApplication.instance()
        if app is not None:
            app.installEventFilter(self)

    def _lan(self):
        root = super()._lan()
        layout = root.layout()
        if isinstance(layout, QtWidgets.QBoxLayout):
            layout.setDirection(QtWidgets.QBoxLayout.TopToBottom); layout.setStretch(0, 2); layout.setStretch(1, 1)
        ethernet = self.lan_dhcp.parentWidget(); form = ethernet.layout() if ethernet is not None else None
        if isinstance(form, QtWidgets.QGridLayout):
            form.setContentsMargins(7, 2, 7, 2); form.setHorizontalSpacing(6); form.setVerticalSpacing(1)
            title = next((label for label in ethernet.findChildren(QtWidgets.QLabel) if label.text() == "Ethernet / IPv4"), None)
            labels = {label.text(): label for label in ethernet.findChildren(QtWidgets.QLabel)}
            if title is not None: title.setStyleSheet("font-size:17px;font-weight:bold"); form.addWidget(title, 0, 0, 1, 2)
            form.addWidget(self.lan_dhcp, 0, 2); form.addWidget(self.lan_static, 0, 3)
            for row, (name, field) in enumerate([("IP-Adresse", self.lan_address), ("Prefix", self.lan_prefix), ("Gateway", self.lan_gateway), ("DNS-Server", self.lan_dns)], 1):
                label = labels.get(name)
                if label is not None: form.addWidget(label, row, 0, alignment=QtCore.Qt.AlignVCenter)
                form.addWidget(field, row, 1, alignment=QtCore.Qt.AlignVCenter); field.setFixedHeight(36)
            form.addWidget(self.lan_refresh_button, 1, 2, 1, 2, alignment=QtCore.Qt.AlignTop); form.addWidget(self.lan_apply_button, 2, 2, 1, 2, alignment=QtCore.Qt.AlignTop)
            self.lan_refresh_button.setFixedHeight(34); self.lan_apply_button.setFixedHeight(34)
            self.lan_bridge_button = QtWidgets.QPushButton("USB-Bridge einrichten")
            self.lan_bridge_button.setFixedHeight(34); self.lan_bridge_button.setToolTip("eth0 und USB-Ethernet transparent über br0 verbinden; br0 erhält 192.168.2.138/24 ohne Gateway/DNS")
            self.lan_bridge_button.clicked.connect(self._configure_usb_bridge)
            form.addWidget(self.lan_bridge_button, 3, 2, 1, 2, alignment=QtCore.Qt.AlignTop)
            self.lan_bridge_status = QtWidgets.QLabel(); self.lan_bridge_status.setWordWrap(True)
            form.addWidget(self.lan_bridge_status, 4, 2, 1, 2, alignment=QtCore.Qt.AlignTop)
            form.addWidget(self.lan_result, 5, 2, 1, 2, alignment=QtCore.Qt.AlignTop)
            form.setColumnStretch(0, 2); form.setColumnStretch(1, 5); form.setColumnStretch(2, 2); form.setColumnStretch(3, 2); form.setRowMinimumHeight(0, 28)
            for row in range(1, 6): form.setRowMinimumHeight(row, 30); form.setRowStretch(row, 0)
            form.setRowStretch(5, 1); ethernet.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding); ethernet.setMaximumHeight(16777215)
        self.lan_prefix.setPlaceholderText("255.255.255.0")
        for label in root.findChildren(QtWidgets.QLabel):
            if label.text() == "Prefix": label.setText("Subnetzmaske"); break
        mqtt_frame = self.lan_mqtt_status.parentWidget(); mqtt_layout = mqtt_frame.layout() if mqtt_frame is not None else None
        if isinstance(mqtt_layout, QtWidgets.QVBoxLayout):
            for index in reversed(range(mqtt_layout.count())):
                widget = mqtt_layout.itemAt(index).widget()
                if widget is not None and widget is not self.lan_mqtt_status: mqtt_layout.removeWidget(widget); widget.hide()
            mqtt_layout.setContentsMargins(10, 5, 10, 5); mqtt_layout.setSpacing(3)
            title = QtWidgets.QLabel("Lokaler MQTT-Broker"); title.setStyleSheet("font-size:16px;font-weight:bold"); mqtt_layout.insertWidget(0, title)
            self.lan_mqtt_status.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft); self.lan_mqtt_status.setWordWrap(True); self.lan_mqtt_status.setMinimumHeight(82); self.lan_mqtt_status.setMaximumHeight(110)
            hint = QtWidgets.QLabel("LAN wird als Broker-Adresse bevorzugt. WLAN bleibt als Recovery-Zugang verfügbar."); hint.setWordWrap(True); hint.setStyleSheet("color:#9edcff;font-size:12px"); mqtt_layout.addWidget(hint); mqtt_layout.addStretch(1)
        self.lan_gateway.setPlaceholderText("optional – leer = keine Default-Route")
        self.lan_dns.setPlaceholderText("optional")
        self._refresh_bridge_status()
        self._lan_mode_changed(); return root

    def _refresh_bridge_status(self):
        if not hasattr(self, "lan_bridge_status"): return
        status=bridge_status()
        if status["configured"]:
            members=", ".join(status["members"]) or "—"
            self.lan_bridge_status.setText(f"<b>br0 aktiv:</b> {status['ipv4']} · Mitglieder: {members}")
        else:
            self.lan_bridge_status.setText("<b>br0:</b> noch nicht eingerichtet")

    def _configure_usb_bridge(self):
        self.lan_bridge_button.setEnabled(False)
        self.lan_bridge_status.setText("USB-Bridge wird eingerichtet …")
        self._run_worker(configure_usb_ethernet_bridge, (), self._usb_bridge_finished, self._usb_bridge_failed)

    def _usb_bridge_finished(self, result):
        self.lan_bridge_button.setEnabled(True)
        if result.returncode:
            self.lan_bridge_status.setText("Bridge fehlgeschlagen: " + (result.stderr or result.stdout).strip())
        else:
            self._refresh_bridge_status()
            self._refresh_network()

    def _usb_bridge_failed(self, error):
        self.lan_bridge_button.setEnabled(True)
        self.lan_bridge_status.setText("Bridge nicht eingerichtet: " + str(error))

    def _lan_mode_changed(self):
        manual = self.lan_static.isChecked()
        for field in self.lan_fields:
            field.setEnabled(manual); field.setReadOnly(not manual); field.setFocusPolicy(QtCore.Qt.StrongFocus if manual else QtCore.Qt.NoFocus)
            if not manual: field.clearFocus()
        if not manual: self._hide_touch_keyboard()

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_F12: self._hide_touch_keyboard(); return True
        editable = obj in getattr(self, "lan_fields", ()) or obj is getattr(self, "wifi_password", None) or obj is getattr(self, "filter", None)
        if editable and event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Escape: self._hide_touch_keyboard(); return True
        if obj is getattr(self, "filter", None) and event.type() == QtCore.QEvent.MouseButtonPress:
            obj.setFocus(QtCore.Qt.MouseFocusReason); obj.deselect(); obj.setCursorPosition(obj.cursorPositionAt(event.pos())); QtCore.QTimer.singleShot(0, lambda field=obj: self._show_touch_keyboard(field)); return True
        if obj in getattr(self, "lan_fields", ()) and event.type() == QtCore.QEvent.MouseButtonPress:
            if getattr(self, "lan_dhcp", None) is not None and self.lan_dhcp.isChecked(): obj.clearFocus(); self._hide_touch_keyboard(); return True
            obj.setFocus(QtCore.Qt.MouseFocusReason); obj.deselect(); obj.setCursorPosition(obj.cursorPositionAt(event.pos())); QtCore.QTimer.singleShot(0, lambda field=obj: self._show_touch_keyboard(field)); return True
        return super().eventFilter(obj, event)

    @staticmethod
    def _prefix_to_netmask(prefix):
        try: return str(ipaddress.IPv4Network(f"0.0.0.0/{int(prefix)}").netmask)
        except (ValueError, TypeError): return str(prefix or "")

    @staticmethod
    def _netmask_to_prefix(mask):
        value = str(mask or "").strip()
        if "." not in value: return value
        try: return str(ipaddress.IPv4Network(f"0.0.0.0/{value}").prefixlen)
        except (ValueError, TypeError): return value

    def _network_refreshed(self, status):
        shown = dict(status); shown["prefix"] = self._prefix_to_netmask(status.get("prefix", "24")); super()._network_refreshed(shown); self._update_compact_broker_status()

    def _update_compact_broker_status(self):
        broker = broker_status(); color = "#34d26b" if broker["running"] else "#e63946"; state = "Läuft" if broker["running"] else "Nicht erreichbar"; self._broker_host = str(broker["host"])
        self.lan_mqtt_status.setText(f"<span style='color:{color};font-size:20px'>●</span> <b>{state}</b>&nbsp;&nbsp;&nbsp; <b>Broker-Adresse:</b> mqtt://{html.escape(self._broker_host)}&nbsp;&nbsp;&nbsp; <b>Port:</b> {broker['port']}<br><b>Bevorzugter Netzwerkweg:</b> {html.escape(str(broker['preferred']))}<br><b>Erreichbar über:</b> {html.escape(str(broker['preferred']))} · {html.escape(self._broker_host)}:{broker['port']}")

    def _apply_lan(self):
        # Once br0 exists, the IP configuration belongs to the bridge itself.
        # eth0/USB are pure L2 bridge ports and must not carry their own IPv4.
        shown_mask=self.lan_prefix.text()
        prefix=self._netmask_to_prefix(shown_mask)
        method='manual' if self.lan_static.isChecked() else 'auto'
        interface='br0' if bridge_status()['configured'] else self.config['network']['ethernet_interface']
        self.lan_apply_button.setEnabled(False)
        self.lan_result.setText(f'{interface}-Konfiguration wird geprüft und angewendet …')
        args=(interface,method,self.lan_address.text(),prefix,self.lan_gateway.text(),self.lan_dns.text())
        self._run_worker(set_ethernet,args,self._lan_applied,self._lan_failed)

    def _refresh_network(self):
        if not hasattr(self,'lan_refresh_button'): return
        self.lan_refresh_button.setEnabled(False)
        interface='br0' if bridge_status()['configured'] else self.config['network']['ethernet_interface']
        self._run_worker(ethernet_status,(interface,),self._network_refreshed,self._lan_failed)

    def _set_data_mode(self, demo):
        super()._set_data_mode(demo)
        self._settings.setValue("app/demo_data", bool(demo))
        self._settings.sync()

    def _system_page(self):
        root = super()._system_page()
        outer = root.layout()
        if isinstance(outer, QtWidgets.QVBoxLayout):
            # Compact SSD SMART/health summary. Values are refreshed separately
            # so the normal system-status refresh remains lightweight.
            self.ssd_health_label = QtWidgets.QLabel("<b>SSD-Gesundheit:</b> wird geprüft …")
            self.ssd_health_label.setWordWrap(True)
            self.ssd_health_label.setStyleSheet("padding:5px;border:1px solid #2f88c9;border-radius:4px")
            outer.insertWidget(max(0, outer.count() - 1), self.ssd_health_label)
            QtCore.QTimer.singleShot(400, self._refresh_ssd_health)
            self._ssd_health_timer = QtCore.QTimer(root)
            self._ssd_health_timer.timeout.connect(self._refresh_ssd_health)
            self._ssd_health_timer.start(60000)

            # Bottom row exactly as approved: reset | Betriebsmodus | Live | Demo.
            bottom = QtWidgets.QHBoxLayout()
            reset = QtWidgets.QPushButton("Werkseinstellungen wiederherstellen")
            reset.setFixedHeight(44)
            reset.setToolTip("DAB-Anwendungseinstellungen zurücksetzen; LAN und WLAN bleiben erhalten")
            reset.clicked.connect(self._confirm_factory_reset)
            mode_label = QtWidgets.QLabel("Betriebsmodus"); mode_label.setStyleSheet("font-weight:bold")
            mode_label.setAlignment(QtCore.Qt.AlignCenter)
            self.fw_live_button = QtWidgets.QPushButton("Live (MQTT)"); self.fw_demo_button = QtWidgets.QPushButton("Demo")
            self.fw_live_button.setFixedHeight(44); self.fw_demo_button.setFixedHeight(44)
            self.fw_live_button.setCheckable(True); self.fw_demo_button.setCheckable(True)
            self.fw_live_button.clicked.connect(lambda: self._set_data_mode(False)); self.fw_demo_button.clicked.connect(lambda: self._set_data_mode(True))
            bottom.addWidget(reset, 3); bottom.addWidget(mode_label, 2); bottom.addWidget(self.fw_live_button, 3); bottom.addWidget(self.fw_demo_button, 2)
            outer.insertLayout(max(0, outer.count() - 1), bottom)
            self._show_data_mode(bool(self.config["app"].get("demo_data", True)))
        return root

    def _refresh_ssd_health(self):
        if not hasattr(self, "ssd_health_label"): return
        def read_health():
            import json as _json
            # Root filesystem device; strip partition suffix for common SATA/NVMe names.
            src = subprocess.run(["findmnt","-n","-o","SOURCE","/"], text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False, timeout=2).stdout.strip()
            dev = src
            if "/dev/nvme" in dev: dev = re.sub(r"p\\d+$", "", dev)
            elif dev.startswith("/dev/"): dev = re.sub(r"\\d+$", "", dev)
            if not dev.startswith("/dev/"): return {"available":False}
            proc = subprocess.run(["smartctl","-a","-j",dev], text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False, timeout=8)
            try: data=_json.loads(proc.stdout or "{}")
            except ValueError: return {"available":False}
            temp=data.get("temperature",{}).get("current")
            hours=data.get("power_on_time",{}).get("hours")
            cycles=data.get("power_cycle_count")
            passed=data.get("smart_status",{}).get("passed")
            nv=data.get("nvme_smart_health_information_log",{})
            used=nv.get("percentage_used")
            written=nv.get("data_units_written")
            tb=None
            if isinstance(written,(int,float)): tb=written*512000/1e12
            health=(max(0,100-used) if isinstance(used,(int,float)) else None)
            return {"available":True,"passed":passed,"temp":temp,"hours":hours,"cycles":cycles,"health":health,"tb":tb}
        self._run_worker(read_health, (), self._ssd_health_ready, lambda _e:self._ssd_health_unavailable())

    def _ssd_health_unavailable(self):
        if hasattr(self,"ssd_health_label"): self.ssd_health_label.setText("<b>SSD-Gesundheit:</b> SMART-Daten nicht verfügbar")

    def _ssd_health_ready(self, d):
        if not d.get("available"): return self._ssd_health_unavailable()
        status = "OK" if d.get("passed") is not False else "WARNUNG"
        parts=[f"<b>SSD-Gesundheit:</b> {status}"]
        if d.get("health") is not None: parts.append(f"{d['health']:.0f} %")
        if d.get("temp") is not None: parts.append(f"{d['temp']} °C")
        if d.get("hours") is not None: parts.append(f"{d['hours']} h")
        if d.get("cycles") is not None: parts.append(f"{d['cycles']} Einschaltvorgänge")
        if d.get("tb") is not None: parts.append(f"{d['tb']:.1f} TB geschrieben")
        self.ssd_health_label.setText(" · ".join(parts))

    def _confirm_factory_reset(self):
        answer = QtWidgets.QMessageBox.question(
            self,
            "Werkseinstellungen wiederherstellen",
            "DAB-Anwendungseinstellungen wirklich auf Werkseinstellungen zurücksetzen?\n\nLAN- und WLAN-Konfiguration bleiben erhalten.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if answer != QtWidgets.QMessageBox.Yes:
            return
        # Only application-owned QSettings are reset. NetworkManager profiles
        # remain untouched so LAN/WLAN connectivity is preserved.
        self._settings.clear()
        self._settings.sync()
        # config/app.yaml ships with demo_data: false, so factory state is
        # live MQTT mode rather than generated demo data.
        default_demo = False
        self.config["app"]["demo_data"] = default_demo
        self._show_data_mode(default_demo)
        self.data_mode_changed.emit(default_demo)
        if hasattr(self, "fw_repository"):
            from src.ui.firmware_window import DEFAULT_REPOSITORY
            self.fw_repository.setText(DEFAULT_REPOSITORY)
        QtWidgets.QMessageBox.information(
            self,
            "Werkseinstellungen",
            "DAB-Anwendungseinstellungen wurden zurückgesetzt.\nLAN und WLAN wurden nicht verändert.\nDatenquelle: Live / MQTT.",
        )

    def _mqtt_page(self):
        root = QtWidgets.QWidget(); grid = QtWidgets.QGridLayout(root); grid.setContentsMargins(8, 7, 8, 7); grid.setHorizontalSpacing(8); grid.setVerticalSpacing(5)
        left_frame = QtWidgets.QFrame(); left_frame.setObjectName("section"); left = QtWidgets.QVBoxLayout(left_frame); left.setContentsMargins(8, 7, 8, 8); left.setSpacing(2)
        left_title = QtWidgets.QLabel("Topics"); left_title.setStyleSheet("font-size:18px;font-weight:bold"); left.addWidget(left_title)
        self.topics = QtWidgets.QTreeWidget(); self.topics.setHeaderHidden(True); self.topics.setItemsExpandable(False); self.topics.setExpandsOnDoubleClick(False)
        self.topics.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn); self.topics.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.topics.itemClicked.connect(self._topic_clicked); self.topics.itemSelectionChanged.connect(self._topic_selected); left.addWidget(self.topics, 1)
        toolbar = QtWidgets.QHBoxLayout(); toolbar.setSpacing(5)
        self.filter = QtWidgets.QLineEdit(); self.filter.setPlaceholderText("Topic filtern …"); self.filter.textChanged.connect(self._rebuild_topics); self.filter.returnPressed.connect(self._hide_touch_keyboard); self.filter.installEventFilter(self)
        clear = QtWidgets.QPushButton("Liste leeren"); clear.setToolTip("Aktuelle Explorer-Liste leeren; neue MQTT-Nachrichten werden danach wieder angezeigt"); clear.clicked.connect(self._clear_mqtt_explorer)
        self.filter.setMinimumWidth(230); clear.setMinimumWidth(135); toolbar.addWidget(self.filter, 1); toolbar.addWidget(clear)
        right_frame = QtWidgets.QFrame(); right_frame.setObjectName("section"); right = QtWidgets.QVBoxLayout(right_frame); right.setContentsMargins(12, 7, 12, 9); right.setSpacing(5)
        right_title = QtWidgets.QLabel("Nachricht"); right_title.setStyleSheet("font-size:18px;font-weight:bold"); right.addWidget(right_title)
        topic_label = QtWidgets.QLabel("Topic"); topic_label.setStyleSheet("color:#9edcff"); right.addWidget(topic_label)
        self.mqtt_topic_value = QtWidgets.QLineEdit(); self.mqtt_topic_value.setReadOnly(True); self.mqtt_topic_value.setFocusPolicy(QtCore.Qt.NoFocus); right.addWidget(self.mqtt_topic_value)
        payload_label = QtWidgets.QLabel("Payload"); payload_label.setStyleSheet("color:#9edcff"); right.addWidget(payload_label)
        self.mqtt_payload_value = QtWidgets.QLineEdit(); self.mqtt_payload_value.setReadOnly(True); self.mqtt_payload_value.setFocusPolicy(QtCore.Qt.NoFocus); self.mqtt_payload_value.setMinimumHeight(42); right.addWidget(self.mqtt_payload_value)
        meta = QtWidgets.QHBoxLayout(); meta.setSpacing(12); self.mqtt_qos_value = QtWidgets.QLabel("QoS: —"); self.mqtt_retain_value = QtWidgets.QLabel("Retained: —"); self.mqtt_time_value = QtWidgets.QLabel("—")
        meta.addWidget(self.mqtt_qos_value); meta.addWidget(self.mqtt_retain_value); meta.addStretch(1); meta.addWidget(self.mqtt_time_value); right.addLayout(meta)
        raw_label = QtWidgets.QLabel("Rohansicht"); raw_label.setStyleSheet("color:#9edcff"); right.addWidget(raw_label)
        self.detail = QtWidgets.QPlainTextEdit(); self.detail.setReadOnly(True); self.detail.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn); self.detail.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded); right.addWidget(self.detail, 1)
        grid.addWidget(left_frame, 0, 0, 2, 1); grid.addLayout(toolbar, 0, 1); grid.addWidget(right_frame, 1, 1)
        grid.setColumnStretch(0, 1); grid.setColumnStretch(1, 1); grid.setRowStretch(0, 0); grid.setRowStretch(1, 1)
        return root

    def _clear_mqtt_explorer(self):
        self.explorer.clear(); self.topics.clear(); self.detail.clear()
        if hasattr(self, "mqtt_topic_value"):
            self.mqtt_topic_value.clear(); self.mqtt_payload_value.clear(); self.mqtt_qos_value.setText("QoS: —"); self.mqtt_retain_value.setText("Retained: —"); self.mqtt_time_value.setText("—")

    def _refresh_selected_topic(self):
        items = self.topics.selectedItems()
        if not items: return
        topic = items[0].data(0, QtCore.Qt.UserRole)
        if topic not in self.explorer: return
        message = self.explorer[topic]; self.mqtt_topic_value.setText(message.topic); self.mqtt_payload_value.setText(message.payload); self.mqtt_qos_value.setText(f"QoS: {message.qos}"); self.mqtt_retain_value.setText(f"Retained: {'true' if message.retain else 'false'}"); self.mqtt_time_value.setText(time.strftime("%H:%M:%S", time.localtime(message.received_at)))
        self.detail.setPlainText(json.dumps(message.parsed, indent=2, ensure_ascii=False) if message.parsed is not None else message.payload)

    def _refresh(self):
        for sid, card in self.cards.items(): card.set_value(self.model.get(sid))
        for sid, curve in self.curves.items():
            pts = self.samples[sid]; curve.setData([x for x, _ in pts], [y for _, y in pts])
        connected = bool(self.mqtt and self.mqtt.connected)
        if connected:
            host = getattr(self, "_broker_host", "")
            if not host: host = str(broker_status()["host"]); self._broker_host = host
            self.status.setText(f"MQTT: verbunden {host}   {time.strftime('%H:%M:%S')}")
        else: self.status.setText(f"MQTT: nicht verbunden   {time.strftime('%H:%M:%S')}")

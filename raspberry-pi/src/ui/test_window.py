from __future__ import annotations

from PyQt5 import QtWidgets

from src.ui.firmware_window import FirmwareMainWindow


class TestMainWindow(FirmwareMainWindow):
    """Incremental test UI additions kept isolated from the stable window."""

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

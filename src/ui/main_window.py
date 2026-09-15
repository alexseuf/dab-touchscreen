from __future__ import annotations
import ctypes, html, json, os, platform, shutil, socket, subprocess, time
from collections import deque
from PyQt5 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg
from src.network.service import device_status, wifi_scan, wifi_status, connect_wifi, disconnect_wifi

SIGNAL_GROUPS={
 'Netz':['grid_voltage_l1','grid_voltage_l2','grid_voltage_l3','grid_current_l1','grid_current_l2','grid_current_l3','grid_frequency','input_power'],
 'Leistungspfad':['dc_link_voltage','output_voltage','output_current','output_power'],
 'Temperaturen':['temp_pfc','temp_dab_primary','temp_dab_secondary','temp_inductor','temp_transformer']}

def eye_icon(slashed=False):
    pixmap=QtGui.QPixmap(32,24);pixmap.fill(QtCore.Qt.transparent)
    painter=QtGui.QPainter(pixmap);painter.setRenderHint(QtGui.QPainter.Antialiasing)
    pen=QtGui.QPen(QtGui.QColor('#ffffff'),2);painter.setPen(pen);painter.drawEllipse(3,5,26,14);painter.setBrush(QtGui.QColor('#ffffff'));painter.drawEllipse(13,9,6,6)
    if slashed:painter.drawLine(4,3,28,21)
    painter.end();return QtGui.QIcon(pixmap)

class WorkerSignals(QtCore.QObject):
    result=QtCore.pyqtSignal(object);error=QtCore.pyqtSignal(str)

class Worker(QtCore.QRunnable):
    def __init__(self,fn,*args):super().__init__();self.fn=fn;self.args=args;self.signals=WorkerSignals()
    @QtCore.pyqtSlot()
    def run(self):
        try:self.signals.result.emit(self.fn(*self.args))
        except Exception as exc:self.signals.error.emit(str(exc))

class TouchKeyboardDialog(QtWidgets.QDialog):
    def __init__(self,value='',parent=None):
        super().__init__(parent);self.setWindowTitle('WLAN-Passwort eingeben');self.shift=False;self.letter_buttons=[]
        self.setModal(True);self.resize(960,390);layout=QtWidgets.QVBoxLayout(self)
        self.entry=QtWidgets.QLineEdit(value);self.entry.setEchoMode(QtWidgets.QLineEdit.Password);self.entry.setMinimumHeight(48);layout.addWidget(self.entry)
        keys=QtWidgets.QGridLayout();layout.addLayout(keys)
        for row,text in enumerate(['1234567890','qwertzuiop','asdfghjkl','yxcvbnm','-_.!@#$%&*+?/']):
            offset=0 if row<2 else row-1
            for column,char in enumerate(text):
                button=QtWidgets.QPushButton(char);button.setMinimumSize(54,46);button.clicked.connect(lambda _,c=char:self._type(c));keys.addWidget(button,row,column+offset)
                if char.isalpha():self.letter_buttons.append(button)
        actions=QtWidgets.QHBoxLayout();layout.addLayout(actions)
        shift=QtWidgets.QPushButton('⇧ Groß/Klein');shift.clicked.connect(self._toggle_shift);actions.addWidget(shift)
        back=QtWidgets.QPushButton('⌫ Löschen');back.clicked.connect(self.entry.backspace);actions.addWidget(back)
        clear=QtWidgets.QPushButton('Leeren');clear.clicked.connect(self.entry.clear);actions.addWidget(clear)
        cancel=QtWidgets.QPushButton('Abbrechen');cancel.clicked.connect(self.reject);actions.addWidget(cancel)
        accept=QtWidgets.QPushButton('Übernehmen');accept.clicked.connect(self.accept);actions.addWidget(accept)
    def _type(self,char):self.entry.insert(char.upper() if self.shift and char.isalpha() else char)
    def _toggle_shift(self):
        self.shift=not self.shift
        for button in self.letter_buttons:button.setText(button.text().upper() if self.shift else button.text().lower())

class ValueCard(QtWidgets.QFrame):
    def __init__(self,title):
        super().__init__();self.setObjectName('card')
        box=QtWidgets.QVBoxLayout(self);box.setContentsMargins(6,2,6,2);box.setSpacing(0);self.title=QtWidgets.QLabel(title);self.title.setObjectName('cardTitle');self.value=QtWidgets.QLabel('—');self.value.setObjectName('value')
        box.addWidget(self.title);box.addWidget(self.value)
    def set_value(self,item):
        decimals={'W': 0, 'V': 1, '°C': 1, 'A': 2}.get(item.unit, 2)
        self.value.setText('—' if item.value is None else f'{item.value:.{decimals}f} {item.unit}')
        self.setProperty('quality',item.quality);self.style().unpolish(self);self.style().polish(self)

class CompactValue(QtWidgets.QWidget):
    def __init__(self,title,vertical=False):
        super().__init__();self.vertical=vertical
        box=(QtWidgets.QVBoxLayout if vertical else QtWidgets.QHBoxLayout)(self);box.setContentsMargins(2,0,2,0);box.setSpacing(4)
        self.title=QtWidgets.QLabel(title);self.title.setObjectName('compactTitle')
        self.value=QtWidgets.QLabel('—');self.value.setObjectName('compactValue');self.value.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        box.addWidget(self.title);box.addWidget(self.value,1)
    def set_value(self,item):
        decimals={'W':0,'V':1,'°C':1,'A':2}.get(item.unit,2)
        self.value.setText('—' if item.value is None else f'{item.value:.{decimals}f} {item.unit}')
        self.setProperty('quality',item.quality);self.style().unpolish(self);self.style().polish(self)

class MainWindow(QtWidgets.QMainWindow):
    model_event=QtCore.pyqtSignal(object);explorer_event=QtCore.pyqtSignal(object)
    def __init__(self,model,config,history=None):
        super().__init__();self.model=model;self.config=config;self.history=history;self.mqtt=None;self.threadpool=QtCore.QThreadPool.globalInstance();self._keyboard_process=None;self._wifi_status_running=False
        self.setWindowTitle(config['app'].get('title','DAB Touchscreen'));self.resize(800,480);self.setMinimumSize(800,480);self._main_return_index=0;self._cpu_sample=None
        if os.environ.get('XDG_SESSION_TYPE')=='wayland' or os.environ.get('WAYLAND_DISPLAY'):
            self.setWindowFlag(QtCore.Qt.FramelessWindowHint,True);QtCore.QTimer.singleShot(0,self.showFullScreen)
        self.samples={k:deque(maxlen=3600) for k in model.definitions};self.cards={};self.explorer={}
        self.nav_stack=QtWidgets.QStackedWidget();self.setCentralWidget(self.nav_stack)
        self.tabs=QtWidgets.QTabWidget();self.tabs.addTab(self._overview(),'Übersicht');self.tabs.addTab(self._charts(),'Verläufe');self.tabs.addTab(self._mqtt_page(),'MQTT Explorer');self.tabs.addTab(QtWidgets.QWidget(),'⚙ Einstellungen');self.tabs.currentChanged.connect(self._main_tab_changed);self.nav_stack.addWidget(self.tabs)
        self.settings_tabs=QtWidgets.QTabWidget();self.settings_tabs.addTab(self._lan(),'Netzwerk (LAN)');self.settings_tabs.addTab(self._wifi(),'WLAN');self.settings_tabs.addTab(self._system_page(),'System');self.settings_tabs.addTab(QtWidgets.QWidget(),'← Zurück');self.settings_tabs.currentChanged.connect(self._settings_tab_changed);self.nav_stack.addWidget(self.settings_tabs)
        self.status=QtWidgets.QLabel('MQTT: wartet | Daten: Demo');self.statusBar().addPermanentWidget(self.status)
        self.model_event.connect(self._on_value);self.explorer_event.connect(self._on_explorer);model.subscribe(self.model_event.emit)
        self.timer=QtCore.QTimer(self);self.timer.timeout.connect(self._refresh);self.timer.start(1000)
        self.setStyleSheet('''QWidget{background:#0b141b;color:#ffffff;font-family:"DejaVu Sans";font-size:14px}QTabWidget::pane{border:1px solid #355364}QTabBar::tab{min-width:155px;min-height:44px;background:#10293a;padding:2px;border:0}QTabBar::tab:selected{background:#1687e8}QFrame#card,QFrame#section{background:#101f29;border:1px solid #355364;border-radius:8px}QFrame#card[quality="stale"],QFrame#card[quality="missing"],CompactValue[quality="stale"],CompactValue[quality="missing"]{color:#89939e}QFrame#card[quality="invalid"],CompactValue[quality="invalid"]{color:#ff7b72}QLabel#cardTitle{font-size:12px;color:#9edcff}QLabel#value{font-size:18px;font-weight:bold}QLabel#compactTitle{font-size:12px;color:#9edcff}QLabel#compactValue{font-size:14px;font-weight:bold}QPushButton,QLineEdit,QComboBox{min-height:42px;padding:3px;background:#183040;color:#ffffff;border:1px solid #36596c;border-radius:5px}QPushButton:pressed{background:#1687e8}QPlainTextEdit,QListWidget,QTreeWidget{background:#101f29;border:1px solid #355364;color:#ffffff;font-family:"DejaVu Sans Mono"}QProgressBar{min-height:22px;background:#183040;border:1px solid #36596c}QProgressBar::chunk{background:#34d26b}QStatusBar{background:#0b141b;color:#ffffff;font-size:12px}''')
        self.wifi_timer=QtCore.QTimer(self);self.wifi_timer.timeout.connect(self._refresh_wifi_status);self.wifi_timer.start(5000)
        self.system_timer=QtCore.QTimer(self);self.system_timer.timeout.connect(self._refresh_system);self.system_timer.start(2000)

    def _main_tab_changed(self,index):
        if index==3:
            self._main_return_index=max(0,self.tabs.currentIndex()-1);self.settings_tabs.setCurrentIndex(0);self.nav_stack.setCurrentWidget(self.settings_tabs);self._refresh_network();self._refresh_system()
    def _settings_tab_changed(self,index):
        if index==3:
            self.tabs.blockSignals(True);self.tabs.setCurrentIndex(self._main_return_index);self.tabs.blockSignals(False);self.nav_stack.setCurrentWidget(self.tabs)

    def _overview(self):
        root=QtWidgets.QWidget();outer=QtWidgets.QVBoxLayout(root);outer.setContentsMargins(8,4,8,4);outer.setSpacing(5)
        flow=QtWidgets.QLabel('3~ NETZ   →   PFC   →   ZWISCHENKREIS   →   DAB   →   DC-AUSGANG');flow.setAlignment(QtCore.Qt.AlignCenter);flow.setFixedHeight(25);flow.setStyleSheet('font-size:16px;font-weight:bold;color:#ffffff');outer.addWidget(flow)
        body=QtWidgets.QHBoxLayout();body.setSpacing(7);outer.addLayout(body,3)
        grid_box=QtWidgets.QFrame();grid_box.setObjectName('section');grid_lay=QtWidgets.QVBoxLayout(grid_box);grid_lay.setContentsMargins(8,5,8,5);grid_lay.setSpacing(1)
        title=QtWidgets.QLabel('Netz 3~');title.setStyleSheet('font-size:17px;font-weight:bold');grid_lay.addWidget(title)
        for sid in ['grid_frequency','grid_voltage_l1','grid_voltage_l2','grid_voltage_l3','grid_current_l1','grid_current_l2','grid_current_l3','grid_power_l1','grid_power_l2','grid_power_l3','input_power']:
            metric=CompactValue(self.model.definitions[sid].get('label',sid));self.cards[sid]=metric;grid_lay.addWidget(metric)
        body.addWidget(grid_box,5)
        path_box=QtWidgets.QFrame();path_box.setObjectName('section');path=QtWidgets.QVBoxLayout(path_box);path.setContentsMargins(8,5,8,5);path.setSpacing(5)
        blocks=QtWidgets.QHBoxLayout();blocks.setSpacing(5)
        pfc=QtWidgets.QLabel('PFC\n3~ → DC');pfc.setAlignment(QtCore.Qt.AlignCenter);pfc.setStyleSheet('font-size:17px;font-weight:bold;border:2px solid #59c9ff;border-radius:7px;background:#15384b;padding:8px')
        dc=QtWidgets.QLabel('║ Cdc ║');dc.setAlignment(QtCore.Qt.AlignCenter);dc.setStyleSheet('font-size:17px;color:#ffd94a')
        dab=QtWidgets.QLabel('DAB\nDC ↔ DC');dab.setAlignment(QtCore.Qt.AlignCenter);dab.setStyleSheet('font-size:17px;font-weight:bold;border:2px solid #ff83bd;border-radius:7px;background:#3a2334;padding:8px')
        blocks.addWidget(pfc);blocks.addWidget(QtWidgets.QLabel('→'));blocks.addWidget(dc);blocks.addWidget(QtWidgets.QLabel('→'));blocks.addWidget(dab);path.addLayout(blocks)
        for sid in ['dc_link_voltage']:
            metric=CompactValue(self.model.definitions[sid].get('label',sid),True);self.cards[sid]=metric;path.addWidget(metric)
        body.addWidget(path_box,7)
        out_box=QtWidgets.QFrame();out_box.setObjectName('section');out=QtWidgets.QVBoxLayout(out_box);out.setContentsMargins(8,5,8,5);out.setSpacing(4)
        title=QtWidgets.QLabel('DC-Ausgang');title.setStyleSheet('font-size:17px;font-weight:bold');out.addWidget(title)
        for sid in ['output_voltage','output_current','output_power']:
            metric=CompactValue(self.model.definitions[sid].get('label',sid),True);self.cards[sid]=metric;out.addWidget(metric)
        out.addStretch(1);body.addWidget(out_box,5)
        temp_box=QtWidgets.QFrame();temp_box.setObjectName('section');temps=QtWidgets.QGridLayout(temp_box);temps.setContentsMargins(8,4,8,4);temps.setHorizontalSpacing(8);temps.setVerticalSpacing(1)
        temp_title=QtWidgets.QLabel('Temperaturen');temp_title.setStyleSheet('font-size:15px;font-weight:bold;color:#55d6ff');temps.addWidget(temp_title,0,0,1,5)
        for col,sid in enumerate(['temp_pfc','temp_inductor','temp_dab_primary','temp_transformer','temp_dab_secondary']):
            metric=CompactValue(self.model.definitions[sid].get('label',sid),True);self.cards[sid]=metric;temps.addWidget(metric,1,col)
        outer.addWidget(temp_box,1);return root

    def _charts(self):
        root=QtWidgets.QWidget();lay=QtWidgets.QVBoxLayout(root);lay.setContentsMargins(5,4,5,4);lay.setSpacing(3);bar=QtWidgets.QHBoxLayout();bar.setSpacing(4)
        self.chart_back=QtWidgets.QPushButton('← Zurück');self.chart_back.setFixedSize(92,38);self.chart_back.clicked.connect(self._restore_all_plots);self.chart_back.hide();bar.addWidget(self.chart_back)
        for seconds,label in [(60,'1 min'),(600,'10 min'),(3600,'1 h'),(21600,'6 h'),(86400,'24 h')]:
            b=QtWidgets.QPushButton(label);b.clicked.connect(lambda _,s=seconds:self._set_window(s));bar.addWidget(b)
        b=QtWidgets.QPushButton('Reset');b.clicked.connect(self._reset_plots);bar.addWidget(b);lay.addLayout(bar)
        groups={
            'voltage':('Spannung','V',['grid_voltage_l1','grid_voltage_l2','grid_voltage_l3','dc_link_voltage','output_voltage']),
            'current':('Strom','A',['grid_current_l1','grid_current_l2','grid_current_l3','output_current']),
            'power':('Leistung','W',['grid_power_l1','grid_power_l2','grid_power_l3','input_power','output_power']),
            'temperature':('Temperatur','°C',['temp_pfc','temp_dab_primary','temp_dab_secondary','temp_inductor','temp_transformer']),
        }
        colors=['#00b4d8','#90e0ef','#9b5de5','#ffb703','#e63946'];self.plots={};self.curves={}
        first=None
        for index,(group,(label,unit,signals)) in enumerate(groups.items()):
            plot=pg.PlotWidget(axisItems={'bottom':pg.DateAxisItem(orientation='bottom')});plot.setMinimumHeight(82)
            plot.showGrid(x=True,y=True,alpha=.25);plot.setLabel('left',label,units=unit);plot.addLegend(offset=(5,2),colCount=3)
            if first is None:first=plot
            else:plot.setXLink(first)
            if index<len(groups)-1:plot.getAxis('bottom').setStyle(showValues=False)
            else:plot.setLabel('bottom','Zeit')
            plot.scene().sigMouseClicked.connect(lambda event,g=group:self._focus_plot(g,event))
            self.plots[group]=plot;lay.addWidget(plot,1)
            for curve_index,sid in enumerate(signals):
                self.curves[sid]=plot.plot(name=self.model.definitions[sid]['label'],pen=pg.mkPen(colors[curve_index],width=2))
        return root
    def _set_window(self,seconds): self.plots['voltage'].setXRange(time.time()-seconds,time.time(),padding=0)
    def _reset_plots(self):
        for plot in self.plots.values():plot.enableAutoRange()
    def _focus_plot(self,group,event=None):
        if event is not None and event.button()!=QtCore.Qt.LeftButton:return
        for name,plot in self.plots.items():plot.setVisible(name==group)
        selected=self.plots[group];selected.getAxis('bottom').setStyle(showValues=True);selected.setLabel('bottom','Zeit')
        self.chart_back.show()
    def _restore_all_plots(self):
        for index,(name,plot) in enumerate(self.plots.items()):
            plot.show();plot.getAxis('bottom').setStyle(showValues=index==len(self.plots)-1)
            plot.setLabel('bottom','Zeit' if index==len(self.plots)-1 else '')
        self.chart_back.hide()

    def _lan(self):
        root=QtWidgets.QWidget();lay=QtWidgets.QVBoxLayout(root);self.lan_text=QtWidgets.QPlainTextEdit();self.lan_text.setReadOnly(True);lay.addWidget(QtWidgets.QLabel('Ethernet- und Brokerstatus'));lay.addWidget(self.lan_text);b=QtWidgets.QPushButton('Status aktualisieren');b.clicked.connect(self._refresh_network);lay.addWidget(b);QtCore.QTimer.singleShot(0,self._refresh_network);return root

    def _system_page(self):
        root=QtWidgets.QWidget();outer=QtWidgets.QVBoxLayout(root);title=QtWidgets.QLabel('Raspberry-Pi-Systemstatus');title.setStyleSheet('font-size:21px;font-weight:bold');outer.addWidget(title)
        grid=QtWidgets.QGridLayout();outer.addLayout(grid);self.system_labels={};self.system_bars={}
        for row,(key,label) in enumerate([('cpu','CPU-Auslastung'),('memory','Arbeitsspeicher'),('temperature','CPU-Temperatur'),('disk','SSD-Belegung')]):
            grid.addWidget(QtWidgets.QLabel(label),row,0);bar=QtWidgets.QProgressBar();bar.setRange(0,100);bar.setFormat('%p %');grid.addWidget(bar,row,1);value=QtWidgets.QLabel('—');value.setMinimumWidth(155);grid.addWidget(value,row,2);self.system_bars[key]=bar;self.system_labels[key]=value
        self.system_details=QtWidgets.QLabel('Systemdaten werden geladen …');self.system_details.setWordWrap(True);self.system_details.setAlignment(QtCore.Qt.AlignTop);outer.addWidget(self.system_details,1)
        actions=QtWidgets.QHBoxLayout();restart=QtWidgets.QPushButton('↻ Raspberry neu starten');restart.clicked.connect(lambda:self._confirm_system_action('reboot'));shutdown=QtWidgets.QPushButton('⏻ Raspberry ausschalten');shutdown.setStyleSheet('background:#8b2f34');shutdown.clicked.connect(lambda:self._confirm_system_action('poweroff'));actions.addWidget(restart);actions.addWidget(shutdown);outer.addLayout(actions);QtCore.QTimer.singleShot(0,self._refresh_system);return root

    def _read_cpu_percent(self):
        values=[int(v) for v in open('/proc/stat',encoding='ascii').readline().split()[1:]];idle=values[3]+values[4];total=sum(values);current=(idle,total)
        if not self._cpu_sample:self._cpu_sample=current;return 0
        old_idle,old_total=self._cpu_sample;self._cpu_sample=current;delta=max(1,total-old_total);return max(0,min(100,100*(1-(idle-old_idle)/delta)))
    def _refresh_system(self):
        try:
            cpu=self._read_cpu_percent();mem={line.split(':',1)[0]:int(line.split()[1]) for line in open('/proc/meminfo',encoding='ascii') if ':' in line};mem_total=mem['MemTotal'];mem_used=mem_total-mem.get('MemAvailable',0);memory=100*mem_used/mem_total
            disk=shutil.disk_usage('/');disk_percent=100*disk.used/disk.total
            try:temperature=float(open('/sys/class/thermal/thermal_zone0/temp',encoding='ascii').read().strip())/1000
            except (OSError,ValueError):temperature=0
            for key,value,text in [('cpu',cpu,f'{cpu:.1f} %'),('memory',memory,f'{mem_used/1048576:.1f} / {mem_total/1048576:.1f} GiB'),('temperature',min(100,temperature),f'{temperature:.1f} °C'),('disk',disk_percent,f'{disk.used/1073741824:.1f} / {disk.total/1073741824:.1f} GiB')]:self.system_bars[key].setValue(round(value));self.system_labels[key].setText(text)
            uptime=int(float(open('/proc/uptime',encoding='ascii').read().split()[0]));days,rem=divmod(uptime,86400);hours,rem=divmod(rem,3600);minutes=rem//60
            ips=subprocess.run(['ip','-4','-brief','address'],text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,check=False,timeout=2).stdout.strip()
            self.system_details.setText(f'<b>Hostname:</b> {html.escape(socket.gethostname())}<br><b>System:</b> {html.escape(platform.platform())}<br><b>Laufzeit:</b> {days} Tage, {hours} Std., {minutes} Min.<br><b>CPU-Kerne:</b> {os.cpu_count()}<br><b>Netzwerk:</b><pre>{html.escape(ips or "—")}</pre>')
        except Exception as exc:self.system_details.setText('Systemdaten konnten nicht gelesen werden: '+html.escape(str(exc)))
    def _confirm_system_action(self,action):
        label='neu starten' if action=='reboot' else 'ausschalten';answer=QtWidgets.QMessageBox.warning(self,'Systemaktion bestätigen',f'Raspberry Pi wirklich {label}?',QtWidgets.QMessageBox.Yes|QtWidgets.QMessageBox.No,QtWidgets.QMessageBox.No)
        if answer!=QtWidgets.QMessageBox.Yes:return
        answer=QtWidgets.QMessageBox.question(self,'Letzte Bestätigung',f'Jetzt wirklich {label}?',QtWidgets.QMessageBox.Yes|QtWidgets.QMessageBox.No,QtWidgets.QMessageBox.No)
        if answer==QtWidgets.QMessageBox.Yes:subprocess.Popen(['systemctl',action],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

    def _wifi(self):
        root=QtWidgets.QWidget();lay=QtWidgets.QGridLayout(root);self.wifi_list=QtWidgets.QListWidget();self.wifi_list.itemSelectionChanged.connect(self._wifi_selected)
        self.wifi_ssid=QtWidgets.QLineEdit();self.wifi_ssid.setReadOnly(True);self.wifi_password=QtWidgets.QLineEdit();self.wifi_password.setEchoMode(QtWidgets.QLineEdit.Password);self.wifi_password.installEventFilter(self)
        password_row=QtWidgets.QWidget();password_layout=QtWidgets.QHBoxLayout(password_row);password_layout.setContentsMargins(0,0,0,0);password_layout.setSpacing(4);password_layout.addWidget(self.wifi_password)
        self.wifi_reveal=QtWidgets.QPushButton();self.wifi_reveal.setIcon(eye_icon());self.wifi_reveal.setIconSize(QtCore.QSize(32,24));self.wifi_reveal.setCheckable(True);self.wifi_reveal.setFixedWidth(54);self.wifi_reveal.setToolTip('Passwort anzeigen/verbergen');self.wifi_reveal.toggled.connect(self._toggle_password_visibility);password_layout.addWidget(self.wifi_reveal)
        self.wifi_result=QtWidgets.QLabel('WLAN-Status wird geladen …');self.wifi_result.setWordWrap(True);self.wifi_signal=QtWidgets.QProgressBar();self.wifi_signal.setRange(0,100);self.wifi_signal.setTextVisible(False)
        self.wifi_scan_button=QtWidgets.QPushButton('↻ WLAN scannen');self.wifi_scan_button.clicked.connect(self._scan_wifi);self.keyboard_button=QtWidgets.QPushButton('⌨ Tastatur');self.keyboard_button.clicked.connect(self._show_touch_keyboard)
        connect=QtWidgets.QPushButton('Verbinden');connect.clicked.connect(self._connect_wifi);disconnect=QtWidgets.QPushButton('Trennen');disconnect.clicked.connect(self._disconnect_wifi)
        lay.setContentsMargins(6,4,6,4);lay.setVerticalSpacing(3)
        lay.addWidget(QtWidgets.QLabel('Verfügbare WLAN-Netze'),0,0);lay.addWidget(self.wifi_list,1,0,6,1);lay.addWidget(self.wifi_scan_button,7,0,2,1)
        lay.addWidget(QtWidgets.QLabel('SSID'),0,1);lay.addWidget(self.wifi_ssid,1,1);lay.addWidget(QtWidgets.QLabel('Passwort'),2,1);lay.addWidget(password_row,3,1);lay.addWidget(self.keyboard_button,4,1);lay.addWidget(connect,5,1);lay.addWidget(disconnect,6,1);lay.addWidget(self.wifi_result,7,1);lay.addWidget(self.wifi_signal,8,1)
        lay.setColumnStretch(0,3);lay.setColumnStretch(1,2);QtCore.QTimer.singleShot(500,self._refresh_wifi_status);QtCore.QTimer.singleShot(800,self._scan_wifi);return root
    def eventFilter(self,obj,event):
        if obj is getattr(self,'wifi_password',None) and event.type()==QtCore.QEvent.MouseButtonPress:QtCore.QTimer.singleShot(0,self._show_touch_keyboard)
        return super().eventFilter(obj,event)
    def _run_worker(self,fn,args,done):
        worker=Worker(fn,*args);worker.signals.result.connect(done);worker.signals.error.connect(lambda error:self.wifi_result.setText('Fehler: '+error));self.threadpool.start(worker)
    def _scan_wifi(self):
        self.wifi_result.setText('WLAN-Suche läuft …');self.wifi_scan_button.setEnabled(False);self._run_worker(wifi_scan,(self.config['network']['wifi_interface'],),self._scan_finished)
    def _scan_finished(self,networks):
        self.wifi_list.clear();self.wifi_list.addItems(networks);self.wifi_scan_button.setEnabled(True);self.wifi_result.setText(f'{len(networks)} WLAN-Netz(e) gefunden' if networks else 'Keine WLAN-Netze gefunden');self._refresh_wifi_status()
    def _wifi_selected(self):
        item=self.wifi_list.currentItem()
        if item:self.wifi_ssid.setText(item.text().split(':',1)[0])
    def _show_touch_keyboard(self):
        self.wifi_password.setFocus(QtCore.Qt.MouseFocusReason)
        if os.environ.get('XDG_SESSION_TYPE')=='wayland' or os.environ.get('WAYLAND_DISPLAY'):
            subprocess.run(['gdbus','call','--session','--dest','sm.puri.OSK0','--object-path','/sm/puri/OSK0','--method','sm.puri.OSK0.SetVisible','true'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False,timeout=2)
            return
        if self._keyboard_process and self._keyboard_process.poll() is None:return
        try:
            keyboard=shutil.which('matchbox-keyboard')
            if not keyboard:
                self.wifi_result.setText('Matchbox-Tastatur ist noch nicht installiert')
                return
            log=open('/tmp/dab-keyboard.log','ab',buffering=0)
            self._keyboard_process=subprocess.Popen(
                [keyboard,'--orientation','landscape','--lang','de','--fontptsize','18','--rowspacing','2','--colspacing','2'],
                stdout=log,stderr=subprocess.STDOUT)
            log.close()
            QtCore.QTimer.singleShot(400,self._raise_touch_keyboard);QtCore.QTimer.singleShot(1000,self._raise_touch_keyboard)
        except OSError as exc:self.wifi_result.setText('Bildschirmtastatur konnte nicht gestartet werden: '+str(exc))
    def _raise_touch_keyboard(self):
        try:
            x11=ctypes.CDLL('libX11.so.6');x11.XOpenDisplay.restype=ctypes.c_void_p;display=x11.XOpenDisplay(None)
            if not display:return
            root=ctypes.c_ulong(x11.XDefaultRootWindow(display));found=[]
            def walk(window):
                name=ctypes.c_char_p()
                if x11.XFetchName(display,window,ctypes.byref(name)) and name.value:
                    title=name.value.decode(errors='ignore').lower()
                    if 'matchbox' in title or 'keyboard' in title:found.append(window)
                root_ret=ctypes.c_ulong();parent=ctypes.c_ulong();children=ctypes.POINTER(ctypes.c_ulong)();count=ctypes.c_uint()
                if x11.XQueryTree(display,window,ctypes.byref(root_ret),ctypes.byref(parent),ctypes.byref(children),ctypes.byref(count)):
                    for index in range(count.value):walk(ctypes.c_ulong(children[index]))
                    if children:x11.XFree(children)
            walk(root)
            for window in found:x11.XMapRaised(display,window);x11.XRaiseWindow(display,window)
            x11.XFlush(display);x11.XCloseDisplay(display)
        except Exception as exc:self.wifi_result.setText('Tastaturfenster konnte nicht angehoben werden: '+str(exc))
    def _toggle_password_visibility(self,visible):
        self.wifi_password.setEchoMode(QtWidgets.QLineEdit.Normal if visible else QtWidgets.QLineEdit.Password)
        self.wifi_reveal.setIcon(eye_icon(slashed=visible))
    def _hide_touch_keyboard(self):
        if os.environ.get('XDG_SESSION_TYPE')=='wayland' or os.environ.get('WAYLAND_DISPLAY'):
            subprocess.run(['gdbus','call','--session','--dest','sm.puri.OSK0','--object-path','/sm/puri/OSK0','--method','sm.puri.OSK0.SetVisible','false'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False,timeout=2)
        if self._keyboard_process and self._keyboard_process.poll() is None:self._keyboard_process.terminate()
        self._keyboard_process=None
    def _connect_wifi(self):
        ssid=self.wifi_ssid.text().strip()
        if not ssid:self.wifi_result.setText('Bitte zuerst ein WLAN auswählen');return
        selected=self.wifi_list.currentItem();security=selected.text().upper() if selected else ''
        if ('WPA' in security or 'WEP' in security) and len(self.wifi_password.text())<8:
            self.wifi_result.setText("<span style='color:#e63946;font-size:22px'>●</span> <b>Passwort zu kurz</b><br>WPA/WPA2 benötigt mindestens 8 Zeichen.");return
        self._hide_touch_keyboard()
        self.wifi_result.setText(f'Verbinde mit {ssid} …');self._run_worker(connect_wifi,(ssid,self.wifi_password.text(),self.config['network']['wifi_interface']),self._connection_finished)
    def _disconnect_wifi(self):self.wifi_result.setText('WLAN wird getrennt …');self._run_worker(disconnect_wifi,(self.config['network']['wifi_interface'],),self._connection_finished)
    def _connection_finished(self,p):
        self.wifi_password.clear();self.wifi_result.setText((p.stdout or p.stderr).strip() or ('Aktion erfolgreich' if p.returncode==0 else 'Aktion fehlgeschlagen'));QtCore.QTimer.singleShot(800,self._refresh_wifi_status)
    def _refresh_wifi_status(self):
        if self._wifi_status_running:return
        self._wifi_status_running=True;self._run_worker(wifi_status,(self.config['network']['wifi_interface'],),self._wifi_status_finished)
    def _wifi_status_finished(self,status):
        self._wifi_status_running=False;self.wifi_signal.setValue(status['signal'])
        if status['connected']:
            dbm=f"{status['dbm']} dBm" if status['dbm'] is not None else 'dBm nicht verfügbar';self.wifi_result.setText(f"<span style='color:#34d26b;font-size:24px'>●</span> <b>WLAN verbunden</b><br>SSID: {html.escape(status['ssid'])}<br>Signal: {status['signal']} % · {dbm} · {html.escape(status['bars'])}<br>IPv4: {html.escape(status['ipv4'])} · {html.escape(status['security'])}")
            if not self.wifi_ssid.text():self.wifi_ssid.setText(status['ssid'])
        else:self.wifi_result.setText("<span style='color:#e63946;font-size:24px'>●</span> <b>Nicht mit WLAN verbunden</b>")

    def _mqtt_page(self):
        root=QtWidgets.QWidget();lay=QtWidgets.QHBoxLayout(root);left=QtWidgets.QVBoxLayout();self.filter=QtWidgets.QLineEdit();self.filter.setPlaceholderText('Topic filtern …');self.filter.textChanged.connect(self._rebuild_topics);self.topics=QtWidgets.QTreeWidget();self.topics.setHeaderLabel('Topics');self.topics.setItemsExpandable(False);self.topics.setExpandsOnDoubleClick(False);self.topics.itemClicked.connect(self._topic_clicked);self.topics.itemSelectionChanged.connect(self._topic_selected);left.addWidget(self.filter);left.addWidget(self.topics);self.detail=QtWidgets.QPlainTextEdit();self.detail.setReadOnly(True);lay.addLayout(left,2);lay.addWidget(self.detail,3);return root

    def set_mqtt(self,mqtt): self.mqtt=mqtt
    def _on_value(self,item):
        if item.value is not None:
            now=time.time();self.samples[item.signal_id].append((now,item.value))
            if self.history: self.history.add(item.signal_id,item.value,now)
        if item.signal_id in self.cards:self.cards[item.signal_id].set_value(item)
    def _on_explorer(self,msg):
        is_new=msg.topic not in self.explorer
        self.explorer[msg.topic]=msg
        if is_new:self._rebuild_topics()
        else:self._refresh_selected_topic()
    def _rebuild_topics(self):
        selected=self.filter.text().lower();self.topics.clear()
        for topic in sorted(self.explorer):
            if selected and selected not in topic.lower():continue
            parent=self.topics.invisibleRootItem()
            for part in topic.split('/'):
                found=None
                for i in range(parent.childCount()):
                    if parent.child(i).text(0)==part:found=parent.child(i);break
                if found is None:found=QtWidgets.QTreeWidgetItem([part]);parent.addChild(found)
                parent=found
            parent.setData(0,QtCore.Qt.UserRole,topic)
        self.topics.expandAll()
    def _topic_selected(self):
        self._refresh_selected_topic()
    def _topic_clicked(self,item,column):
        if item.childCount():item.setExpanded(not item.isExpanded())
    def _refresh_selected_topic(self):
        items=self.topics.selectedItems()
        if not items:return
        topic=items[0].data(0,QtCore.Qt.UserRole)
        if topic in self.explorer:
            m=self.explorer[topic];payload=json.dumps(m.parsed,indent=2,ensure_ascii=False) if m.parsed is not None else m.payload
            self.detail.setPlainText(f'Topic: {m.topic}\nQoS: {m.qos}\nRetain: {m.retain}\nZeit: {time.ctime(m.received_at)}\n\n{payload}')
    def _refresh(self):
        for sid,card in self.cards.items():card.set_value(self.model.get(sid))
        for sid,curve in self.curves.items():
            pts=self.samples[sid];curve.setData([x for x,_ in pts],[y for _,y in pts])
        self.status.setText(f'MQTT: {"verbunden" if self.mqtt and self.mqtt.connected else "getrennt"} | {time.strftime("%H:%M:%S")}')
    def _refresh_network(self): self.lan_text.setPlainText('\n'.join(device_status()) or 'Keine Daten')

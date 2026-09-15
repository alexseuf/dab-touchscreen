from __future__ import annotations
import math, random, sys, time
from pathlib import Path
import yaml
from PyQt5 import QtCore, QtGui, QtWidgets
from src.data.model import DataModel
from src.data.history import HistoryStore
from src.mqtt.client import MqttService
from src.ui.main_window import MainWindow

ROOT=Path(__file__).resolve().parents[1]
def load_yaml(name):
    with (ROOT/'config'/name).open(encoding='utf-8') as f:return yaml.safe_load(f) or {}

class DemoPublisher(QtCore.QObject):
    def __init__(self,model):
        super().__init__();self.model=model;self.t=0;self.timer=QtCore.QTimer(self);self.timer.timeout.connect(self.tick);self.timer.start(500)
    def tick(self):
        self.t+=.5;p=5200+800*math.sin(self.t/8);vals={'grid_voltage_l1':230+random.uniform(-1,1),'grid_voltage_l2':231+random.uniform(-1,1),'grid_voltage_l3':229+random.uniform(-1,1),'grid_current_l1':p/3/230,'grid_current_l2':p/3/231,'grid_current_l3':p/3/229,'grid_frequency':50+random.uniform(-.03,.03),'input_power':p,'dc_link_voltage':700+random.uniform(-2,2),'output_voltage':400+random.uniform(-1,1),'output_current':p*.94/400,'output_power':p*.94,'temp_pfc':43+2*math.sin(self.t/20),'temp_dab_primary':46+2*math.sin(self.t/23),'temp_dab_secondary':44+2*math.sin(self.t/19),'temp_inductor':49+2*math.sin(self.t/25),'temp_transformer':47+2*math.sin(self.t/28)}
        for sid,val in vals.items():self.model.update_topic(self.model.definitions[sid]['topic'],str(round(val,3)))

def run(fullscreen=None):
    cfg=load_yaml('app.yaml');defs=load_yaml('topics.yaml')['signals'];model=DataModel(defs,cfg['app']['stale_after_seconds'])
    try:history=HistoryStore()
    except OSError:history=HistoryStore('/tmp/dab-touchscreen-history.sqlite3')
    app=QtWidgets.QApplication(sys.argv);app.setApplicationName('DAB Touchscreen')
    app.setFont(QtGui.QFont('DejaVu Sans',14));window=MainWindow(model,cfg,history)
    mqtt=MqttService(cfg['mqtt']['host'],cfg['mqtt']['port'],model,window.explorer_event.emit);window.set_mqtt(mqtt);mqtt.start()
    demo=DemoPublisher(model) if cfg['app'].get('demo_data',True) else None
    if fullscreen if fullscreen is not None else cfg['app'].get('fullscreen',True):window.showFullScreen()
    else:window.show()
    rc=app.exec_();mqtt.stop();return rc

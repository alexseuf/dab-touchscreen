from __future__ import annotations
import json, threading, time
from dataclasses import dataclass
import paho.mqtt.client as mqtt

@dataclass
class ExplorerMessage:
    topic:str; payload:str; qos:int; retain:bool; received_at:float; parsed:object|None

class MqttService:
    def __init__(self,host,port,model,explorer_callback=None,username=None,password=None):
        self.host,self.port,self.model=host,int(port),model;self.explorer_callback=explorer_callback
        self.connected=False
        if hasattr(mqtt, 'CallbackAPIVersion'):
            self.client=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,client_id='dab-touchscreen')
        else:
            self.client=mqtt.Client(client_id='dab-touchscreen')
        if username:self.client.username_pw_set(username,password or '')
        self.client.on_connect=self._connect;self.client.on_disconnect=self._disconnect;self.client.on_message=self._message
    def _connect(self,client,userdata,flags,reason_code,properties=None):
        self.connected=not bool(reason_code)
        if self.connected: client.subscribe('#',qos=0)
    def _disconnect(self,*args): self.connected=False
    def _message(self,client,userdata,msg):
        self.model.update_topic(msg.topic,msg.payload)
        text=msg.payload.decode('utf-8','replace');parsed=None
        try: parsed=json.loads(text)
        except (ValueError,TypeError): pass
        if self.explorer_callback: self.explorer_callback(ExplorerMessage(msg.topic,text,msg.qos,msg.retain,time.time(),parsed))
    def start(self): self.client.connect_async(self.host,self.port,30);self.client.loop_start()
    def stop(self): self.client.loop_stop();self.client.disconnect()

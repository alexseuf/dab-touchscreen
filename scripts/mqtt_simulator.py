#!/usr/bin/env python3
import argparse, math, random, time
import paho.mqtt.client as mqtt
import yaml
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--host',default='127.0.0.1');ap.add_argument('--port',type=int,default=1883);ap.add_argument('--interval',type=float,default=.5);a=ap.parse_args()
    topics=yaml.safe_load((ROOT/'config/topics.yaml').read_text())['signals']
    if hasattr(mqtt,'CallbackAPIVersion'): c=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,client_id='dab-demo-publisher')
    else: c=mqtt.Client(client_id='dab-demo-publisher')
    c.connect(a.host,a.port,30);c.loop_start();t=0
    try:
        while True:
            t+=a.interval;p=5200+800*math.sin(t/8)
            v1=230+random.uniform(-1,1);v2=231+random.uniform(-1,1);v3=229+random.uniform(-1,1)
            i1=p/690;i2=p/693;i3=p/687
            vals={'grid_voltage_l1':v1,'grid_voltage_l2':v2,'grid_voltage_l3':v3,'grid_current_l1':i1,'grid_current_l2':i2,'grid_current_l3':i3,'grid_power_l1':v1*i1,'grid_power_l2':v2*i2,'grid_power_l3':v3*i3,'grid_frequency':50+random.uniform(-.03,.03),'input_power':p,'dc_link_voltage':700+random.uniform(-2,2),'output_voltage':400+random.uniform(-1,1),'output_current':p*.94/400,'output_power':p*.94,'temp_pfc':43+2*math.sin(t/20),'temp_dab_primary':46+2*math.sin(t/23),'temp_dab_secondary':44+2*math.sin(t/19),'temp_inductor':49+2*math.sin(t/25),'temp_transformer':47+2*math.sin(t/28)}
            for sid,val in vals.items():c.publish(topics[sid]['topic'],f'{val:.3f}',retain=True)
            time.sleep(a.interval)
    except KeyboardInterrupt: pass
    finally:c.loop_stop();c.disconnect()
if __name__=='__main__':main()

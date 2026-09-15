from __future__ import annotations
import ipaddress, os, socket, subprocess

def nmcli(*args,timeout=15):
    env={**os.environ,'LC_ALL':'C'}
    return subprocess.run(['nmcli','--terse','--escape','no',*args],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout,check=False,env=env)

def device_status():
    result=[]
    for interface,label in [('eth0','Ethernet'),('wlan0','WLAN')]:
        state=nmcli('-g','GENERAL.STATE,GENERAL.CONNECTION','device','show',interface)
        fields=state.stdout.strip().splitlines()
        status=fields[0] if fields else 'nicht verfügbar'
        connection=fields[1] if len(fields)>1 else '—'
        address=subprocess.run(['ip','-4','-brief','address','show','dev',interface],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False).stdout.split()
        ipv4=next((part for part in address if '/' in part),'—')
        result.extend([f'{label} ({interface})',f'  Status: {status}',f'  Verbindung: {connection}',f'  IPv4: {ipv4}'])
    try:
        with socket.create_connection(('127.0.0.1',1883),timeout=.5):pass
        result.append('MQTT-Broker: erreichbar (127.0.0.1:1883)')
    except OSError:result.append('MQTT-Broker: nicht erreichbar')
    return result

def wifi_scan(interface='wlan0'):
    p=nmcli('-f','SSID,SIGNAL,SECURITY','device','wifi','list','ifname',interface,'--rescan','yes',timeout=25)
    return p.stdout.strip().splitlines()

def wifi_status(interface='wlan0'):
    active=nmcli('-f','ACTIVE,SSID,SIGNAL,BARS,SECURITY','device','wifi','list','ifname',interface,'--rescan','no')
    row=next((line for line in active.stdout.splitlines() if line.startswith('yes:')),None)
    if not row:return {'connected':False,'ssid':'—','signal':0,'bars':'','security':'—','dbm':None,'ipv4':'—'}
    fields=row.split(':',4);signal=int(fields[2]) if len(fields)>2 and fields[2].isdigit() else 0
    address=nmcli('-g','IP4.ADDRESS','device','show',interface).stdout.strip().splitlines()
    dbm=None
    try:
        for line in open('/proc/net/wireless',encoding='ascii'):
            if line.lstrip().startswith(interface+':'):
                dbm=int(float(line.split()[3].rstrip('.')));break
    except (OSError,ValueError,IndexError):pass
    return {'connected':True,'ssid':fields[1] if len(fields)>1 else '—','signal':signal,'bars':fields[3] if len(fields)>3 else '','security':fields[4] if len(fields)>4 else '—','dbm':dbm,'ipv4':address[0] if address else '—'}

def connect_wifi(ssid,password,interface='wlan0'):
    if not ssid: raise ValueError('SSID fehlt')
    return nmcli('device','wifi','connect',ssid,'password',password,'ifname',interface,timeout=45)

def disconnect_wifi(interface='wlan0'):
    return nmcli('device','disconnect',interface,timeout=30)

def set_ethernet(connection,method,address='',gateway='',dns=''):
    if method=='manual': ipaddress.ip_interface(address)
    args=['connection','modify',connection,'ipv4.method',method]
    if method=='manual': args += ['ipv4.addresses',address,'ipv4.gateway',gateway,'ipv4.dns',dns]
    return nmcli(*args)

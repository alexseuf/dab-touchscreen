from __future__ import annotations
import ipaddress, os, socket, subprocess

def nmcli(*args,timeout=15):
    env={**os.environ,'LC_ALL':'C'}
    return subprocess.run(['nmcli','--terse','--escape','no',*args],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout,check=False,env=env)

def device_status():
    result=[]
    for interface,label in [('eth0','Ethernet'),('wlan0','WLAN')]:
        state=nmcli('-g','GENERAL.STATE,GENERAL.CONNECTION','device','show',interface)
        fields=state.stdout.strip().splitlines();status=fields[0] if fields else 'nicht verfügbar';connection=fields[1] if len(fields)>1 else '—'
        address=subprocess.run(['ip','-4','-brief','address','show','dev',interface],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False).stdout.split();ipv4=next((part for part in address if '/' in part),'—')
        result.extend([f'{label} ({interface})',f'  Status: {status}',f'  Verbindung: {connection}',f'  IPv4: {ipv4}'])
    try:
        with socket.create_connection(('127.0.0.1',1883),timeout=.5):pass
        result.append('MQTT-Broker: erreichbar (127.0.0.1:1883)')
    except OSError:result.append('MQTT-Broker: nicht erreichbar')
    return result

def wifi_radio_enabled():
    result=nmcli('radio','wifi')
    if result.returncode: raise RuntimeError((result.stderr or result.stdout).strip() or 'WLAN-Status konnte nicht gelesen werden')
    return result.stdout.strip().lower() == 'enabled'

def set_wifi_radio(enabled):
    return nmcli('radio','wifi','on' if enabled else 'off',timeout=30)

def wifi_scan(interface='wlan0'):
    p=nmcli('-f','SSID,SIGNAL,SECURITY','device','wifi','list','ifname',interface,'--rescan','yes',timeout=25)
    return p.stdout.strip().splitlines()

def wifi_status(interface='wlan0'):
    radio=wifi_radio_enabled()
    if not radio:return {'radio_enabled':False,'connected':False,'ssid':'—','signal':0,'bars':'','security':'—','dbm':None,'ipv4':'—'}
    active=nmcli('-f','ACTIVE,SSID,SIGNAL,BARS,SECURITY','device','wifi','list','ifname',interface,'--rescan','no');row=next((line for line in active.stdout.splitlines() if line.startswith('yes:')),None)
    if not row:return {'radio_enabled':True,'connected':False,'ssid':'—','signal':0,'bars':'','security':'—','dbm':None,'ipv4':'—'}
    fields=row.split(':',4);signal=int(fields[2]) if len(fields)>2 and fields[2].isdigit() else 0;address=nmcli('-g','IP4.ADDRESS','device','show',interface).stdout.strip().splitlines();dbm=None
    try:
        for line in open('/proc/net/wireless',encoding='ascii'):
            if line.lstrip().startswith(interface+':'):dbm=int(float(line.split()[3].rstrip('.')));break
    except (OSError,ValueError,IndexError):pass
    return {'radio_enabled':True,'connected':True,'ssid':fields[1] if len(fields)>1 else '—','signal':signal,'bars':fields[3] if len(fields)>3 else '','security':fields[4] if len(fields)>4 else '—','dbm':dbm,'ipv4':address[0] if address else '—'}

def connect_wifi(ssid,password,interface='wlan0'):
    if not ssid: raise ValueError('SSID fehlt')
    profiles=nmcli('-g','NAME,TYPE','connection','show')
    for line in profiles.stdout.splitlines():
        fields=line.rsplit(':',1)
        if len(fields)!=2 or fields[1] not in ('802-11-wireless','wifi'): continue
        name=fields[0]
        saved_ssid=nmcli('-g','802-11-wireless.ssid','connection','show',name)
        if saved_ssid.returncode==0 and saved_ssid.stdout.strip()==ssid:
            activated=nmcli('connection','up',name,'ifname',interface,timeout=45)
            if activated.returncode==0:return activated
    if not password:
        return subprocess.CompletedProcess(['nmcli'],10,'','Für dieses WLAN ist kein gespeichertes Profil vorhanden. Bitte Passwort eingeben.')
    return nmcli('device','wifi','connect',ssid,'password',password,'ifname',interface,timeout=45)

def disconnect_wifi(interface='wlan0'):return nmcli('device','disconnect',interface,timeout=30)

def _field(output):return next((line.strip() for line in output.splitlines() if line.strip()),'')

def ethernet_status(interface='eth0'):
    shown=nmcli('-g','GENERAL.STATE,GENERAL.CONNECTION,IP4.ADDRESS,IP4.GATEWAY,IP4.DNS','device','show',interface);rows=[line.strip() for line in shown.stdout.splitlines()];connection=rows[1] if len(rows)>1 else ''
    if not connection or connection=='--':
        profiles=nmcli('-g','NAME,TYPE','connection','show');connection=next((line.rsplit(':',1)[0] for line in profiles.stdout.splitlines() if line.rsplit(':',1)[-1] in ('802-3-ethernet','ethernet')),'')
    configured=nmcli('-g','ipv4.method,ipv4.addresses,ipv4.gateway,ipv4.dns','connection','show',connection) if connection and connection!='--' else None;settings=[line.strip() for line in configured.stdout.splitlines()] if configured else [];live_address=next((row for row in rows[2:] if '/' in row),'');address=(settings[1] if len(settings)>1 else '') or live_address;ip,prefix=(address.split('/',1)+['24'])[:2] if address else ('','24');gateway=(settings[2] if len(settings)>2 else '') or (rows[3] if len(rows)>3 else '');dns=(settings[3] if len(settings)>3 else '') or ', '.join(row for row in rows[4:] if row);method=settings[0] if settings else 'auto'
    return {'interface':interface,'state':rows[0] if rows else 'nicht verfügbar','connection':connection,'method':method,'address':ip,'prefix':prefix,'gateway':gateway,'dns':dns,'live_address':live_address}

def broker_status():
    addresses={}
    for interface in ('eth0','wlan0'):
        output=subprocess.run(['ip','-4','-brief','address','show','dev',interface],text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,check=False).stdout.split();addresses[interface]=next((part.split('/')[0] for part in output if '/' in part),'')
    try:
        with socket.create_connection(('127.0.0.1',1883),timeout=.5):pass
        running=True
    except OSError:running=False
    host=addresses['eth0'] or addresses['wlan0'] or '127.0.0.1';return {'running':running,'host':host,'port':1883,'preferred':'LAN' if addresses['eth0'] else ('WLAN' if addresses['wlan0'] else 'lokal')}

def set_ethernet(interface,method,address='',prefix='24',gateway='',dns=''):
    status=ethernet_status(interface);connection=status['connection']
    if not connection or connection=='--':raise ValueError(f'Keine Ethernet-Verbindung für {interface} gefunden')
    if method not in ('auto','manual'):raise ValueError('Ungültige IPv4-Methode')
    args=['connection','modify',connection]
    if method=='manual':
        ip=ipaddress.IPv4Address(address.strip());prefix_int=int(prefix)
        if not 1<=prefix_int<=32:raise ValueError('Prefix muss zwischen 1 und 32 liegen')
        network=ipaddress.IPv4Network(f'{ip}/{prefix_int}',strict=False);gateway_ip=ipaddress.IPv4Address(gateway.strip())
        if gateway_ip not in network:raise ValueError('Gateway liegt nicht im angegebenen Netz')
        dns_values=[value for value in dns.replace(',',' ').split() if value]
        if not dns_values:raise ValueError('Mindestens ein DNS-Server ist erforderlich')
        for value in dns_values:ipaddress.IPv4Address(value)
        args += ['ipv4.method','manual','ipv4.addresses',f'{ip}/{prefix_int}','ipv4.gateway',str(gateway_ip),'ipv4.dns',','.join(dns_values),'ipv4.ignore-auto-dns','yes']
    else:args += ['ipv4.method','auto','ipv4.addresses','','ipv4.gateway','','ipv4.dns','','ipv4.ignore-auto-dns','no']
    changed=nmcli(*args)
    if changed.returncode:return changed
    activated=nmcli('connection','up',connection,'ifname',interface,timeout=45)
    if activated.returncode:
        if status['method']=='manual' and status['address']:restore=['connection','modify',connection,'ipv4.method','manual','ipv4.addresses',f"{status['address']}/{status['prefix']}",'ipv4.gateway',status['gateway'],'ipv4.dns',status['dns'].replace(' ',''),'ipv4.ignore-auto-dns','yes']
        else:restore=['connection','modify',connection,'ipv4.method','auto','ipv4.addresses','','ipv4.gateway','','ipv4.dns','','ipv4.ignore-auto-dns','no']
        nmcli(*restore);nmcli('connection','up',connection,'ifname',interface,timeout=45);activated.stderr=(activated.stderr or '')+'\nVorherige Ethernet-Konfiguration wurde wiederhergestellt.'
    return activated

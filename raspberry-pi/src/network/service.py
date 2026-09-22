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


def usb_ethernet_status():
    """Return USB Ethernet adapters without making their presence mandatory."""
    adapters=[]
    sys_net='/sys/class/net'
    try:
        names=sorted(os.listdir(sys_net))
    except OSError:
        return adapters
    for interface in names:
        if interface in ('lo','eth0','wlan0'):
            continue
        device=os.path.realpath(os.path.join(sys_net,interface,'device'))
        # USB NICs have a USB ancestor in their sysfs device path.
        if '/usb' not in device:
            continue
        type_result=nmcli('-g','GENERAL.TYPE,GENERAL.STATE,GENERAL.CONNECTION','device','show',interface)
        rows=[row.strip() for row in type_result.stdout.splitlines()]
        if not rows or rows[0] not in ('ethernet','802-3-ethernet'):
            continue
        address=subprocess.run(['ip','-4','-brief','address','show','dev',interface],text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,check=False).stdout.split()
        ipv4=next((part for part in address if '/' in part),'')
        driver=''
        try:
            driver=os.path.basename(os.path.realpath(os.path.join(sys_net,interface,'device','driver')))
        except OSError:
            pass
        mac=''
        try:
            mac=open(os.path.join(sys_net,interface,'address'),encoding='ascii').read().strip()
        except OSError:
            pass
        adapters.append({'interface':interface,'state':rows[1] if len(rows)>1 else 'unbekannt','connection':rows[2] if len(rows)>2 and rows[2]!='--' else '—','ipv4':ipv4 or '—','driver':driver or '—','mac':mac or '—'})
    return adapters

def broker_status():
    addresses={}
    for interface in ('br0','eth0','wlan0'):
        output=subprocess.run(['ip','-4','-brief','address','show','dev',interface],text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,check=False).stdout.split();addresses[interface]=next((part.split('/')[0] for part in output if '/' in part),'')
    try:
        with socket.create_connection(('127.0.0.1',1883),timeout=.5):pass
        running=True
    except OSError:running=False
    host=addresses['br0'] or addresses['eth0'] or addresses['wlan0'] or '127.0.0.1'
    preferred='Bridge/LAN' if addresses['br0'] else ('LAN' if addresses['eth0'] else ('WLAN' if addresses['wlan0'] else 'lokal'))
    return {'running':running,'host':host,'port':1883,'preferred':preferred}

def set_ethernet(interface,method,address='',prefix='24',gateway='',dns=''):
    status=ethernet_status(interface);connection=status['connection']
    if not connection or connection=='--':raise ValueError(f'Keine Ethernet-Verbindung für {interface} gefunden')
    if method not in ('auto','manual'):raise ValueError('Ungültige IPv4-Methode')
    args=['connection','modify',connection]
    if method=='manual':
        ip=ipaddress.IPv4Address(address.strip());prefix_int=int(prefix)
        if not 1<=prefix_int<=32:raise ValueError('Prefix muss zwischen 1 und 32 liegen')
        network=ipaddress.IPv4Network(f'{ip}/{prefix_int}',strict=False)
        gateway_value=gateway.strip()
        if gateway_value:
            gateway_ip=ipaddress.IPv4Address(gateway_value)
            if gateway_ip not in network:raise ValueError('Gateway liegt nicht im angegebenen Netz')
        dns_values=[value for value in dns.replace(',',' ').split() if value]
        for value in dns_values:ipaddress.IPv4Address(value)
        # Gateway and DNS are intentionally optional. An isolated DUT LAN must
        # not install a competing default route; WLAN remains Internet/recovery.
        args += ['ipv4.method','manual','ipv4.addresses',f'{ip}/{prefix_int}','ipv4.gateway',gateway_value,'ipv4.dns',','.join(dns_values),'ipv4.ignore-auto-dns','yes','ipv4.never-default','yes' if not gateway_value else 'no']
    else:args += ['ipv4.method','auto','ipv4.addresses','','ipv4.gateway','','ipv4.dns','','ipv4.ignore-auto-dns','no']
    changed=nmcli(*args)
    if changed.returncode:return changed
    activated=nmcli('connection','up',connection,'ifname',interface,timeout=45)
    if activated.returncode:
        if status['method']=='manual' and status['address']:restore=['connection','modify',connection,'ipv4.method','manual','ipv4.addresses',f"{status['address']}/{status['prefix']}",'ipv4.gateway',status['gateway'],'ipv4.dns',status['dns'].replace(' ',''),'ipv4.ignore-auto-dns','yes']
        else:restore=['connection','modify',connection,'ipv4.method','auto','ipv4.addresses','','ipv4.gateway','','ipv4.dns','','ipv4.ignore-auto-dns','no']
        nmcli(*restore);nmcli('connection','up',connection,'ifname',interface,timeout=45);activated.stderr=(activated.stderr or '')+'\nVorherige Ethernet-Konfiguration wurde wiederhergestellt.'
    return activated


def bridge_status(bridge='br0'):
    """Return the current DAB bridge state without requiring a USB NIC."""
    link=subprocess.run(['ip','-brief','link','show','dev',bridge],text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,check=False)
    if link.returncode:
        return {'configured':False,'bridge':bridge,'ipv4':'—','members':[]}
    addr=subprocess.run(['ip','-4','-brief','address','show','dev',bridge],text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,check=False).stdout.split()
    ipv4=next((part for part in addr if '/' in part),'—')
    members=[]
    try:
        members=sorted(os.listdir(f'/sys/class/net/{bridge}/brif'))
    except OSError:
        pass
    return {'configured':True,'bridge':bridge,'ipv4':ipv4,'members':members}

def configure_usb_ethernet_bridge(address='192.168.2.138',prefix='24',lan_interface='eth0',bridge='br0'):
    """Create a transparent L2 bridge between onboard LAN and the detected USB NIC.

    The management address lives on br0. No gateway/DNS/default route is installed,
    so WLAN remains the Internet and recovery path. If no USB NIC is present,
    nothing is changed.
    """
    adapters=usb_ethernet_status()
    if not adapters:
        raise ValueError('Kein USB-Ethernet-Adapter erkannt; bestehendes LAN bleibt unverändert')
    usb_interface=adapters[0]['interface']
    ip=ipaddress.IPv4Address(address.strip());prefix_int=int(prefix)
    if not 1<=prefix_int<=32:raise ValueError('Prefix muss zwischen 1 und 32 liegen')

    bridge_profile='dab-br0'
    profiles=nmcli('-g','NAME,TYPE','connection','show').stdout.splitlines()
    if not any(line.rsplit(':',1)[0]==bridge_profile for line in profiles if ':' in line):
        created=nmcli('connection','add','type','bridge','ifname',bridge,'con-name',bridge_profile)
        if created.returncode:return created
    changed=nmcli('connection','modify',bridge_profile,
        'ipv4.method','manual','ipv4.addresses',f'{ip}/{prefix_int}',
        'ipv4.gateway','','ipv4.dns','','ipv4.ignore-auto-dns','yes',
        'ipv4.never-default','yes','ipv6.method','disabled')
    if changed.returncode:return changed

    def active_or_create_slave(interface,profile_name):
        shown=nmcli('-g','GENERAL.CONNECTION','device','show',interface)
        connection=_field(shown.stdout)
        if connection in ('','--'):
            added=nmcli('connection','add','type','ethernet','ifname',interface,'con-name',profile_name)
            if added.returncode:return added
            connection=profile_name
        return nmcli('connection','modify',connection,'master',bridge_profile,'slave-type','bridge')

    onboard=active_or_create_slave(lan_interface,'dab-br0-eth0')
    if onboard.returncode:return onboard
    usb=active_or_create_slave(usb_interface,f'dab-br0-{usb_interface}')
    if usb.returncode:return usb
    up=nmcli('connection','up',bridge_profile,timeout=45)
    if up.returncode:return up
    nmcli('device','connect',lan_interface,timeout=30)
    nmcli('device','connect',usb_interface,timeout=30)
    return up

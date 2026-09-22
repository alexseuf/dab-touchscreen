import subprocess
import unittest
from unittest.mock import patch

from src.network.service import ethernet_status, set_ethernet


def result(stdout='', returncode=0, stderr=''):
    return subprocess.CompletedProcess(['nmcli'], returncode, stdout, stderr)


class EthernetConfigurationTest(unittest.TestCase):
    @patch('src.network.service.subprocess.run')
    @patch('src.network.service.nmcli')
    def test_bridge_manual_method_survives_empty_gateway_and_dns(self, nmcli, run):
        # nmcli -g may return empty fields as completely empty output; status
        # must still read ipv4.method from the profile rather than row offsets.
        def side(*args, **kwargs):
            key=' '.join(args)
            if 'GENERAL.STATE' in key: return result('100 (connected)\n')
            if 'GENERAL.CONNECTION' in key: return result('dab-br0\n')
            if 'ipv4.method' in key: return result('manual\n')
            if 'ipv4.addresses' in key: return result('192.168.2.34/24\n')
            if 'ipv4.gateway' in key or 'ipv4.dns' in key: return result('')
            return result('')
        nmcli.side_effect=side
        run.return_value=result('br0 UP 192.168.2.34/24\n')
        status=ethernet_status('br0')
        self.assertEqual('manual',status['method'])
        self.assertEqual('192.168.2.34',status['address'])
        self.assertEqual('',status['gateway'])
        self.assertEqual('',status['dns'])


    @patch('src.network.service.subprocess.run')
    @patch('src.network.service.nmcli')
    def test_inactive_ethernet_uses_existing_wired_profile(self, nmcli, run):
        def side(*args, **kwargs):
            key=' '.join(args)
            if 'GENERAL.STATE' in key: return result('20 (unavailable)\n')
            if 'GENERAL.CONNECTION' in key: return result('--\n')
            if args[:3] == ('-g','NAME,TYPE','connection'):
                return result('Kabelgebundene Verbindung 1:802-3-ethernet\nWLAN:wifi\n')
            if 'ipv4.method' in key: return result('auto\n')
            return result('')
        nmcli.side_effect=side
        run.return_value=result('')
        status=ethernet_status('eth0')
        self.assertEqual('Kabelgebundene Verbindung 1',status['connection'])
        self.assertEqual('auto',status['method'])

    @patch('src.network.service.ethernet_status', return_value={'connection':'Kabelgebundene Verbindung 1'})
    @patch('src.network.service.nmcli')
    def test_static_configuration_is_validated_and_activated(self, nmcli, _status):
        nmcli.side_effect=[result(),result()]
        applied=set_ethernet('eth0','manual','192.168.1.100','24','192.168.1.1','192.168.1.1, 1.1.1.1')
        self.assertEqual(0,applied.returncode)
        modify=nmcli.call_args_list[0].args
        self.assertIn('192.168.1.100/24',modify)
        self.assertIn('192.168.1.1,1.1.1.1',modify)
        self.assertEqual(('connection','up','Kabelgebundene Verbindung 1','ifname','eth0'),nmcli.call_args_list[1].args)

    @patch('src.network.service.ethernet_status', return_value={'connection':'Kabelgebundene Verbindung 1'})
    @patch('src.network.service.nmcli')
    def test_isolated_static_lan_allows_empty_gateway_and_dns(self, nmcli, _status):
        nmcli.side_effect=[result(),result()]
        applied=set_ethernet('eth0','manual','192.168.2.138','24','','')
        self.assertEqual(0,applied.returncode)
        modify=nmcli.call_args_list[0].args
        self.assertIn('192.168.2.138/24',modify)
        self.assertEqual('',modify[modify.index('ipv4.gateway')+1])
        self.assertEqual('',modify[modify.index('ipv4.dns')+1])
        self.assertEqual('yes',modify[modify.index('ipv4.never-default')+1])

    @patch('src.network.service.ethernet_status', return_value={'connection':'Kabelgebundene Verbindung 1'})
    def test_gateway_outside_subnet_is_rejected(self, _status):
        with self.assertRaisesRegex(ValueError,'Gateway'):
            set_ethernet('eth0','manual','192.168.1.100','24','10.0.0.1','192.168.1.1')

    @patch('src.network.service.ethernet_status', return_value={'connection':'Kabelgebundene Verbindung 1'})
    @patch('src.network.service.nmcli')
    def test_dhcp_clears_static_values(self, nmcli, _status):
        nmcli.side_effect=[result(),result()]
        set_ethernet('eth0','auto')
        modify=nmcli.call_args_list[0].args
        self.assertIn('auto',modify)
        self.assertIn('ipv4.addresses',modify)
        self.assertIn('ipv4.ignore-auto-dns',modify)


if __name__=='__main__':
    unittest.main()

import subprocess
import unittest
from unittest.mock import patch

from src.network.service import ethernet_status, set_ethernet


def result(stdout='', returncode=0, stderr=''):
    return subprocess.CompletedProcess(['nmcli'], returncode, stdout, stderr)


class EthernetConfigurationTest(unittest.TestCase):
    @patch('src.network.service.nmcli')
    def test_inactive_ethernet_uses_existing_wired_profile(self, nmcli):
        nmcli.side_effect=[
            result('20 (unavailable)\n\n\n\n'),
            result('Kabelgebundene Verbindung 1:802-3-ethernet\nWLAN:wifi\n'),
            result('auto\n\n\n\n'),
        ]
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

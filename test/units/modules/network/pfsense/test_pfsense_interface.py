# Copyright: (c) 2018, Frederic Bor <frederic.bor@wanadoo.fr>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import sys

if sys.version_info < (2, 7):
    pytestmark = pytest.mark.skip("pfSense Ansible modules require Python >= 2.7")

from ansible.modules.network.pfsense import pfsense_interface
from .pfsense_module import TestPFSenseModule


class TestPFSenseInterfaceModule(TestPFSenseModule):

    module = pfsense_interface

    def __init__(self, *args, **kwargs):
        super(TestPFSenseInterfaceModule, self).__init__(*args, **kwargs)
        self.config_file = 'pfsense_interface_config.xml'

    @staticmethod
    def get_args_fields():
        """ return params fields """
        fields = ['descr', 'interface', 'enable', 'ipv4_type', 'mac', 'mtu', 'mss', 'speed_duplex']
        fields += ['ipv4_address', 'ipv4_prefixlen', 'ipv4_gateway', 'create_ipv4_gateway', 'ipv4_gateway_address', 'blockpriv', 'blockbogons']
        return fields

    def setUp(self):
        """ mocking up """

        def php_mock(command):
            if 'get_interface_list' in command:
                return ['vmx0', 'vmx1', 'vmx2', 'vmx3', 'vmx0.100', 'vmx1.1100']
            return ['autoselect']

        super(TestPFSenseInterfaceModule, self).setUp()

        self.php.return_value = None
        self.php.side_effect = php_mock

    ##############
    # tests utils
    #
    def get_target_elt(self, interface, absent=False):
        """ get the generated interface xml definition """
        elt_filter = {}
        elt_filter['descr'] = interface['descr']

        return self.assert_has_xml_tag('interfaces', elt_filter, absent=absent)

    def check_target_elt(self, interface, interface_elt):
        """ test the xml definition of interface """
        self.assert_xml_elt_equal(interface_elt, 'if', self.unalias_interface(interface['interface'], physical=True))

        # bools
        if interface.get('enable'):
            self.assert_xml_elt_is_none_or_empty(interface_elt, 'enable')
        else:
            self.assert_not_find_xml_elt(interface_elt, 'enable')

        if interface.get('blockpriv'):
            self.assert_xml_elt_equal(interface_elt, 'blockpriv', '')
        else:
            self.assert_not_find_xml_elt(interface_elt, 'blockpriv')

        if interface.get('blockbogons'):
            self.assert_xml_elt_equal(interface_elt, 'blockbogons', '')
        else:
            self.assert_not_find_xml_elt(interface_elt, 'blockbogons')

        # type related
        if interface.get('ipv4_type') is None or interface.get('ipv4_type') == 'none':
            self.assert_not_find_xml_elt(interface_elt, 'ipaddr')
            self.assert_not_find_xml_elt(interface_elt, 'subnet')
            self.assert_not_find_xml_elt(interface_elt, 'gateway')
        elif interface.get('ipv4_type') == 'static':
            if interface.get('ipv4_address'):
                self.assert_xml_elt_equal(interface_elt, 'ipaddr', interface['ipv4_address'])
            if interface.get('ipv4_prefixlen'):
                self.assert_xml_elt_equal(interface_elt, 'subnet', str(interface['ipv4_prefixlen']))
            if interface.get('ipv4_gateway'):
                self.assert_xml_elt_equal(interface_elt, 'gateway', interface['ipv4_gateway'])

        # mac, mss, mtu
        if interface.get('mac'):
            self.assert_xml_elt_equal(interface_elt, 'spoofmac', interface['mac'])
        else:
            self.assert_xml_elt_is_none_or_empty(interface_elt, 'spoofmac')

        if interface.get('mtu'):
            self.assert_xml_elt_equal(interface_elt, 'mtu', str(interface['mtu']))
        else:
            self.assert_not_find_xml_elt(interface_elt, 'mtu')

        if interface.get('mss'):
            self.assert_xml_elt_equal(interface_elt, 'mss', str(interface['mss']))
        else:
            self.assert_not_find_xml_elt(interface_elt, 'mss')

    ##############
    # tests
    #
    def test_interface_create_no_address(self):
        """ test creation of a new interface with no address """
        interface = dict(descr='VOICE', interface='vmx0.100')
        command = "create interface 'VOICE', port='vmx0.100', ipv4_type='none', speed_duplex='autoselect'"
        self.do_module_test(interface, command=command)

    def test_interface_create_static(self):
        """ test creation of a new interface with a static ip """
        interface = dict(descr='VOICE', interface='vmx0.100', ipv4_type='static', ipv4_address='10.20.30.40', ipv4_prefixlen=24)
        command = "create interface 'VOICE', port='vmx0.100', ipv4_type='static', ipv4_address='10.20.30.40', ipv4_prefixlen='24', speed_duplex='autoselect'"
        self.do_module_test(interface, command=command)

    def test_interface_create_gateway(self):
        """ test creation of a new interface with a static ip and a gateway """
        interface = dict(descr='VOICE', interface='vmx0.100', ipv4_type='static', ipv4_address='10.20.30.40', ipv4_prefixlen=24, ipv4_gateway='voice_gw')
        interface.update(dict(create_ipv4_gateway=True, ipv4_gateway_address='10.20.30.1'))
        command1 = "create gateway 'voice_gw', interface='opt4', ip='10.20.30.1'"
        command2 = ("create interface 'VOICE', port='vmx0.100', ipv4_type='static', ipv4_address='10.20.30.40'"
                    ", ipv4_prefixlen='24', ipv4_gateway='voice_gw', speed_duplex='autoselect'")
        self.do_module_test(interface, command=[command1, command2])

    def test_interface_create_none_mac_mtu_mss(self):
        """ test creation of a new interface """
        interface = dict(descr='VOICE', interface='vmx0.100', mac='00:11:22:33:44:55', mtu=1500, mss=1100)
        command = "create interface 'VOICE', port='vmx0.100', ipv4_type='none', mac='00:11:22:33:44:55', mtu='1500', mss='1100', speed_duplex='autoselect'"
        self.do_module_test(interface, command=command)

    def test_interface_delete(self):
        """ test deletion of an interface """
        interface = dict(descr='vt1', state='absent')
        command = "delete interface 'vt1'"
        self.do_module_test(interface, delete=True, command=command)

    def test_interface_delete_lan(self):
        """ test deletion of an interface """
        interface = dict(descr='lan', state='absent')
        commands = [
            "delete rule_separator 'test_separator', interface='lan'",
            "update rule 'floating_rule_2', interface='floating' set interface='wan,opt3'",
            "delete rule 'floating_rule_1', interface='floating'",
            "delete rule 'antilock_out_1', interface='lan'",
            "delete rule 'antilock_out_2', interface='lan'",
            "delete rule 'antilock_out_3', interface='lan'",
            "delete interface 'lan'"
        ]
        self.do_module_test(interface, delete=True, command=commands)

    def test_interface_update_noop(self):
        """ test not updating a interface """
        interface = dict(descr='lan_1100', interface='vmx1.1100', enable=True, ipv4_type='static', ipv4_address='172.16.151.210', ipv4_prefixlen=24)
        self.do_module_test(interface, changed=False)

    def test_interface_update_name(self):
        """ test updating interface name """
        interface = dict(descr='wlan_1100', interface='vmx1.1100', enable=True, ipv4_type='static', ipv4_address='172.16.151.210', ipv4_prefixlen=24)
        command = "update interface 'lan_1100' set interface='wlan_1100'"
        self.do_module_test(interface, changed=True, command=command)

    def test_interface_update_enable(self):
        """ test disabling interface """
        interface = dict(descr='lan_1100', interface='vmx1.1100', enable=False, ipv4_type='static', ipv4_address='172.16.151.210', ipv4_prefixlen=24)
        command = "update interface 'lan_1100' set enable=False"
        self.do_module_test(interface, changed=True, command=command)

    def test_interface_update_enable2(self):
        """ test enabling interface """
        interface = dict(descr='vt1', interface='vmx3', enable=True)
        command = "update interface 'vt1' set enable=True"
        self.do_module_test(interface, changed=True, command=command)

    def test_interface_update_mac(self):
        """ test updating mac """
        interface = dict(descr='lan_1100', interface='vmx1.1100', enable=True, ipv4_type='static',
                         ipv4_address='172.16.151.210', ipv4_prefixlen=24, mac='00:11:22:33:44:55', )
        command = "update interface 'lan_1100' set mac='00:11:22:33:44:55'"
        self.do_module_test(interface, changed=True, command=command)

    def test_interface_update_blocks(self):
        """ test updating block fields """
        interface = dict(descr='lan_1100', interface='vmx1.1100', enable=True, ipv4_type='static',
                         ipv4_address='172.16.151.210', ipv4_prefixlen=24, blockpriv=True, blockbogons=True)
        command = "update interface 'lan_1100' set blockpriv=True, blockbogons=True"
        self.do_module_test(interface, changed=True, command=command)

    def test_interface_error_used(self):
        """ test error already used """
        interface = dict(descr='lan_1100', interface='vmx1', enable=True, ipv4_type='static', ipv4_address='172.16.151.210', ipv4_prefixlen=24)
        msg = "Port vmx1 is already in use on interface lan"
        self.do_module_test(interface, failed=True, msg=msg)

    def test_interface_error_gw(self):
        """ test error no such gateway """
        interface = dict(descr='lan_1100', interface='vmx1.1100', enable=True, ipv4_type='static',
                         ipv4_address='172.16.151.210', ipv4_prefixlen=24, ipv4_gateway='voice_gw')
        msg = "Gateway voice_gw does not exist on lan_1100"
        self.do_module_test(interface, failed=True, msg=msg)

    def test_interface_error_if(self):
        """ test error no such interface """
        interface = dict(descr='wlan_1100', interface='vmx1.1200', enable=True, ipv4_type='static',
                         ipv4_address='172.16.151.210', ipv4_prefixlen=24, ipv4_gateway='voice_gw')
        msg = "vmx1.1200 can't be assigned. Interface may only be one the following: ['vmx0', 'vmx1', 'vmx2', 'vmx3', 'vmx0.100', 'vmx1.1100']"
        self.do_module_test(interface, failed=True, msg=msg)

    def test_interface_error_eq(self):
        """ test error same ipv4 address """
        interface = dict(descr='VOICE', interface='vmx0.100', ipv4_type='static', ipv4_address='192.168.1.242', ipv4_prefixlen=32)
        msg = "IPv4 address 192.168.1.242/32 is being used by or overlaps with: lan (192.168.1.242/24)"
        self.do_module_test(interface, failed=True, msg=msg)

    def test_interface_error_overlaps1(self):
        """ test error same ipv4 address """
        interface = dict(descr='VOICE', interface='vmx0.100', ipv4_type='static', ipv4_address='192.168.1.1', ipv4_prefixlen=30)
        msg = "IPv4 address 192.168.1.1/30 is being used by or overlaps with: lan (192.168.1.242/24)"
        self.do_module_test(interface, failed=True, msg=msg)

    def test_interface_error_overlaps2(self):
        """ test error same ipv4 address """
        interface = dict(descr='VOICE', interface='vmx0.100', ipv4_type='static', ipv4_address='192.168.1.1', ipv4_prefixlen=22)
        msg = "IPv4 address 192.168.1.1/22 is being used by or overlaps with: lan (192.168.1.242/24)"
        self.do_module_test(interface, failed=True, msg=msg)

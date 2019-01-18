# Copyright: (c) 2019, Olivier Blin <olivier.oblin@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.nxos import nxos_l3_interface
from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosL3InterfaceModule(TestNxosModule):

    module = nxos_l3_interface

    def setUp(self):
        super(TestNxosL3InterfaceModule, self).setUp()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_l3_interface.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_l3_interface.get_config')
        self.get_config = self.mock_get_config.start()

    def tearDown(self):
        super(TestNxosL3InterfaceModule, self).tearDown()
        self.mock_load_config.stop()
        self.mock_get_config.stop()

    def load_fixtures(self, commands=None, device=''):
        self.load_config.return_value = None
        self.get_config.return_value = load_fixture('nxos_l3_interface', self.mode)

    def test_nxos_l3_interface_unknonw_ethernet(self):
        self.mode = 'ethernet_noshut'
        set_module_args(dict(name='Ethernet1/2', ipv4='192.168.0.1/24'))
        result = self.execute_module(changed=False)

    # Add when missing
    def test_nxos_l3_interface_add_missing_ipv4(self):
        self.mode = 'ethernet_noshut'
        set_module_args(dict(name='Ethernet1/1', ipv4='192.168.0.1/24'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['interface Ethernet1/1', 'ip address 192.168.0.1/24', 'exit'])

    def test_nxos_l3_interface_add_missing_ipv4_on_e11(self):
        self.mode = 'ethernet_noshut'
        set_module_args(dict(name='et1/1', ipv4='192.168.0.1/24'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['interface Ethernet1/1', 'ip address 192.168.0.1/24', 'exit'])

    def test_nxos_l3_interface_add_missing_ipv6(self):
        self.mode = 'ethernet_noshut'
        set_module_args(dict(name='Ethernet1/1', ipv6='2001:db8::1/124'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['interface Ethernet1/1', 'ipv6 address 2001:db8::1/124', 'exit'])

    def test_nxos_l3_interface_add_missing_ipv4_and_ipv6(self):
        self.mode = 'ethernet_noshut'
        set_module_args(dict(name='Ethernet1/1', ipv4='192.168.0.1/24', ipv6='2001:db8::1/124'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['interface Ethernet1/1', 'ip address 192.168.0.1/24', 'ipv6 address 2001:db8::1/124', 'exit'])

    # Add when existing
    def test_nxos_l3_interface_add_existing_ipv4(self):
        self.mode = 'ethernet_noshut_ipv4_ipv6'
        set_module_args(dict(name='Ethernet1/1', ipv4='192.168.0.1/24'))
        result = self.execute_module()

    def test_nxos_l3_interface_add_existing_ipv4_on_e11(self):
        self.mode = 'ethernet_noshut_ipv4_ipv6'
        set_module_args(dict(name='et1/1', ipv4='192.168.0.1/24'))
        result = self.execute_module()

    def test_nxos_l3_interface_add_existing_ipv6(self):
        self.mode = 'ethernet_noshut_ipv4_ipv6'
        set_module_args(dict(name='Ethernet1/1', ipv6='2001:db8::1/124'))
        result = self.execute_module()

    def test_nxos_l3_interface_add_existing_ipv4_and_ipv6(self):
        self.mode = 'ethernet_noshut_ipv4_ipv6'
        set_module_args(dict(name='Ethernet1/1', ipv4='192.168.0.1/24', ipv6='2001:db8::1/124'))
        result = self.execute_module()

    def test_nxos_l3_interface_new_ipv4_and_ipv6(self):
        self.mode = 'ethernet_noshut_ipv4_ipv6'
        set_module_args(dict(name='Ethernet1/1', ipv4='192.168.0.2/24', ipv6='2001:db8::2/124'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['interface Ethernet1/1', 'ip address 192.168.0.2/24', 'ipv6 address 2001:db8::2/124', 'exit'])

    # Add when existing with multiple IPv6
    def test_nxos_l3_interface_multiple_ipv6_add_first(self):
        self.mode = 'ethernet_noshut_multiple_ipv6'
        set_module_args(dict(name='Ethernet1/1', ipv6='2001:db8::1/124'))
        result = self.execute_module()

    def test_nxos_l3_interface_multiple_ipv6_add_last(self):
        self.mode = 'ethernet_noshut_multiple_ipv6'
        set_module_args(dict(name='Ethernet1/1', ipv6='2001:db8:2::1/124'))
        result = self.execute_module()

    # Add aggregate
    def test_nxos_l3_interface_add_missing_with_empty_aggregate(self):
        self.mode = 'ethernet_noshut'
        set_module_args(dict(aggregate=[]))
        result = self.execute_module()

    def test_nxos_l3_interface_add_missing_with_aggregate(self):
        self.mode = 'ethernet_noshut'
        set_module_args(dict(aggregate=[
            dict(name='Ethernet1/1', ipv4='192.168.0.2/24', ipv6='2001:db8::2/124'),
            dict(name='Ethernet1/1', ipv6='2001:db8:1::2/124'),
            dict(name='Ethernet1/1', ipv6='2001:db8:2::2/124')]))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], [
            'interface Ethernet1/1', 'ip address 192.168.0.2/24', 'ipv6 address 2001:db8::2/124', 'exit',
            'interface Ethernet1/1', 'ipv6 address 2001:db8:1::2/124', 'exit',
            'interface Ethernet1/1', 'ipv6 address 2001:db8:2::2/124', 'exit'])

    # Rem when missing
    def test_nxos_l3_interface_rem_missing_ipv4(self):
        self.mode = 'ethernet_noshut'
        set_module_args(dict(name='Ethernet1/1', ipv4='192.168.0.1/24', state='absent'))
        result = self.execute_module()

    def test_nxos_l3_interface_rem_missing_ipv4_on_e11(self):
        self.mode = 'ethernet_noshut'
        set_module_args(dict(name='et1/1', ipv4='192.168.0.1/24', state='absent'))
        result = self.execute_module()

    def test_nxos_l3_interface_rem_missing_ipv6(self):
        self.mode = 'ethernet_noshut'
        set_module_args(dict(name='Ethernet1/1', ipv6='2001:db8::1/124', state='absent'))
        result = self.execute_module()

    def test_nxos_l3_interface_rem_missing_ipv4_and_ipv6(self):
        self.mode = 'ethernet_noshut'
        set_module_args(dict(name='Ethernet1/1', ipv4='192.168.0.1/24', ipv6='2001:db8::1/124', state='absent'))
        result = self.execute_module()

    # Rem when existing
    def test_nxos_l3_interface_rem_existing_ipv4(self):
        self.mode = 'ethernet_noshut_ipv4_ipv6'
        set_module_args(dict(name='Ethernet1/1', ipv4='192.168.0.1/24', state='absent'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['interface Ethernet1/1', 'no ip address 192.168.0.1/24', 'exit'])

    def test_nxos_l3_interface_rem_existing_ipv4_on_e11(self):
        self.mode = 'ethernet_noshut_ipv4_ipv6'
        set_module_args(dict(name='et1/1', ipv4='192.168.0.1/24', state='absent'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['interface Ethernet1/1', 'no ip address 192.168.0.1/24', 'exit'])

    def test_nxos_l3_interface_rem_existing_ipv6(self):
        self.mode = 'ethernet_noshut_ipv4_ipv6'
        set_module_args(dict(name='Ethernet1/1', ipv6='2001:db8::1/124', state='absent'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['interface Ethernet1/1', 'no ipv6 address 2001:db8::1/124', 'exit'])

    def test_nxos_l3_interface_rem_existing_ipv4_and_ipv6(self):
        self.mode = 'ethernet_noshut_ipv4_ipv6'
        set_module_args(dict(name='Ethernet1/1', ipv4='192.168.0.1/24', ipv6='2001:db8::1/124', state='absent'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['interface Ethernet1/1', 'no ip address 192.168.0.1/24', 'no ipv6 address 2001:db8::1/124', 'exit'])

    # Rem when existing with multiple IPv6
    def test_nxos_l3_interface_multiple_ipv6_rem_first(self):
        self.mode = 'ethernet_noshut_multiple_ipv6'
        set_module_args(dict(name='Ethernet1/1', ipv6='2001:db8::1/124', state='absent'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['interface Ethernet1/1', 'no ipv6 address 2001:db8::1/124', 'exit'])

    def test_nxos_l3_interface_multiple_ipv6_rem_last(self):
        self.mode = 'ethernet_noshut_multiple_ipv6'
        set_module_args(dict(name='Ethernet1/1', ipv6='2001:db8:2::1/124', state='absent'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['interface Ethernet1/1', 'no ipv6 address 2001:db8:2::1/124', 'exit'])

    # Rem when missing with aggregate
    def test_nxos_l3_interface_rem_with_empty_aggregate(self):
        self.mode = 'ethernet_noshut_multiple_ipv6'
        set_module_args(dict(aggregate=[], state='absent'))
        result = self.execute_module()

    def test_nxos_l3_interface_rem_missing_with_aggregate(self):
        self.mode = 'ethernet_noshut_multiple_ipv6'
        set_module_args(dict(state='absent', aggregate=[
            dict(name='Ethernet1/1', ipv4='192.168.0.2/24', ipv6='2001:db8::2/124'),
            dict(name='Ethernet1/1', ipv6='2001:db8:1::2/124'),
            dict(name='Ethernet1/1', ipv6='2001:db8:2::2/124')]))
        result = self.execute_module()

    # Rem when existing with aggregate
    def test_nxos_l3_interface_rem_existing_with_aggregate(self):
        self.mode = 'ethernet_noshut_multiple_ipv6'
        set_module_args(dict(state='absent', aggregate=[
            dict(name='Ethernet1/1', ipv4='192.168.0.1/24', ipv6='2001:db8::1/124'),
            dict(name='Ethernet1/1', ipv6='2001:db8:1::1/124'),
            dict(name='Ethernet1/1', ipv6='2001:db8:2::1/124')]))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], [
            'interface Ethernet1/1', 'no ip address 192.168.0.1/24', 'no ipv6 address 2001:db8::1/124', 'exit',
            'interface Ethernet1/1', 'no ipv6 address 2001:db8:1::1/124', 'exit',
            'interface Ethernet1/1', 'no ipv6 address 2001:db8:2::1/124', 'exit'])

    # Add itf only
    def test_nxos_l3_interface_add_on_itf_only(self):
        self.mode = 'ethernet_noshut'
        set_module_args(dict(name='Ethernet1/1'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['interface Ethernet1/1'])

    # Add unknown interface
    def test_nxos_l3_interface_add_on_unknown_itf(self):
        self.mode = 'ethernet_noshut'
        set_module_args(dict(name='Ethernet1/2', ipv4='192.168.0.1/24'))
        result = self.execute_module()
        self.assertEqual(result['warnings'], ['Unknown interface Ethernet1/2'])

    # Rem unknown interface
    def test_nxos_l3_interface_rem_on_unknown_itf(self):
        self.mode = 'ethernet_noshut'
        set_module_args(dict(name='Ethernet1/2', ipv4='192.168.0.1/24', state='absent'))
        result = self.execute_module()
        self.assertEqual(result['warnings'], ['Unknown interface Ethernet1/2'])

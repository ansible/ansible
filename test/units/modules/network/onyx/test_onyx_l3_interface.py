#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.compat.tests.mock import patch
from ansible.modules.network.onyx import onyx_l3_interface
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxL3InterfaceModule(TestOnyxModule):

    module = onyx_l3_interface

    def setUp(self):
        super(TestOnyxL3InterfaceModule, self).setUp()
        self.mock_get_config = patch.object(
            onyx_l3_interface.OnyxL3InterfaceModule,
            "_get_interfaces_config")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestOnyxL3InterfaceModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def _execute_module(self, failed=False, changed=False, commands=None, sort=True):
        if failed:
            result = self.failed()
            self.assertTrue(result['failed'], result)
        else:
            result = self.changed(changed)
            self.assertEqual(result['changed'], changed, result)

        if commands is not None:
            commands_res = result.get('commands')
            if sort:
                self.assertEqual(sorted(commands), sorted(commands_res), commands_res)
            else:
                self.assertEqual(commands, commands_res, commands_res)

        return result

    def load_fixture(self, config_file):
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None

    def load_eth_ifc_fixture(self):
        config_file = 'onyx_l3_interface_show.cfg'
        self.load_fixture(config_file)

    def load_vlan_ifc_fixture(self):
        config_file = 'onyx_l3_vlan_interface_show.cfg'
        self.load_fixture(config_file)

    def test_vlan_ifc_no_change(self):
        set_module_args(dict(name='Vlan 1002', state='present',
                             ipv4='172.3.12.4/24'))
        self.load_vlan_ifc_fixture()
        self._execute_module(changed=False)

    def test_vlan_ifc_remove(self):
        set_module_args(dict(name='Vlan 1002', state='absent'))
        commands = ['interface vlan 1002 no ip address']
        self.load_vlan_ifc_fixture()
        self._execute_module(changed=True, commands=commands)

    def test_vlan_ifc_update(self):
        set_module_args(dict(name='Vlan 1002', state='present',
                             ipv4='172.3.13.4/24'))
        commands = ['interface vlan 1002 ip address 172.3.13.4/24']
        self.load_vlan_ifc_fixture()
        self._execute_module(changed=True, commands=commands)

    def test_eth_ifc_no_change(self):
        set_module_args(dict(name='Eth1/5', state='present',
                             ipv4='172.3.12.4/24'))
        self.load_eth_ifc_fixture()
        self._execute_module(changed=False)

    def test_eth_ifc_remove(self):
        set_module_args(dict(name='Eth1/5', state='absent'))
        commands = ['interface ethernet 1/5 no ip address']
        self.load_eth_ifc_fixture()
        self._execute_module(changed=True, commands=commands)

    def test_eth_ifc_update(self):
        set_module_args(dict(name='Eth1/5', state='present',
                             ipv4='172.3.13.4/24'))
        commands = ['interface ethernet 1/5 ip address 172.3.13.4/24']
        self.load_eth_ifc_fixture()
        self._execute_module(changed=True, commands=commands)

    def test_eth_ifc_add_ip(self):
        set_module_args(dict(name='Eth1/6', state='present',
                             ipv4='172.3.14.4/24'))
        commands = ['interface ethernet 1/6 no switchport force',
                    'interface ethernet 1/6 ip address 172.3.14.4/24']
        self.load_eth_ifc_fixture()
        self._execute_module(changed=True, commands=commands)

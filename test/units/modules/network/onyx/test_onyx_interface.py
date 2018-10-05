#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.compat.tests.mock import patch
from ansible.modules.network.onyx import onyx_interface
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxInterfaceModule(TestOnyxModule):

    module = onyx_interface

    def setUp(self):
        super(TestOnyxInterfaceModule, self).setUp()
        self.mock_get_config = patch.object(
            onyx_interface.OnyxInterfaceModule, "_get_interfaces_config")
        self.get_config = self.mock_get_config.start()

        self.mock_get_interfaces_status = patch.object(
            onyx_interface.OnyxInterfaceModule, "_get_interfaces_status")
        self.get_interfaces_status = self.mock_get_interfaces_status.start()

        self.mock_get_interfaces_rates = patch.object(
            onyx_interface.OnyxInterfaceModule, "_get_interfaces_rates")
        self.get_interfaces_rates = self.mock_get_interfaces_rates.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_version = patch.object(
            onyx_interface.OnyxInterfaceModule, "_get_os_version")
        self.get_version = self.mock_get_version.start()

    def tearDown(self):
        super(TestOnyxInterfaceModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'onyx_interfaces_show.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None
        self.get_version.return_value = "3.6.5000"

    def test_mtu_no_change(self):
        set_module_args(dict(name='Eth1/1', mtu=1500))
        self.execute_module(changed=False)

    def test_mtu_change(self):
        set_module_args(dict(name='Eth1/1', mtu=1522))
        commands = ['interface ethernet 1/1', 'mtu 1522 force', 'exit']
        self.execute_module(changed=True, commands=commands)

    def test_speed_no_change(self):
        set_module_args(dict(name='Eth1/1', speed='40G'))
        self.execute_module(changed=False)

    def test_speed_change(self):
        set_module_args(dict(name='Eth1/1', speed='100G'))
        commands = ['interface ethernet 1/1', 'speed 100G force', 'exit']
        self.execute_module(changed=True, commands=commands)

    def test_mtu_speed_change(self):
        set_module_args(dict(name='Eth1/1', speed='100G', mtu=1522))
        commands = ['interface ethernet 1/1', 'speed 100G force',
                    'mtu 1522 force', 'exit']
        self.execute_module(changed=True, commands=commands)

    def test_admin_state_no_change(self):
        set_module_args(dict(name='Eth1/1', enabled=True))
        self.execute_module(changed=False)

    def test_admin_state_change(self):
        set_module_args(dict(name='Eth1/1', enabled=False))
        commands = ['interface ethernet 1/1', 'shutdown', 'exit']
        self.execute_module(changed=True, commands=commands)

    def test_add_loopback_if(self):
        set_module_args(dict(name='Loopback 1', description='Loopback test'))
        commands = ['interface loopback 1', 'description Loopback test',
                    'exit']
        self.execute_module(changed=True, commands=commands)

    def test_add_vlan_if(self):
        set_module_args(dict(name='Vlan 101', description='Vlan test',
                             enabled=True))
        commands = ['interface vlan 101', 'description Vlan test',
                    'no shutdown', 'exit']
        self.execute_module(changed=True, commands=commands)

    def test_remove_vlan_if(self):
        set_module_args(dict(name='Vlan 1002', state='absent'))
        commands = ['no interface vlan 1002']
        self.execute_module(changed=True, commands=commands)

    def test_oper_state_check(self):
        set_module_args(dict(name='Eth1/1', enabled=True, state='down'))
        config_file = 'onyx_interfaces_status.cfg'
        self.get_interfaces_status.return_value = load_fixture(config_file)
        self.execute_module(changed=False)

    def test_vlan_oper_state_check(self):
        set_module_args(dict(name='Vlan 1002', state='down'))
        config_file = 'onyx_interfaces_status.cfg'
        self.get_interfaces_status.return_value = load_fixture(config_file)
        self.execute_module(changed=False)

    def test_rx_rate_check(self):
        set_module_args(dict(name='Eth1/1', enabled=True, rx_rate='ge(9000)'))
        config_file = 'onyx_interfaces_rates.cfg'
        self.get_interfaces_rates.return_value = load_fixture(config_file)
        self.execute_module(changed=False)

    def test_tx_rate_check(self):
        set_module_args(dict(name='Eth1/1', enabled=True, tx_rate='ge(10000)'))
        config_file = 'onyx_interfaces_rates.cfg'
        self.get_interfaces_rates.return_value = load_fixture(config_file)
        self.execute_module(changed=False)

#
# (c) 2016 Red Hat Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.compat.tests.mock import patch
from ansible.modules.network.onyx import onyx_l2_interface
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxInterfaceModule(TestOnyxModule):

    module = onyx_l2_interface

    def setUp(self):
        super(TestOnyxInterfaceModule, self).setUp()
        self.mock_get_config = patch.object(
            onyx_l2_interface.OnyxL2InterfaceModule, "_get_switchport_config")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_version = patch.object(
            onyx_l2_interface.OnyxL2InterfaceModule, "_get_os_version")
        self.get_version = self.mock_get_version.start()

    def tearDown(self):
        super(TestOnyxInterfaceModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'onyx_l2_interface_show.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None
        self.get_version.return_value = "3.6.5000"

    def test_access_vlan_no_change(self):
        set_module_args(dict(name='Eth1/11', access_vlan=1))
        self.execute_module(changed=False)

    def test_trunk_vlans_no_change(self):
        set_module_args(dict(name='Eth1/10', mode='hybrid', access_vlan=1,
                             trunk_allowed_vlans=[10]))
        self.execute_module(changed=False)

    def test_access_vlan_change(self):
        set_module_args(dict(name='Eth1/11', access_vlan=10))
        commands = ['interface ethernet 1/11', 'switchport access vlan 10',
                    'exit']
        self.execute_module(changed=True, commands=commands)

    def test_trunk_vlan_change(self):
        set_module_args(dict(name='Eth1/10', mode='hybrid', access_vlan=1,
                             trunk_allowed_vlans=[11]))
        commands = ['interface ethernet 1/10',
                    'switchport hybrid allowed-vlan remove 10',
                    'switchport hybrid allowed-vlan add 11', 'exit']
        self.execute_module(changed=True, commands=commands)

    def test_trunk_vlan_add(self):
        set_module_args(dict(name='Eth1/10', mode='hybrid', access_vlan=1,
                             trunk_allowed_vlans=[10, 11]))
        commands = ['interface ethernet 1/10',
                    'switchport hybrid allowed-vlan add 11', 'exit']
        self.execute_module(changed=True, commands=commands)

    def test_switch_port_access(self):
        set_module_args(dict(name='Eth1/12', mode='access', access_vlan=11))
        commands = ['interface ethernet 1/12', 'switchport mode access',
                    'switchport access vlan 11', 'exit']
        self.execute_module(changed=True, commands=commands)

    def test_switch_port_trunk(self):
        set_module_args(dict(name='Eth1/12', mode='trunk',
                             trunk_allowed_vlans=[11]))
        commands = ['interface ethernet 1/12', 'switchport mode trunk',
                    'switchport trunk allowed-vlan add 11', 'exit']
        self.execute_module(changed=True, commands=commands)

    def test_switch_port_hybrid(self):
        set_module_args(dict(name='Eth1/12', mode='hybrid', access_vlan=10,
                             trunk_allowed_vlans=[11]))
        commands = ['interface ethernet 1/12', 'switchport mode hybrid',
                    'switchport access vlan 10',
                    'switchport hybrid allowed-vlan add 11', 'exit']
        self.execute_module(changed=True, commands=commands)

    def test_aggregate(self):
        aggregate = list()
        aggregate.append(dict(name='Eth1/10'))
        aggregate.append(dict(name='Eth1/12'))

        set_module_args(dict(aggregate=aggregate, access_vlan=10))
        commands = ['interface ethernet 1/10', 'switchport mode access',
                    'switchport access vlan 10', 'exit',
                    'interface ethernet 1/12', 'switchport mode access',
                    'switchport access vlan 10', 'exit']
        self.execute_module(changed=True, commands=commands, sort=False)

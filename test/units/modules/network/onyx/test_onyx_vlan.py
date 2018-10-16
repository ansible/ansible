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

from units.compat.mock import patch
from ansible.modules.network.onyx import onyx_vlan
from units.modules.utils import set_module_args
from .onyx_module import TestOnyxModule, load_fixture


class TestOnyxVlanModule(TestOnyxModule):

    module = onyx_vlan

    def setUp(self):
        super(TestOnyxVlanModule, self).setUp()
        self.mock_get_config = patch.object(
            onyx_vlan.OnyxVlanModule, "_get_vlan_config")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.onyx.onyx.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_version = patch.object(
            onyx_vlan.OnyxVlanModule, "_get_os_version")
        self.get_version = self.mock_get_version.start()

    def tearDown(self):
        super(TestOnyxVlanModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_get_version.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'onyx_vlan_show.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None
        self.get_version.return_value = "3.6.5000"

    def test_vlan_no_change(self):
        set_module_args(dict(vlan_id=20))
        self.execute_module(changed=False)

    def test_vlan_remove_name(self):
        set_module_args(dict(vlan_id=10, name=''))
        commands = ['vlan 10 no name']
        self.execute_module(changed=True, commands=commands)

    def test_vlan_change_name(self):
        set_module_args(dict(vlan_id=10, name='test-test'))
        commands = ['vlan 10 name test-test']
        self.execute_module(changed=True, commands=commands)

    def test_vlan_create(self):
        set_module_args(dict(vlan_id=30))
        commands = ['vlan 30', 'exit']
        self.execute_module(changed=True, commands=commands)

    def test_vlan_create_with_name(self):
        set_module_args(dict(vlan_id=30, name='test-test'))
        commands = ['vlan 30', 'exit', 'vlan 30 name test-test']
        self.execute_module(changed=True, commands=commands)

    def test_vlan_remove(self):
        set_module_args(dict(vlan_id=20, state='absent'))
        commands = ['no vlan 20']
        self.execute_module(changed=True, commands=commands)

    def test_vlan_remove_not_exist(self):
        set_module_args(dict(vlan_id=30, state='absent'))
        self.execute_module(changed=False)

    def test_vlan_aggregate(self):
        aggregate = list()
        aggregate.append(dict(vlan_id=30))
        aggregate.append(dict(vlan_id=20))
        set_module_args(dict(aggregate=aggregate))
        commands = ['vlan 30', 'exit']
        self.execute_module(changed=True, commands=commands)

    def test_vlan_aggregate_purge(self):
        aggregate = list()
        aggregate.append(dict(vlan_id=30))
        aggregate.append(dict(vlan_id=20))
        set_module_args(dict(aggregate=aggregate, purge=True))
        commands = ['vlan 30', 'exit', 'no vlan 10', 'no vlan 1']
        self.execute_module(changed=True, commands=commands)

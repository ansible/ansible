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

import json

from ansible.compat.tests.mock import patch
from ansible.modules.network.mlnxos import mlnxos_vlan
from ansible.module_utils.network.mlnxos import mlnxos as mlnxos_utils
from units.modules.utils import set_module_args
from .mlnxos_module import TestMlnxosModule, load_fixture


class TestMlnxosVlanModule(TestMlnxosModule):

    module = mlnxos_vlan

    def setUp(self):
        super(TestMlnxosVlanModule, self).setUp()
        self.mock_get_config = patch.object(
            mlnxos_vlan.MlnxosVlanModule, "_get_vlan_config")
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.mlnxos.mlnxos.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestMlnxosVlanModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'mlnxos_vlan_show.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None

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

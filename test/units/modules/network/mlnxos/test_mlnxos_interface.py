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
from ansible.modules.network.mlnxos import mlnxos_interface
from ansible.module_utils.network.mlnxos import mlnxos as mlnxos_utils
from units.modules.utils import set_module_args
from .mlnxos_module import TestMlnxosModule, load_fixture


class TestMlnxosInterfaceModule(TestMlnxosModule):

    module = mlnxos_interface

    def setUp(self):
        super(TestMlnxosInterfaceModule, self).setUp()
        self.mock_get_config = patch.object(
            mlnxos_interface.MlnxosInterfaceModule, "_get_interfaces_config")
        self.get_config = self.mock_get_config.start()

        self.mock_get_interfaces_status = patch.object(
            mlnxos_interface.MlnxosInterfaceModule, "_get_interfaces_status")
        self.get_interfaces_status = self.mock_get_interfaces_status.start()

        self.mock_get_interfaces_rates = patch.object(
            mlnxos_interface.MlnxosInterfaceModule, "_get_interfaces_rates")
        self.get_interfaces_rates = self.mock_get_interfaces_rates.start()

        self.mock_load_config = patch(
            'ansible.module_utils.network.mlnxos.mlnxos.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestMlnxosInterfaceModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        config_file = 'mlnxos_interfaces_show.cfg'
        self.get_config.return_value = load_fixture(config_file)
        self.load_config.return_value = None

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

    def test_oper_state_check(self):
        set_module_args(dict(name='Eth1/1', enabled=True, state='down'))
        config_file = 'mlnxos_interfaces_status.cfg'
        self.get_interfaces_status.return_value = load_fixture(config_file)
        commands = ['interface ethernet 1/1', 'shutdown', 'exit']
        self.execute_module(changed=False)

    def test_rx_rate_check(self):
        set_module_args(dict(name='Eth1/1', enabled=True, rx_rate='ge(9000)'))
        config_file = 'mlnxos_interfaces_rates.cfg'
        self.get_interfaces_rates.return_value = load_fixture(config_file)
        self.execute_module(changed=False)

    def test_tx_rate_check(self):
        set_module_args(dict(name='Eth1/1', enabled=True, tx_rate='ge(10000)'))
        config_file = 'mlnxos_interfaces_rates.cfg'
        self.get_interfaces_rates.return_value = load_fixture(config_file)
        self.execute_module(changed=False)

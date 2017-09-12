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

import os

from ansible.compat.tests.mock import patch
from ansible.modules.network.nxos import nxos_switchport
from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosSwitchportModule(TestNxosModule):

    module = nxos_switchport

    def setUp(self):
        self.mock_run_commands = patch('ansible.modules.network.nxos.nxos_switchport.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_switchport.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        self.mock_run_commands.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, device=''):
        def load_from_file(*args, **kwargs):
            module, commands = args
            output = list()
            for command in commands:
                filename = str(command).split(' | ')[0].replace(' ', '_')
                filename = filename.replace('2/1', '')
                output.append(load_fixture('nxos_switchport', filename))
            return output

        self.run_commands.side_effect = load_from_file
        self.load_config.return_value = None

    def test_nxos_switchport_present(self):
        set_module_args(dict(interface='Ethernet2/1', mode='access', access_vlan=1, state='present'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['interface ethernet2/1', 'switchport access vlan 1'])

    def test_nxos_switchport_unconfigured(self):
        set_module_args(dict(interface='Ethernet2/1', state='unconfigured'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['interface ethernet2/1',
                                              'switchport mode access',
                                              'switch access vlan 1',
                                              'switchport trunk native vlan 1',
                                              'switchport trunk allowed vlan all'])

    def test_nxos_switchport_absent(self):
        set_module_args(dict(interface='Ethernet2/1', mode='access', access_vlan=3, state='absent'))
        result = self.execute_module(changed=False)
        self.assertEqual(result['commands'], [])

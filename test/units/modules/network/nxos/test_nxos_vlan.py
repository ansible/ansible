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
from ansible.modules.network.nxos import nxos_vlan
from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosVlanModule(TestNxosModule):

    module = nxos_vlan

    def setUp(self):
        super(TestNxosVlanModule, self).setUp()

        self.mock_run_commands = patch('ansible.modules.network.nxos.nxos_vlan.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_vlan.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_vlan.get_config')
        self.get_config = self.mock_get_config.start()

    def tearDown(self):
        super(TestNxosVlanModule, self).tearDown()
        self.mock_run_commands.stop()
        self.mock_load_config.stop()
        self.mock_get_config.stop()

    def load_fixtures(self, commands=None, device=''):
        def load_from_file(*args, **kwargs):
            module, commands = args
            output = list()

            for item in commands:
                try:
                    obj = json.loads(item)
                    command = obj['command']
                except ValueError:
                    command = item
                filename = '%s.txt' % str(command).split(' | ')[0].replace(' ', '_')
                output.append(load_fixture('nxos_vlan', filename))
            return output

        self.run_commands.side_effect = load_from_file
        self.load_config.return_value = None
        self.get_config.return_value = load_fixture('nxos_vlan', 'config.cfg')

    def test_nxos_vlan_range(self):
        set_module_args(dict(vlan_range='6-10'))
        self.execute_module(changed=True, commands=['vlan 6', 'vlan 7', 'vlan 8', 'vlan 9', 'vlan 10'])

    def test_nxos_vlan_range_absent(self):
        set_module_args(dict(vlan_range='1-5', state='absent'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['no vlan 1'])

    def test_nxos_vlan_id(self):
        set_module_args(dict(vlan_id='15', state='present'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['vlan 15', 'state active', 'no shutdown', 'exit'])

    def test_nxos_vlan_id_absent(self):
        set_module_args(dict(vlan_id='1', state='absent'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['no vlan 1'])

    def test_nxos_vlan_named_vlan(self):
        set_module_args(dict(vlan_id='15', name='WEB'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['vlan 15', 'name WEB', 'state active', 'no shutdown', 'exit'])

    def test_nxos_vlan_shut_down(self):
        set_module_args(dict(vlan_id='1', admin_state='down'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['vlan 1', 'shutdown', 'exit'])

    def test_nxos_vlan_no_change(self):
        set_module_args(dict(vlan_id='1', name='default', vlan_state='active', admin_state='up'))
        result = self.execute_module(changed=False)
        self.assertEqual(result['commands'], [])

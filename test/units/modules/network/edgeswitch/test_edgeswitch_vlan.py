# (c) 2018 Red Hat Inc.
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from units.compat.mock import patch
from ansible.modules.network.edgeswitch import edgeswitch_vlan
from ansible.modules.network.edgeswitch.edgeswitch_vlan import parse_vlan_brief, parse_interfaces_switchport
from units.modules.utils import set_module_args
from .edgeswitch_module import TestEdgeswitchModule, load_fixture


class TestEdgeswitchVlanModule(TestEdgeswitchModule):

    module = edgeswitch_vlan

    def setUp(self):
        super(TestEdgeswitchVlanModule, self).setUp()

        self.mock_run_commands = patch('ansible.modules.network.edgeswitch.edgeswitch_vlan.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_load_config = patch('ansible.modules.network.edgeswitch.edgeswitch_vlan.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestEdgeswitchVlanModule, self).tearDown()
        self.mock_run_commands.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None):
        def load_from_file(*args, **kwargs):
            module, commands = args
            output = list()

            for command in commands:
                if command.startswith('vlan ') or command == 'exit':
                    output.append('')
                else:
                    filename = str(command).split(' | ')[0].replace(' ', '_')
                    output.append(load_fixture('edgeswitch_vlan_%s' % filename))
            return output

        self.run_commands.side_effect = load_from_file
        self.load_config.return_value = {}

    def test_edgeswitch_vlan_create(self):
        set_module_args({'vlan_id': '200', 'name': 'video', 'state': 'present'})
        result = self.execute_module(changed=True)
        expected_commands = [
            'vlan database',
            'vlan 200',
            'vlan name 200 \"video\"',
            'exit'
        ]
        self.assertEqual(result['commands'], expected_commands)

    def test_edgeswitch_vlan_id_startwith_100(self):
        set_module_args({'vlan_id': '100', 'name': 'voice', 'state': 'present'})
        result = self.execute_module(changed=False)
        expected_commands = []
        self.assertEqual(result['commands'], expected_commands)

    def test_edgeswitch_vlan_rename(self):
        set_module_args({'vlan_id': '100', 'name': 'video', 'state': 'present'})
        result = self.execute_module(changed=True)
        expected_commands = [
            'vlan database',
            'vlan name 100 \"video\"',
            'exit'
        ]
        self.assertEqual(result['commands'], expected_commands)

    def test_edgeswitch_vlan_with_interfaces_range(self):
        set_module_args({'vlan_id': '100', 'name': 'voice', 'state': 'present', 'tagged_interfaces': ['0/6-0/8']})
        result = self.execute_module(changed=True)
        expected_commands = [
            'interface 0/6-0/8',
            'vlan participation include 100',
            'vlan tagging 100',
        ]
        self.assertEqual(result['commands'], expected_commands)

    def test_edgeswitch_vlan_with_interfaces_and_newvlan(self):
        set_module_args({'vlan_id': '3', 'name': 'vlan3', 'state': 'present', 'untagged_interfaces': ['0/8', '0/7']})
        result = self.execute_module(changed=True)
        expected_commands = [
            'vlan database',
            'vlan 3',
            'vlan name 3 \"vlan3\"',
            'exit',
            'interface 0/7-0/8',
            'vlan participation include 3',
            'vlan pvid 3',
        ]
        self.assertEqual(result['commands'], expected_commands)

    def test_parse_interfaces_switchport(self):
        result = parse_interfaces_switchport(load_fixture('edgeswitch_vlan_show_interfaces_switchport'))
        i1 = {
            'interface': '0/1',
            'pvid_mode': '1',
            'untagged_vlans': ['1'],
            'tagged_vlans': ['100'],
            'forbidden_vlans': [''],
        }
        i3 = {
            'interface': '0/3',
            'pvid_mode': '1',
            'untagged_vlans': [''],
            'tagged_vlans': ['100'],
            'forbidden_vlans': ['1'],
        }
        i5 = {
            'interface': '0/5',
            'pvid_mode': '100',
            'untagged_vlans': ['100'],
            'tagged_vlans': [''],
            'forbidden_vlans': [''],
        }
        self.assertEqual(result['0/1'], i1)
        self.assertEqual(result['0/3'], i3)
        self.assertEqual(result['0/5'], i5)

    def test_parse_vlan_brief(self):
        result = parse_vlan_brief(load_fixture('edgeswitch_vlan_show_vlan_brief'))
        obj = [
            {
                'vlan_id': '1',
                'name': 'default'
            },
            {
                'vlan_id': '100',
                'name': 'voice'
            }
        ]
        self.assertEqual(result, obj)

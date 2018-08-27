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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from ansible.compat.tests.mock import patch
from ansible.modules.network.ios import ios_vlan
from ansible.modules.network.ios.ios_vlan import parse_vlan_brief
from units.modules.utils import set_module_args
from .ios_module import TestIosModule, load_fixture


class TestIosVlanModule(TestIosModule):

    module = ios_vlan

    def setUp(self):
        super(TestIosVlanModule, self).setUp()

        self.mock_run_commands = patch('ansible.modules.network.ios.ios_vlan.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_load_config = patch('ansible.modules.network.ios.ios_vlan.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestIosVlanModule, self).tearDown()
        self.mock_run_commands.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        self.run_commands.return_value = [load_fixture('ios_vlan_config.cfg')]
        self.load_config.return_value = {'diff': None, 'session': 'session'}

    def test_ios_vlan_create(self):
        set_module_args({'vlan_id': '3', 'name': 'test', 'state': 'present'})
        result = self.execute_module(changed=True)
        expected_commands = [
            'vlan 3',
            'name test',
        ]
        self.assertEqual(result['commands'], expected_commands)

    def test_ios_vlan_id_startwith_9(self):
        set_module_args({'vlan_id': '9', 'name': 'vlan9', 'state': 'present'})
        result = self.execute_module(changed=False)
        expected_commands = []
        self.assertEqual(result['commands'], expected_commands)

    def test_ios_vlan_rename(self):
        set_module_args({'vlan_id': '2', 'name': 'test', 'state': 'present'})
        result = self.execute_module(changed=True)
        expected_commands = [
            'vlan 2',
            'name test',
        ]
        self.assertEqual(result['commands'], expected_commands)

    def test_ios_vlan_with_interfaces(self):
        set_module_args({'vlan_id': '2', 'name': 'vlan2', 'state': 'present', 'interfaces': ['GigabitEthernet1/0/8', 'GigabitEthernet1/0/7']})
        result = self.execute_module(changed=True)
        expected_commands = [
            'vlan 2',
            'interface GigabitEthernet1/0/8',
            'switchport mode access',
            'switchport access vlan 2',
            'vlan 2',
            'interface GigabitEthernet1/0/6',
            'switchport mode access',
            'no switchport access vlan 2',
        ]
        self.assertEqual(result['commands'], expected_commands)

    def test_ios_vlan_with_interfaces_and_newvlan(self):
        set_module_args({'vlan_id': '3', 'name': 'vlan3', 'state': 'present', 'interfaces': ['GigabitEthernet1/0/8', 'GigabitEthernet1/0/7']})
        result = self.execute_module(changed=True)
        expected_commands = [
            'vlan 3',
            'name vlan3',
            'interface GigabitEthernet1/0/8',
            'switchport mode access',
            'switchport access vlan 3',
            'interface GigabitEthernet1/0/7',
            'switchport mode access',
            'switchport access vlan 3',
        ]
        self.assertEqual(result['commands'], expected_commands)

    def test_parse_vlan_brief(self):
        result = parse_vlan_brief(load_fixture('ios_vlan_config.cfg'))
        obj = [
            {
                'name': 'default',
                'interfaces': [
                    'GigabitEthernet1/0/4',
                    'GigabitEthernet1/0/5',
                    'GigabitEthernet1/0/52',
                    'GigabitEthernet1/0/54',
                ],
                'state': 'active',
                'vlan_id': '1',
            },
            {
                'name': 'vlan2',
                'interfaces': [
                    'GigabitEthernet1/0/6',
                    'GigabitEthernet1/0/7',
                ],
                'state': 'active',
                'vlan_id': '2',
            },
            {
                'name': 'vlan9',
                'interfaces': [
                    'GigabitEthernet1/0/6',
                ],
                'state': 'active',
                'vlan_id': '9',
            },
            {
                'name': 'fddi-default',
                'interfaces': [],
                'state': 'act/unsup',
                'vlan_id': '1002',
            },
            {
                'name': 'fddo-default',
                'interfaces': [],
                'state': 'act/unsup',
                'vlan_id': '1003',
            },
        ]
        self.assertEqual(result, obj)

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

from units.compat.mock import patch
from ansible.modules.network.cnos import cnos_vlan
from ansible.modules.network.cnos.cnos_vlan import parse_vlan_brief
from units.modules.utils import set_module_args
from .cnos_module import TestCnosModule, load_fixture


class TestCnosVlanModule(TestCnosModule):

    module = cnos_vlan

    def setUp(self):
        super(TestCnosVlanModule, self).setUp()

        self.mock_run_commands = patch('ansible.modules.network.cnos.cnos_vlan.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_load_config = patch('ansible.modules.network.cnos.cnos_vlan.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestCnosVlanModule, self).tearDown()
        self.mock_run_commands.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        self.run_commands.return_value = [load_fixture('cnos_vlan_config.cfg')]
        self.load_config.return_value = {'diff': None, 'session': 'session'}

    def test_cnos_vlan_create(self):
        set_module_args({'vlan_id': '3', 'name': 'test', 'state': 'present'})
        result = self.execute_module(changed=True)
        expected_commands = [
            'vlan 3',
            'name test',
        ]
        self.assertEqual(result['commands'], expected_commands)

    def test_cnos_vlan_id_startwith_9(self):
        set_module_args({'vlan_id': '13', 'name': 'anil', 'state': 'present'})
        result = self.execute_module(changed=False)
        expected_commands = []
        self.assertEqual(result['commands'], expected_commands)

    def test_cnos_vlan_rename(self):
        set_module_args({'vlan_id': '2', 'name': 'test', 'state': 'present'})
        result = self.execute_module(changed=True)
        expected_commands = [
            'vlan 2',
            'name test',
        ]
        self.assertEqual(result['commands'], expected_commands)

    def test_cnos_vlan_with_interfaces(self):
        set_module_args({'vlan_id': '2', 'name': 'vlan2', 'state': 'present',
                         'interfaces': ['Ethernet1/33', 'Ethernet1/44']})
        result = self.execute_module(changed=True)
        expected_commands = [
            'vlan 2',
            'name vlan2',
            'vlan 2',
            'interface Ethernet1/33',
            'switchport mode access',
            'switchport access vlan 2',
            'vlan 2',
            'interface Ethernet1/44',
            'switchport mode access',
            'switchport access vlan 2',
        ]
        self.assertEqual(result['commands'], expected_commands)

    def test_cnos_vlan_with_interfaces_and_newvlan(self):
        set_module_args({'vlan_id': '3',
                         'name': 'vlan3', 'state': 'present',
                         'interfaces': ['Ethernet1/33', 'Ethernet1/44']})
        result = self.execute_module(changed=True)
        expected_commands = [
            'vlan 3',
            'name vlan3',
            'vlan 3',
            'interface Ethernet1/33',
            'switchport mode access',
            'switchport access vlan 3',
            'vlan 3',
            'interface Ethernet1/44',
            'switchport mode access',
            'switchport access vlan 3',
        ]
        self.assertEqual(result['commands'], expected_commands)

    def test_parse_vlan_brief(self):
        result = parse_vlan_brief(load_fixture('cnos_vlan_config.cfg'))
        obj = [
            {
                'interfaces': [
                    'po1',
                    'po2',
                    'po11',
                    'po12',
                    'po13',
                    'po14',
                    'po15',
                    'po17',
                    'po20',
                    'po100',
                    'po1001',
                    'po1002',
                    'po1003',
                    'po1004',
                    'Ethernet1/2',
                    'Ethernet1/3',
                    'Ethernet1/4',
                    'Ethernet1/9',
                    'Ethernet1/10',
                    'Ethernet1/11',
                    'Ethernet1/14',
                    'Ethernet1/15',
                    'Ethernet1/16',
                    'Ethernet1/17',
                    'Ethernet1/18',
                    'Ethernet1/19',
                    'Ethernet1/20',
                    'Ethernet1/21',
                    'Ethernet1/22',
                    'Ethernet1/23',
                    'Ethernet1/24',
                    'Ethernet1/25',
                    'Ethernet1/26',
                    'Ethernet1/27',
                    'Ethernet1/28',
                    'Ethernet1/29',
                    'Ethernet1/30',
                    'Ethernet1/31',
                    'Ethernet1/32',
                    'Ethernet1/33',
                    'Ethernet1/34',
                    'Ethernet1/35',
                    'Ethernet1/36',
                    'Ethernet1/37',
                    'Ethernet1/38',
                    'Ethernet1/39',
                    'Ethernet1/40',
                    'Ethernet1/41',
                    'Ethernet1/42',
                    'Ethernet1/43',
                    'Ethernet1/44',
                    'Ethernet1/45',
                    'Ethernet1/46',
                    'Ethernet1/47',
                    'Ethernet1/48',
                    'Ethernet1/49',
                    'Ethernet1/50',
                    'Ethernet1/51',
                    'Ethernet1/52',
                    'Ethernet1/53',
                    'Ethernet1/54'],
                'state': 'ACTIVE',
                'name': 'default',
                'vlan_id': '1'},
            {
                'interfaces': [],
                'state': 'ACTIVE',
                'name': 'VLAN0002',
                'vlan_id': '2'},
            {
                'interfaces': [],
                'state': 'ACTIVE',
                'name': 'VLAN0003',
                'vlan_id': '3'},
            {
                'interfaces': [],
                'state': 'ACTIVE',
                'name': 'VLAN0005',
                'vlan_id': '5'},
            {
                'interfaces': [],
                'state': 'ACTIVE',
                'name': 'VLAN0012',
                'vlan_id': '12'},
            {
                'interfaces': [],
                'state': 'ACTIVE',
                'name': 'anil',
                'vlan_id': '13'}]
        self.assertEqual(result, obj)

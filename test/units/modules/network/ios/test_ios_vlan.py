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
        self.run_commands.return_value = load_fixture('ios_vlan_config.cfg')
        self.load_config.return_value = {'diff': None, 'session': 'session'}

    def test_ios_vlan_create(self):
        set_module_args({'vlan_id': '2', 'name': 'test', 'state': 'present'})
        result = self.execute_module()
        self.assertEqual(result['commands'], ['vlan 2', 'name test'])

    def test_parse_vlan_brief(self):
        result = parse_vlan_brief(load_fixture('ios_vlan_config.cfg'))
        obj = [
            {
                'name': 'default',
                'interfaces': [
                    'GigabitEthernet1/0/4',
                    'GigabitEthernet1/0/5',
                    'GigabitEthernet1/0/52',
                ],
                'state': 'active',
                'vlan_id': '1'},
            {
                'name': 'fddi-default',
                'interfaces': [],
                'state': 'act/unsup',
                'vlan_id': '1002',
            }
        ]
        self.assertEqual(result, obj)

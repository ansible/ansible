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
from units.compat.mock import patch
from ansible.modules.network.ios import ios_l2_interface
from units.modules.utils import set_module_args
from .ios_module import TestIosModule, load_fixture


class TestIosUserModule(TestIosModule):
    module = ios_l2_interface

    def setUp(self):
        super(TestIosUserModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.ios.ios_l2_interface.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.ios.ios_l2_interface.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestIosUserModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        self.get_config.return_value = load_fixture('ios_l2_interface_config.cfg')
        self.load_config.return_value = dict(diff=None, session='session')

    def test_ios_l2_interface_with_voice_vlan(self):
        set_module_args({'state': 'present', 'voice_vlan': '20', 'access_vlan': '10', 'mode': 'voice-access',
                         'name': 'GigabitEthernet0/5'})
        result = self.execute_module(changed=True)
        expected_commands = [
            'interface GigabitEthernet0/5',
            'switchport mode access',
            'switchport access vlan 10',
            'switchport voice vlan 20',
        ]
        self.assertEqual(result['commands'], expected_commands)

    def test_ios_l2_interface_default_interface(self):
        set_module_args({'state': 'unconfigured', 'name': 'GigabitEthernet0/5'})
        result = self.execute_module(changed=True)
        expected_commands = [
            'interface GigabitEthernet0/5',
            'switchport mode access',
            'switchport access vlan 1',
            'no switchport voice vlan',
            'switchport trunk native vlan 1',
            'switchport trunk allowed vlan all',
        ]
        self.assertEqual(result['commands'], expected_commands)

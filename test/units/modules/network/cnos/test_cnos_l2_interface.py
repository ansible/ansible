#
# (c) 2018 Lenovo.
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
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
import json

from units.compat.mock import patch
from ansible.modules.network.cnos import cnos_l2_interface
from units.modules.utils import set_module_args
from .cnos_module import TestCnosModule, load_fixture


class TestCnosL2InterfaceModule(TestCnosModule):
    module = cnos_l2_interface

    def setUp(self):
        super(TestCnosL2InterfaceModule, self).setUp()
        self._patch_get_config = patch(
            'ansible.modules.network.cnos.cnos_l2_interface.get_config'
        )
        self._patch_load_config = patch(
            'ansible.modules.network.cnos.cnos_l2_interface.load_config'
        )
        self._patch_run_commands = patch(
            'ansible.modules.network.cnos.cnos_l2_interface.run_commands'
        )

        self._get_config = self._patch_get_config.start()
        self._load_config = self._patch_load_config.start()
        self._run_commands = self._patch_run_commands.start()
        self._run_commands.side_effect = self.run_commands_load_fixtures

    def run_commands_load_fixtures(self, module, commands, *args, **kwargs):
        return self.load_fixtures(
            commands,
            destination=self._run_commands,
            return_values=True
        )

    def tearDown(self):
        super(TestCnosL2InterfaceModule, self).tearDown()
        self._patch_get_config.stop()
        self._patch_load_config.stop()
        self._patch_run_commands.stop()

    def load_fixtures(self, commands=None,
                      destination=None, return_values=False):
        side_effects = []

        if not destination:
            destination = self._get_config

        if not commands:
            commands = ['cnos_config_config.cfg']

        for command in commands:
            filename = str(command).replace(' ', '_')
            filename = str(filename).replace('/', '_')
            side_effects.append(load_fixture(filename))

        if return_values is True:
            return side_effects

        destination.side_effect = side_effects
        return None

    def test_cnos_l2_interface_access_vlan(self, *args, **kwargs):
        set_module_args(dict(
            name='Ethernet 1/33',
            mode='access',
            access_vlan=13,
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result,
            {
                'commands': [
                    'interface ethernet 1/33',
                    'switchport access vlan 13'
                ],
                'changed': True,
                'warnings': []
            }
        )

    def test_cnos_l2_interface_vlan_does_not_exist(self, *args, **kwargs):
        set_module_args(dict(
            name='Ethernet 1/33',
            mode='access',
            access_vlan=10,
        ))
        result = self.execute_module(failed=True)
        self.assertEqual(
            result,
            {
                'msg': 'You are trying to configure a VLAN on an interface '
                       'that\ndoes not exist on the  switch yet!',
                'failed': True,
                'vlan': '10'
            }
        )

    def test_cnos_l2_interface_incorrect_state(self, *args, **kwargs):
        set_module_args(dict(
            name='Ethernet 1/44',
            mode='access',
            access_vlan=10,
        ))
        result = self.execute_module(failed=True)
        self.assertEqual(
            result,
            {
                'msg': 'Ensure interface is configured to be a L2\nport first '
                       'before using this module. You can use\nthe cnos_'
                       'interface module for this.',
                'failed': True
            }
        )

    def test_cnos_l2_interface_trunk(self, *args, **kwargs):
        set_module_args(dict(
            name='Ethernet 1/45',
            mode='trunk',
            native_vlan='12',
            trunk_allowed_vlans='13,12'
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result,
            {
                'commands': [
                    'interface ethernet 1/45',
                    'switchport mode trunk',
                    'switchport trunk allowed vlan 13,12',
                    'switchport trunk native vlan 12'
                ],
                'changed': True,
                'warnings': []
            }
        )

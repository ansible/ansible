#
# (c) 2018 Extreme Networks Inc.
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

from units.compat.mock import patch
from units.modules.utils import set_module_args
from ansible.modules.network.slxos import slxos_l2_interface
from .slxos_module import TestSlxosModule, load_fixture


class TestSlxosL2InterfaceModule(TestSlxosModule):
    module = slxos_l2_interface

    def setUp(self):
        super(TestSlxosL2InterfaceModule, self).setUp()
        self._patch_get_config = patch(
            'ansible.modules.network.slxos.slxos_l2_interface.get_config'
        )
        self._patch_load_config = patch(
            'ansible.modules.network.slxos.slxos_l2_interface.load_config'
        )
        self._patch_run_commands = patch(
            'ansible.modules.network.slxos.slxos_l2_interface.run_commands'
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
        super(TestSlxosL2InterfaceModule, self).tearDown()
        self._patch_get_config.stop()
        self._patch_load_config.stop()
        self._patch_run_commands.stop()

    def load_fixtures(self, commands=None, destination=None, return_values=False):
        side_effects = []

        if not destination:
            destination = self._get_config

        if not commands:
            commands = ['slxos_config_config.cfg']

        for command in commands:
            filename = str(command).replace(' ', '_')
            filename = str(filename).replace('/', '_')
            side_effects.append(load_fixture(filename))

        if return_values is True:
            return side_effects

        destination.side_effect = side_effects
        return None

    def test_slxos_l2_interface_access_vlan(self, *args, **kwargs):
        set_module_args(dict(
            name='Ethernet 0/2',
            mode='access',
            access_vlan=200,
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result,
            {
                'commands': [
                    'interface ethernet 0/2',
                    'switchport access vlan 200'
                ],
                'changed': True,
                'warnings': []
            }
        )

    def test_slxos_l2_interface_vlan_does_not_exist(self, *args, **kwargs):
        set_module_args(dict(
            name='Ethernet 0/2',
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

    def test_slxos_l2_interface_incorrect_state(self, *args, **kwargs):
        set_module_args(dict(
            name='Ethernet 0/3',
            mode='access',
            access_vlan=10,
        ))
        result = self.execute_module(failed=True)
        self.assertEqual(
            result,
            {
                'msg': 'Ensure interface is configured to be a L2\nport first '
                       'before using this module. You can use\nthe slxos_'
                       'interface module for this.',
                'failed': True
            }
        )

    def test_slxos_l2_interface_trunk(self, *args, **kwargs):
        set_module_args(dict(
            name='Ethernet 0/4',
            mode='trunk',
            native_vlan='22',
            trunk_allowed_vlans='200,22'
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result,
            {
                'commands': [
                    'interface ethernet 0/4',
                    'switchport trunk allowed vlan add 200,22',
                    'switchport trunk native vlan 22'
                ],
                'changed': True,
                'warnings': []
            }
        )

    def test_slxos_l2_interface_invalid_argument(self, *args, **kwargs):
        set_module_args(dict(
            name='Ethernet 0/2',
            mode='access',
            access_vlan=10,
            shawshank='Redemption'
        ))
        result = self.execute_module(failed=True)
        self.assertEqual(result['failed'], True)
        self.assertTrue(re.match(
            r'Unsupported parameters for \((basic.py|basic.pyc)\) module: '
            'shawshank Supported parameters include: access_vlan, aggregate, '
            'mode, name, native_vlan, state, trunk_allowed_vlans, trunk_vlans',
            result['msg']
        ))

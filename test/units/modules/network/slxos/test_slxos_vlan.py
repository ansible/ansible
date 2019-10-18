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
from ansible.modules.network.slxos import slxos_vlan
from .slxos_module import TestSlxosModule, load_fixture


class TestSlxosVlanModule(TestSlxosModule):
    module = slxos_vlan

    def setUp(self):
        super(TestSlxosVlanModule, self).setUp()
        self._patch_run_commands = patch(
            'ansible.modules.network.slxos.slxos_vlan.run_commands'
        )
        self._patch_load_config = patch(
            'ansible.modules.network.slxos.slxos_vlan.load_config'
        )

        self._run_commands = self._patch_run_commands.start()
        self._load_config = self._patch_load_config.start()

    def tearDown(self):
        super(TestSlxosVlanModule, self).tearDown()
        self._patch_run_commands.stop()
        self._patch_load_config.stop()

    def load_fixtures(self, commands=None):
        config_file = 'show_vlan_brief'
        self._run_commands.return_value = [load_fixture(config_file)]
        self._load_config.return_value = None

    def test_slxos_vlan_id_with_name(self, *args, **kwargs):
        load_fixture('show_vlan_brief')
        set_module_args(dict(
            vlan_id=100,
            name='ONEHUNDRED'
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result,
            {
                'commands': [
                    'vlan 100',
                    'name ONEHUNDRED'
                ],
                'changed': True
            }
        )

    def test_slxos_vlan_with_members(self, *args, **kwargs):
        set_module_args(dict(
            vlan_id=100,
            name='ONEHUNDRED',
            interfaces=[
                'Ethernet 0/1',
                'Ethernet 0/2'
            ]
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result,
            {
                'commands': [
                    'vlan 100',
                    'name ONEHUNDRED',
                    'interface Ethernet 0/1',
                    'switchport',
                    'switchport mode access',
                    'switchport access vlan 100',
                    'interface Ethernet 0/2',
                    'switchport',
                    'switchport mode access',
                    'switchport access vlan 100'
                ],
                'changed': True
            }
        )

    def test_slxos_vlan_state_absent(self, *args, **kwargs):
        set_module_args(dict(
            vlan_id=200,
            state='absent'
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result,
            {
                'commands': [
                    'no vlan 200'
                ],
                'changed': True
            }
        )

    def test_slxos_vlan_state_absent_nonexistent_vlan(self, *args, **kwargs):
        set_module_args(dict(
            vlan_id=100,
            state='absent'
        ))
        result = self.execute_module()
        self.assertEqual(
            result,
            {
                'commands': [],
                'changed': False
            }
        )

    def test_slxos_interface_invalid_argument(self, *args, **kwargs):
        set_module_args(dict(
            name='Ethernet 0/1',
            shawshank='Redemption'
        ))
        result = self.execute_module(failed=True)
        self.assertEqual(result['failed'], True)
        self.assertTrue(re.match(
            r'Unsupported parameters for \((basic.py|basic.pyc)\) module: '
            'shawshank Supported parameters include: aggregate, delay, '
            'interfaces, name, purge, state, vlan_id',
            result['msg']
        ), 'Result did not match expected output. Got: %s' % result['msg'])

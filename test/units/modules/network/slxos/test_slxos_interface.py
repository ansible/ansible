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
import json

from ansible.compat.tests.mock import patch
from ansible.modules.network.slxos import slxos_interface
from units.modules.utils import set_module_args
from .slxos_module import TestSlxosModule, load_fixture


class TestSlxosInterfaceModule(TestSlxosModule):
    module = slxos_interface

    def setUp(self):
        super(TestSlxosInterfaceModule, self).setUp()
        self._patch_get_config = patch(
            'ansible.modules.network.slxos.slxos_interface.get_config'
        )
        self._patch_load_config = patch(
            'ansible.modules.network.slxos.slxos_interface.load_config'
        )
        self._patch_exec_command = patch(
            'ansible.modules.network.slxos.slxos_interface.exec_command'
        )

        self._get_config = self._patch_get_config.start()
        self._load_config = self._patch_load_config.start()
        self._exec_command = self._patch_exec_command.start()

    def tearDown(self):
        super(TestSlxosInterfaceModule, self).tearDown()
        self._patch_get_config.stop()
        self._patch_load_config.stop()
        self._patch_exec_command.stop()

    def load_fixtures(self, commands=None):
        config_file = 'slxos_config_config.cfg'
        self._get_config.return_value = load_fixture(config_file)
        self._load_config.return_value = None

    def test_slxos_interface_description(self, *args, **kwargs):
        set_module_args(dict(
            name='Ethernet 0/2',
            description='show version'
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result,
            {
                'commands': [
                    'interface Ethernet 0/2',
                    'description show version'
                ],
                'changed': True
            }
        )

    def test_slxos_interface_speed(self, *args, **kwargs):
        set_module_args(dict(
            name='Ethernet 0/2',
            speed=1000
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result,
            {
                'commands': [
                    'interface Ethernet 0/2',
                    'speed 1000'
                ],
                'changed': True
            }
        )

    def test_slxos_interface_mtu(self, *args, **kwargs):
        set_module_args(dict(
            name='Ethernet 0/2',
            mtu=1548
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result,
            {
                'commands': [
                    'interface Ethernet 0/2',
                    'mtu 1548'
                ],
                'changed': True
            }
        )

    def test_slxos_interface_mtu_out_of_range(self, *args, **kwargs):
        set_module_args(dict(
            name='Ethernet 0/2',
            mtu=15000
        ))
        result = self.execute_module(failed=True)
        self.assertEqual(
            result,
            {
                'msg': 'mtu must be between 1548 and 9216',
                'failed': True
            }
        )

    def test_slxos_interface_enabled(self, *args, **kwargs):
        set_module_args(dict(
            name='Ethernet 0/1',
            enabled=True
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result,
            {
                'commands': [
                    'interface Ethernet 0/1',
                    'no shutdown'
                ],
                'changed': True
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
            'shawshank Supported parameters include: aggregate, '
            'delay, description, enabled, mtu, name, neighbors, '
            'rx_rate, speed, state, tx_rate',
            result['msg']
        ))

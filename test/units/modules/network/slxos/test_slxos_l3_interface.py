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
from ansible.modules.network.slxos import slxos_l3_interface
from units.modules.utils import set_module_args
from .slxos_module import TestSlxosModule, load_fixture


class TestSlxosL3InterfaceModule(TestSlxosModule):
    module = slxos_l3_interface

    def setUp(self):
        super(TestSlxosL3InterfaceModule, self).setUp()
        self._patch_get_config = patch(
            'ansible.modules.network.slxos.slxos_l3_interface.get_config'
        )
        self._patch_load_config = patch(
            'ansible.modules.network.slxos.slxos_l3_interface.load_config'
        )

        self._get_config = self._patch_get_config.start()
        self._load_config = self._patch_load_config.start()

    def tearDown(self):
        super(TestSlxosL3InterfaceModule, self).tearDown()
        self._patch_get_config.stop()
        self._patch_load_config.stop()

    def load_fixtures(self, commands=None):
        config_file = 'slxos_config_config.cfg'
        self._get_config.return_value = load_fixture(config_file)
        self._load_config.return_value = None

    def test_slxos_l3_interface_ipv4_address(self, *args, **kwargs):
        set_module_args(dict(
            name='Ethernet 0/2',
            ipv4='192.168.4.1/24'
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result,
            {
                'commands': [
                    'interface Ethernet 0/2',
                    'ip address 192.168.4.1/24'
                ],
                'changed': True
            }
        )

    def test_slxos_l3_interface_absent(self, *args, **kwargs):
        set_module_args(dict(
            name='Ethernet 0/9',
            state='absent'
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result,
            {
                'commands': [
                    'interface Ethernet 0/9',
                    'no ip address',
                    'no ipv6 address'
                ],
                'changed': True
            }
        )

    def test_slxos_l3_interface_invalid_argument(self, *args, **kwargs):
        set_module_args(dict(
            name='Ethernet 0/1',
            shawshank='Redemption'
        ))
        result = self.execute_module(failed=True)
        self.assertEqual(result['failed'], True)
        self.assertTrue(re.match(
            r'Unsupported parameters for \((basic.py|basic.pyc)\) module: '
            'shawshank Supported parameters include: aggregate, ipv4, ipv6, '
            'name, state',
            result['msg']
        ))

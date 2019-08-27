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
from ansible.modules.network.slxos import slxos_linkagg
from .slxos_module import TestSlxosModule, load_fixture


class TestSlxosLinkaggModule(TestSlxosModule):
    module = slxos_linkagg

    def setUp(self):
        super(TestSlxosLinkaggModule, self).setUp()
        self._patch_get_config = patch(
            'ansible.modules.network.slxos.slxos_linkagg.get_config'
        )
        self._patch_load_config = patch(
            'ansible.modules.network.slxos.slxos_linkagg.load_config'
        )

        self._get_config = self._patch_get_config.start()
        self._load_config = self._patch_load_config.start()

    def tearDown(self):
        super(TestSlxosLinkaggModule, self).tearDown()
        self._patch_get_config.stop()
        self._patch_load_config.stop()

    def load_fixtures(self, commands=None):
        config_file = 'slxos_config_config.cfg'
        self._get_config.return_value = load_fixture(config_file)
        self._load_config.return_value = None

    def test_slxos_linkagg_group_present(self, *args, **kwargs):
        set_module_args(dict(
            group='10',
            state='present'
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result,
            {
                'commands': [
                    'interface port-channel 10',
                    'exit'
                ],
                'changed': True
            }
        )

    def test_slxos_linkagg_group_members_active(self, *args, **kwargs):
        set_module_args(dict(
            group='10',
            mode='active',
            members=[
                'Ethernet 0/1',
                'Ethernet 0/2'
            ]
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result,
            {
                'commands': [
                    'interface port-channel 10',
                    'exit',
                    'interface Ethernet 0/1',
                    'channel-group 10 mode active',
                    'interface Ethernet 0/2',
                    'channel-group 10 mode active'
                ],
                'changed': True
            }
        )

    def test_slxos_linkagg_group_member_removal(self, *args, **kwargs):
        set_module_args(dict(
            group='20',
            mode='active',
            members=[
                'Ethernet 0/10',
            ]
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result,
            {
                'commands': [
                    'interface port-channel 20',
                    'exit',
                    'interface Ethernet 0/11',
                    'no channel-group'
                ],
                'changed': True
            }
        )

    def test_slxos_linkagg_group_members_absent(self, *args, **kwargs):
        set_module_args(dict(
            group='20',
            state='absent'
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result,
            {
                'commands': [
                    'no interface port-channel 20'
                ],
                'changed': True
            }
        )
        set_module_args(dict(
            group='10',
            state='absent'
        ))
        result = self.execute_module(changed=False)
        self.assertEqual(
            result,
            {
                'commands': [],
                'changed': False
            }
        )

    def test_slxos_linkagg_invalid_argument(self, *args, **kwargs):
        set_module_args(dict(
            group='10',
            shawshank='Redemption'
        ))
        result = self.execute_module(failed=True)
        self.assertEqual(result['failed'], True)
        self.assertTrue(re.match(
            r'Unsupported parameters for \((basic.pyc|basic.py)\) module: '
            'shawshank Supported parameters include: aggregate, group, '
            'members, mode, purge, state',
            result['msg']
        ))

#
# (c) 2018 Red Hat Inc.
# Copyright (C) 2017 Lenovo.
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

from units.compat.mock import patch
from ansible.modules.network.cnos import cnos_linkagg
from units.modules.utils import set_module_args
from .cnos_module import TestCnosModule, load_fixture


class TestCnosLinkaggModule(TestCnosModule):
    module = cnos_linkagg

    def setUp(self):
        super(TestCnosLinkaggModule, self).setUp()
        self._patch_get_config = patch(
            'ansible.modules.network.cnos.cnos_linkagg.get_config'
        )
        self._patch_load_config = patch(
            'ansible.modules.network.cnos.cnos_linkagg.load_config'
        )

        self._get_config = self._patch_get_config.start()
        self._load_config = self._patch_load_config.start()

    def tearDown(self):
        super(TestCnosLinkaggModule, self).tearDown()
        self._patch_get_config.stop()
        self._patch_load_config.stop()

    def load_fixtures(self, commands=None):
        config_file = 'cnos_linkagg_config.cfg'
        self._get_config.return_value = load_fixture(config_file)
        self._load_config.return_value = None

    def test_cnos_linkagg_group_present(self, *args, **kwargs):
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

    def test_cnos_linkagg_group_members_active(self, *args, **kwargs):
        set_module_args(dict(
            group='10',
            mode='active',
            members=[
                'Ethernet 1/33',
                'Ethernet 1/44'
            ]
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result,
            {
                'commands': [
                    'interface port-channel 10',
                    'exit',
                    'interface Ethernet 1/33',
                    'channel-group 10 mode active',
                    'interface Ethernet 1/44',
                    'channel-group 10 mode active'
                ],
                'changed': True
            }
        )

    def test_cnos_linkagg_group_member_removal(self, *args, **kwargs):
        set_module_args(dict(
            group='20',
            mode='active',
            members=[
                'Ethernet 1/10',
            ]
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result,
            {
                'commands': [
                    'interface port-channel 20',
                    'exit',
                    'interface Ethernet 1/10',
                    'channel-group 20 mode active'
                ],
                'changed': True
            }
        )

    def test_cnos_linkagg_group_members_absent(self, *args, **kwargs):
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

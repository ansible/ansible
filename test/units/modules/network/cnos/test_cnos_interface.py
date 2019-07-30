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
from ansible.modules.network.cnos import cnos_interface
from units.modules.utils import set_module_args
from .cnos_module import TestCnosModule, load_fixture


class TestCnosInterfaceModule(TestCnosModule):
    module = cnos_interface

    def setUp(self):
        super(TestCnosInterfaceModule, self).setUp()
        self._patch_get_config = patch(
            'ansible.modules.network.cnos.cnos_interface.get_config'
        )
        self._patch_load_config = patch(
            'ansible.modules.network.cnos.cnos_interface.load_config'
        )
        self._patch_exec_command = patch(
            'ansible.modules.network.cnos.cnos_interface.exec_command'
        )

        self._get_config = self._patch_get_config.start()
        self._load_config = self._patch_load_config.start()
        self._exec_command = self._patch_exec_command.start()

    def tearDown(self):
        super(TestCnosInterfaceModule, self).tearDown()
        self._patch_get_config.stop()
        self._patch_load_config.stop()
        self._patch_exec_command.stop()

    def load_fixtures(self, commands=None):
        config_file = 'cnos_config_config.cfg'
        self._get_config.return_value = load_fixture(config_file)
        self._load_config.return_value = None

    def test_cnos_interface_description(self, *args, **kwargs):
        set_module_args(dict(
            name='Ethernet1/2',
            description='show version'
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result,
            {
                'commands': [
                    'interface Ethernet1/2',
                    'description show version',
                    'duplex auto'
                ],
                'changed': True
            }
        )

    def test_cnos_interface_speed(self, *args, **kwargs):
        set_module_args(dict(
            name='Ethernet1/2',
            speed=1000
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result,
            {
                'commands': [
                    'interface Ethernet1/2',
                    'speed 1000',
                    'duplex auto'
                ],
                'changed': True
            }
        )

    def test_cnos_interface_mtu(self, *args, **kwargs):
        set_module_args(dict(
            name='Ethernet1/2',
            mtu=1548
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result,
            {
                'commands': [
                    'interface Ethernet1/2',
                    'duplex auto',
                    'mtu 1548'
                ],
                'changed': True
            }
        )

    def test_cnos_interface_mtu_out_of_range(self, *args, **kwargs):
        set_module_args(dict(
            name='Ethernet0/2',
            mtu=15000
        ))
        result = self.execute_module(failed=True)
        self.assertEqual(
            result,
            {
                'msg': 'mtu must be between 64 and 9216',
                'failed': True
            }
        )

    def test_cnos_interface_enabled(self, *args, **kwargs):
        set_module_args(dict(
            name='Ethernet1/44',
            enabled=True
        ))
        result = self.execute_module(changed=True)
        self.assertEqual(
            result,
            {
                'commands': [
                    'interface Ethernet1/44',
                    'duplex auto',
                    'no shutdown'
                ],
                'changed': True
            }
        )

#
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

from ansible.compat.tests.mock import patch
from ansible.modules.network.ios import ios_vrf
from .ios_module import TestIosModule, load_fixture, set_module_args


class TestIosVrfModule(TestIosModule):

    module = ios_vrf

    def setUp(self):
        self.mock_get_config = patch('ansible.modules.network.ios.ios_vrf.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.ios.ios_vrf.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        self.mock_get_config.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None):
        self.get_config.return_value = load_fixture('ios_vrf_config.cfg')
        self.load_config.return_value = None

    def test_ios_vrf_name(self):
        set_module_args(dict(name='test_4'))
        commands = ['vrf definition test_4']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_ios_vrf_name_unchanged(self):
        set_module_args(dict(name='test_1', rd='1:100', description='test vrf 1'))
        self.execute_module()

    def test_ios_vrf_description(self):
        set_module_args(dict(name='test_1', description='test string'))
        commands = ['vrf definition test_1', 'description test string']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_ios_vrf_rd(self):
        set_module_args(dict(name='test_1', rd='2:100'))
        commands = ['vrf definition test_1', 'rd 2:100']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_ios_vrf_interfaces(self):
        set_module_args(dict(name='test_1', interfaces=['Ethernet1']))
        commands = ['interface Ethernet2', 'no vrf forwarding test_1',
                    'interface Ethernet1', 'vrf forwarding test_1',
                    'ip address 1.2.3.4/5']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_ios_vrf_state_absent(self):
        set_module_args(dict(name='test_1', state='absent'))
        commands = ['no vrf definition test_1']
        self.execute_module(changed=True, commands=commands)

    def test_ios_vrf_purge_all(self):
        set_module_args(dict(purge=True))
        commands = ['no vrf definition test_1', 'no vrf definition test_2',
                    'no vrf definition test_3']
        self.execute_module(changed=True, commands=commands)

    def test_ios_vrf_purge_all_but_one(self):
        set_module_args(dict(name='test_1', purge=True))
        commands = ['no vrf definition test_2', 'no vrf definition test_3']
        self.execute_module(changed=True, commands=commands)

    def test_ios_vrfs_no_purge(self):
        vrfs = [{'name': 'test_1'}, {'name': 'test_4'}]
        set_module_args(dict(vrfs=vrfs))
        commands = ['vrf definition test_4']
        self.execute_module(changed=True, commands=commands)

    def test_ios_vrfs_purge(self):
        vrfs = [{'name': 'test_1'}, {'name': 'test_4'}]
        set_module_args(dict(vrfs=vrfs, purge=True))
        commands = ['no vrf definition test_2', 'no vrf definition test_3',
                    'vrf definition test_4']
        self.execute_module(changed=True, commands=commands)

    def test_ios_vrfs_global_arg(self):
        vrfs = [{'name': 'test_1'}, {'name': 'test_2'}]
        set_module_args(dict(vrfs=vrfs, description='test string'))
        commands = ['vrf definition test_1', 'description test string',
                    'vrf definition test_2', 'description test string']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_ios_vrfs_local_override_description(self):
        vrfs = [{'name': 'test_1', 'description': 'test vrf 1'},
                {'name': 'test_2'}]
        set_module_args(dict(vrfs=vrfs, description='test string'))
        commands = ['vrf definition test_2', 'description test string']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_ios_vrfs_local_override_state(self):
        vrfs = [{'name': 'test_1', 'state': 'absent'},
                {'name': 'test_2'}]
        set_module_args(dict(vrfs=vrfs, description='test string'))
        commands = ['no vrf definition test_1', 'vrf definition test_2',
                    'description test string']
        self.execute_module(changed=True, commands=commands, sort=False)



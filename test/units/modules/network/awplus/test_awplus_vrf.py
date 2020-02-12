#
# (c) 2020 Allied Telesis
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

from units.compat.mock import patch
from ansible.modules.network.awplus import awplus_vrf
from units.modules.utils import set_module_args
from .awplus_module import TestAwplusModule, load_fixture


class TestAwplusVrfModule(TestAwplusModule):
    module = awplus_vrf

    def setUp(self):
        super(TestAwplusVrfModule, self).setUp()

        self.mock_get_config = patch(
            'ansible.modules.network.awplus.awplus_vrf.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch(
            'ansible.modules.network.awplus.awplus_vrf.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_run_commands = patch(
            'ansible.modules.network.awplus.awplus_vrf.get_intf_info')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestAwplusVrfModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None, transport='cli'):
        self.get_config.return_value = load_fixture('awplus_vrf_config.cfg')
        self.load_config.return_value = None

        def load_from_file(*args, **kwargs):
            return load_fixture('awplus_vrf_intf.cfg')

        self.run_commands.side_effect = load_from_file

    def test_awplus_vrf_name(self):
        set_module_args(dict(name='test_4'))
        commands = ['ip vrf test_4']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_awplus_vrf_name_unchanged(self):
        set_module_args(dict(name='test_1'))
        self.execute_module(changed=False)

    def test_awplus_vrf_description(self):
        set_module_args(dict(name='test_1', description='test string'))
        commands = ['ip vrf test_1', 'description test string']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_awplus_vrf_rd(self):
        set_module_args(dict(name='test_1', rd='2:100'))
        commands = ['ip vrf test_1', 'rd 2:100']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_awplus_vrf_interfaces(self):
        set_module_args(dict(name='test_1', interfaces=['vlan2', 'vlan100']))
        commands = ['interface lo2', 'no ip vrf test_1',
                    'interface vlan100', 'ip vrf forwarding test_1']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_awplus_vrf_state_absent(self):
        set_module_args(dict(name='test_1', state='absent'))
        commands = ['no ip vrf test_1']
        self.execute_module(changed=True, commands=commands)

    def test_awplus_vrf_purge_all(self):
        set_module_args(dict(purge=True))
        commands = ['no ip vrf test_1', 'no ip vrf red']
        self.execute_module(changed=True, commands=commands)

    def test_awplus_vrf_purge_all_but_one(self):
        set_module_args(dict(name='test_1', purge=True))
        commands = ['no ip vrf red']
        self.execute_module(changed=True, commands=commands)

    def test_awplus_vrfs_no_purge(self):
        vrfs = [{'name': 'test_1'}, {'name': 'red'}]
        set_module_args(dict(vrfs=vrfs))
        commands = []
        self.execute_module(changed=False, commands=commands)

    def test_awplus_vrfs_global_arg(self):
        vrfs = [{'name': 'test_1'}, {'name': 'red'}]
        set_module_args(dict(vrfs=vrfs, description='test string'))
        commands = ['ip vrf test_1', 'description test string',
                    'ip vrf red', 'description test string']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_awplus_vrfs_local_override_description(self):
        vrfs = [{'name': 'test_1', 'description': 'test vrf 1'},
                {'name': 'test_2'}]
        set_module_args(dict(vrfs=vrfs, description='test string'))
        commands = ['ip vrf test_1', 'description test vrf 1',
                    'ip vrf test_2', 'description test string']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_awplus_vrfs_local_override_state(self):
        vrfs = [{'name': 'test_1', 'state': 'absent'}, {'name': 'run'}]
        set_module_args(dict(vrfs=vrfs, description='test string'))
        commands = ['no ip vrf test_1',
                    'ip vrf run', 'description test string']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_awplus_vrf_route_both(self):
        set_module_args(dict(name='test_5', rd='2:100',
                             route_both=['2:100', '3:100']))
        commands = ['ip vrf test_5', 'rd 2:100',
                    'route-target both 2:100', 'route-target both 3:100']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_awplus_vrf_route_import(self):
        set_module_args(dict(name='test_1', rd='3:100',
                             route_import=['3:100', '4:100']))
        commands = ['ip vrf test_1', 'rd 3:100', 'route-target import 3:100',
                    'route-target import 4:100']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_awplus_vrf_route_export(self):
        set_module_args(dict(name='test_7', rd='4:100',
                             route_export=['3:100', '4:100']))
        commands = ['ip vrf test_7', 'rd 4:100', 'route-target export 3:100',
                    'route-target export 4:100']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_awplus_vrf_route_both_mixed(self):
        set_module_args(dict(name='test_8', rd='5:100', route_both=[
                        '3:100', '4:100'], route_export=['3:100', '4:100']))
        self.execute_module(changed=True)

    def test_awplus_vrf_all_route_both_idempotent(self):
        set_module_args(dict(name='red', rd='2:100', route_both=['2:100']))
        self.execute_module(changed=False, commands=[], sort=False)

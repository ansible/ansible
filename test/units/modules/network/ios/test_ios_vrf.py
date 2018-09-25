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

from ansible.compat.tests.mock import patch
from ansible.modules.network.ios import ios_vrf
from units.modules.utils import set_module_args
from .ios_module import TestIosModule, load_fixture


class TestIosVrfModule(TestIosModule):
    module = ios_vrf

    def setUp(self):
        super(TestIosVrfModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.ios.ios_vrf.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.ios.ios_vrf.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_exec_command = patch('ansible.modules.network.ios.ios_vrf.exec_command')
        self.exec_command = self.mock_exec_command.start()

    def tearDown(self):
        super(TestIosVrfModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_exec_command.stop()

    def load_fixtures(self, commands=None):
        self.get_config.return_value = load_fixture('ios_vrf_config.cfg')
        self.exec_command.return_value = (0, load_fixture('ios_vrf_config.cfg').strip(), None)
        self.load_config.return_value = None

    def test_ios_vrf_name(self):
        set_module_args(dict(name='test_4'))
        commands = ['vrf definition test_4', 'address-family ipv4', 'exit', 'address-family ipv6', 'exit']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_ios_vrf_name_unchanged(self):
        set_module_args(dict(name='test_1', rd='1:100', description='test vrf 1'))
        self.execute_module()

    def test_ios_vrf_description(self):
        set_module_args(dict(name='test_1', description='test string'))
        commands = ['vrf definition test_1', 'address-family ipv4', 'exit', 'address-family ipv6', 'exit', 'description test string']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_ios_vrf_rd(self):
        set_module_args(dict(name='test_1', rd='2:100'))
        commands = ['vrf definition test_1', 'address-family ipv4', 'exit', 'address-family ipv6', 'exit', 'rd 2:100']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_ios_vrf_interfaces(self):
        set_module_args(dict(name='test_1', interfaces=['Ethernet1']))
        commands = ['interface Ethernet2', 'no vrf forwarding test_1', 'interface Ethernet1', 'vrf forwarding test_1', 'ip address 1.2.3.4/5']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_ios_vrf_state_absent(self):
        set_module_args(dict(name='test_1', state='absent'))
        commands = ['no vrf definition test_1']
        self.execute_module(changed=True, commands=commands)

    def test_ios_vrf_purge_all(self):
        set_module_args(dict(purge=True))
        commands = ['no vrf definition test_1', 'no vrf definition test_2', 'no vrf definition test_3', 'no vrf definition test_17',
                    'no vrf definition test_18', 'no vrf definition test_19']
        self.execute_module(changed=True, commands=commands)

    def test_ios_vrf_purge_all_but_one(self):
        set_module_args(dict(name='test_1', purge=True))
        commands = ['no vrf definition test_2', 'no vrf definition test_3', 'no vrf definition test_17', 'no vrf definition test_18',
                    'no vrf definition test_19']
        self.execute_module(changed=True, commands=commands)

    def test_ios_vrfs_no_purge(self):
        vrfs = [{'name': 'test_1'}, {'name': 'test_4'}]
        set_module_args(dict(vrfs=vrfs))
        commands = ['vrf definition test_4', 'address-family ipv4', 'exit', 'address-family ipv6', 'exit']
        self.execute_module(changed=True, commands=commands)

    def test_ios_vrfs_purge(self):
        vrfs = [{'name': 'test_1'}, {'name': 'test_4'}]
        set_module_args(dict(vrfs=vrfs, purge=True))
        commands = ['vrf definition test_4', 'address-family ipv4', 'exit', 'address-family ipv6', 'exit', 'no vrf definition test_2',
                    'no vrf definition test_3', 'no vrf definition test_17', 'no vrf definition test_18', 'no vrf definition test_19']
        self.execute_module(changed=True, commands=commands)

    def test_ios_vrfs_global_arg(self):
        vrfs = [{'name': 'test_1'}, {'name': 'test_2'}]
        set_module_args(dict(vrfs=vrfs, description='test string'))
        commands = ['vrf definition test_1', 'address-family ipv4', 'exit', 'address-family ipv6', 'exit', 'description test string', 'vrf definition test_2',
                    'address-family ipv4', 'exit', 'address-family ipv6', 'exit', 'description test string']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_ios_vrfs_local_override_description(self):
        vrfs = [{'name': 'test_1', 'description': 'test vrf 1'}, {'name': 'test_2'}]
        set_module_args(dict(vrfs=vrfs, description='test string'))
        commands = ['vrf definition test_2', 'address-family ipv4', 'exit', 'address-family ipv6', 'exit', 'description test string']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_ios_vrfs_local_override_state(self):
        vrfs = [{'name': 'test_1', 'state': 'absent'}, {'name': 'test_2'}]
        set_module_args(dict(vrfs=vrfs, description='test string'))
        commands = ['no vrf definition test_1', 'vrf definition test_2', 'address-family ipv4', 'exit', 'address-family ipv6', 'exit',
                    'description test string']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_ios_vrf_route_both(self):
        set_module_args(dict(name='test_5', rd='2:100', route_both=['2:100', '3:100']))
        commands = ['vrf definition test_5', 'address-family ipv4', 'exit', 'address-family ipv6', 'exit', 'rd 2:100', 'route-target import 2:100',
                    'route-target import 3:100', 'route-target export 2:100', 'route-target export 3:100']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_ios_vrf_route_import(self):
        set_module_args(dict(name='test_6', rd='3:100', route_import=['3:100', '4:100']))
        commands = ['vrf definition test_6', 'address-family ipv4', 'exit', 'address-family ipv6', 'exit', 'rd 3:100', 'route-target import 3:100',
                    'route-target import 4:100']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_ios_vrf_route_export(self):
        set_module_args(dict(name='test_7', rd='4:100', route_export=['3:100', '4:100']))
        commands = ['vrf definition test_7', 'address-family ipv4', 'exit', 'address-family ipv6', 'exit', 'rd 4:100', 'route-target export 3:100',
                    'route-target export 4:100']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_ios_vrf_route_both_mixed(self):
        set_module_args(dict(name='test_8', rd='5:100', route_both=['3:100', '4:100'], route_export=['3:100', '4:100']))
        self.execute_module(changed=True)

    def test_ios_vrf_route_both_ipv4(self):
        set_module_args(dict(name='test_9', rd='168.0.0.9:100', route_both_ipv4=['168.0.0.9:100', '3:100']))
        commands = ['vrf definition test_9', 'address-family ipv4', 'exit', 'address-family ipv6', 'exit', 'rd 168.0.0.9:100', 'address-family ipv4',
                    'route-target import 168.0.0.9:100', 'route-target import 3:100', 'exit-address-family', 'address-family ipv4',
                    'route-target export 168.0.0.9:100', 'route-target export 3:100', 'exit-address-family']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_ios_vrf_route_import_ipv4(self):
        set_module_args(dict(name='test_10', rd='168.0.0.10:100', route_import_ipv4=['168.0.0.10:100', '3:100']))
        commands = ['vrf definition test_10', 'address-family ipv4', 'exit', 'address-family ipv6', 'exit', 'rd 168.0.0.10:100', 'address-family ipv4',
                    'route-target import 168.0.0.10:100', 'route-target import 3:100', 'exit-address-family']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_ios_vrf_route_export_ipv4(self):
        set_module_args(dict(name='test_11', rd='168.0.0.11:100', route_export_ipv4=['168.0.0.11:100', '3:100']))
        commands = ['vrf definition test_11', 'address-family ipv4', 'exit', 'address-family ipv6', 'exit', 'rd 168.0.0.11:100', 'address-family ipv4',
                    'route-target export 168.0.0.11:100', 'route-target export 3:100', 'exit-address-family']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_ios_vrf_route_both_ipv4_mixed(self):
        set_module_args(dict(name='test_12', rd='168.0.0.12:100', route_both_ipv4=['168.0.0.12:100', '3:100'], route_export_ipv4=['168.0.0.15:100', '6:100']))
        self.execute_module(changed=True)

    def test_ios_vrf_route_both_ipv6(self):
        set_module_args(dict(name='test_13', rd='2:100', route_both_ipv6=['2:100', '168.0.0.13:100']))
        commands = ['vrf definition test_13', 'address-family ipv4', 'exit', 'address-family ipv6', 'exit', 'rd 2:100', 'address-family ipv6',
                    'route-target import 2:100', 'route-target import 168.0.0.13:100', 'exit-address-family', 'address-family ipv6',
                    'route-target export 2:100', 'route-target export 168.0.0.13:100', 'exit-address-family']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_ios_vrf_route_import_ipv6(self):
        set_module_args(dict(name='test_14', rd='3:100', route_import_ipv6=['3:100', '168.0.0.14:100']))
        commands = ['vrf definition test_14', 'address-family ipv4', 'exit', 'address-family ipv6', 'exit', 'rd 3:100', 'address-family ipv6',
                    'route-target import 3:100', 'route-target import 168.0.0.14:100', 'exit-address-family']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_ios_vrf_route_export_ipv6(self):
        set_module_args(dict(name='test_15', rd='4:100', route_export_ipv6=['168.0.0.15:100', '4:100']))
        commands = ['vrf definition test_15', 'address-family ipv4', 'exit', 'address-family ipv6', 'exit', 'rd 4:100', 'address-family ipv6',
                    'route-target export 168.0.0.15:100', 'route-target export 4:100', 'exit-address-family']
        self.execute_module(changed=True, commands=commands, sort=False)

    def test_ios_vrf_route_both_ipv6_mixed(self):
        set_module_args(dict(name='test_16', rd='5:100', route_both_ipv6=['168.0.0.9:100', '4:100'], route_export_ipv6=['168.0.0.12:100', '6:100']))
        self.execute_module(changed=True)

    def test_ios_vrf_route_both_ipv6_mixed_idempotent(self):
        set_module_args(dict(name='test_17', rd='2:100', route_import_ipv6=['168.0.0.14:100'], route_both_ipv6=['2:100', '168.0.0.13:100'],
                             route_export_ipv6=['168.0.0.15:100', '4:100']))
        self.execute_module(changed=False, commands=[], sort=False)

    def test_ios_vrf_route_both_ipv4_mixed_idempotent(self):
        set_module_args(dict(name='test_18', rd='168.0.0.9:100', route_import_ipv4=['168.0.0.10:600'], route_export_ipv4=['168.0.0.10:100'],
                             route_both_ipv4=['168.0.0.9:100', '3:100']))
        self.execute_module(changed=False, commands=[], sort=False)

    def test_ios_vrf_all_route_both_idempotent(self):
        set_module_args(dict(name='test_19', rd='10:700', route_both=['2:100', '2:101'], route_export=['2:102', '2:103'], route_import=['2:104', '2:105'],
                             route_both_ipv4=['2:100', '2:101'], route_export_ipv4=['2:102', '2:103'], route_import_ipv4=['2:104', '2:105'],
                             route_both_ipv6=['2:100', '2:101'], route_export_ipv6=['2:102', '2:103'], route_import_ipv6=['2:104', '2:105']))
        self.execute_module(changed=False, commands=[], sort=False)

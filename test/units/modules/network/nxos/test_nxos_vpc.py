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

from units.compat.mock import patch
from ansible.modules.network.nxos import nxos_vpc
from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosVpcModule(TestNxosModule):

    module = nxos_vpc

    def setUp(self):
        super(TestNxosVpcModule, self).setUp()

        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_vpc.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_vpc.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_run_commands = patch('ansible.modules.network.nxos.nxos_vpc.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestNxosVpcModule, self).tearDown()
        self.mock_get_config.stop()
        self.mock_load_config.stop()
        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None, device=''):
        def load_from_file(*args, **kwargs):
            module, commands = args
            output = list()

            for command in commands:
                filename = str(command).split(' | ')[0].replace(' ', '_')
                output.append(load_fixture('nxos_vpc', filename))
            return output

        def vrf_load_from_file(*args, **kwargs):
            """Load vpc output for vrf tests"""
            module, commands = args
            output = list()
            for command in commands:
                filename = 'vrf_test_' + str(command).split(' | ')[0].replace(' ', '_')
                output.append(load_fixture('nxos_vpc', filename))
            return output

        self.load_config.return_value = None
        if device == '_vrf_test':
            self.run_commands.side_effect = vrf_load_from_file
        else:
            self.run_commands.side_effect = load_from_file

    def test_nxos_vpc_present(self):
        set_module_args(dict(domain=100, role_priority=32667, system_priority=2000,
                             pkl_dest='192.168.100.4', pkl_src='10.1.100.20',
                             peer_gw=True, auto_recovery=True))
        self.execute_module(changed=True, commands=[
            'vpc domain 100', 'terminal dont-ask', 'role priority 32667', 'system-priority 2000',
            'peer-keepalive destination 192.168.100.4 source 10.1.100.20',
            'peer-gateway', 'auto-recovery',
        ])

    def test_nxos_vpc_vrf_1(self):
        # No vrf -> vrf 'default'
        set_module_args(dict(
            domain=100,
            pkl_dest='192.168.1.1',
            pkl_src='10.1.1.1',
            pkl_vrf='default',
        ))
        self.execute_module(changed=True, commands=[
            'vpc domain 100',
            'peer-keepalive destination 192.168.1.1 source 10.1.1.1 vrf default'
        ])

    def test_nxos_vpc_vrf_2(self):
        # vrf 'my_vrf'-> vrf 'test-vrf'
        # All pkl commands should be present
        self.get_config.return_value = load_fixture('nxos_vpc', 'vrf_test_vpc_config')
        set_module_args(dict(
            domain=100,
            pkl_dest='192.168.1.1',
            pkl_src='10.1.1.1',
            pkl_vrf='test-vrf',
        ))
        self.execute_module(changed=True, device='_vrf_test', commands=[
            'vpc domain 100',
            'peer-keepalive destination 192.168.1.1 source 10.1.1.1 vrf test-vrf'
        ])

    def test_nxos_vpc_vrf_3(self):
        # vrf 'my_vrf' -> vrf 'obviously-different-vrf'
        # Existing pkl_src should be retained even though playbook does not specify it
        self.get_config.return_value = load_fixture('nxos_vpc', 'vrf_test_vpc_config')
        set_module_args(dict(
            domain=100,
            pkl_dest='192.168.1.1',
            pkl_vrf='obviously-different-vrf'
        ))
        self.execute_module(changed=True, device='_vrf_test', commands=[
            'vpc domain 100',
            'peer-keepalive destination 192.168.1.1 source 10.1.1.1 vrf obviously-different-vrf'
        ])

    def test_nxos_vpc_vrf_4(self):
        # vrf 'my_vrf'-> vrf 'management'
        # 'management' is the default value for vrf, it will not nvgen
        self.get_config.return_value = load_fixture('nxos_vpc', 'vrf_test_vpc_config')
        set_module_args(dict(
            domain=100,
            pkl_dest='192.168.1.1',
            pkl_vrf='management',
        ))
        self.execute_module(changed=True, device='_vrf_test', commands=[
            'vpc domain 100',
            'peer-keepalive destination 192.168.1.1 source 10.1.1.1 vrf management'
        ])

    def test_nxos_vpc_vrf_5(self):
        # vrf 'my_vrf' -> vrf 'my_vrf' (idempotence)
        self.get_config.return_value = load_fixture('nxos_vpc', 'vrf_test_vpc_config')
        set_module_args(dict(
            domain=100,
            pkl_dest='192.168.1.1',
            pkl_src='10.1.1.1',
            pkl_vrf='my_vrf',
        ))
        self.execute_module(changed=False, device='_vrf_test')

    def test_nxos_vpc_vrf_6(self):
        # vrf 'my_vrf' -> absent tests
        self.get_config.return_value = load_fixture('nxos_vpc', 'vrf_test_vpc_config')
        set_module_args(dict(
            domain=100,
            state='absent'
        ))
        self.execute_module(changed=True, device='_vrf_test', commands=[
            'terminal dont-ask',
            'no vpc domain 100',
        ])

    def test_nxos_vpc_vrf_7(self):
        # dest 192.168.1.1 source 10.1.1.1 vrf my_vrf -> (dest only) (idempotence)
        # pkl_src/pkl_vrf not in playbook but exists on device.
        self.get_config.return_value = load_fixture('nxos_vpc', 'vrf_test_vpc_config')
        set_module_args(dict(
            domain=100,
            pkl_dest='192.168.1.1',
        ))
        self.execute_module(changed=False, device='_vrf_test')

    def test_nxos_vpc_vrf_8(self):
        # dest 192.168.1.1 source 10.1.1.1 vrf my_vrf -> (optional vrf) (idempotence)
        # pkl_src not in playbook but exists on device.
        self.get_config.return_value = load_fixture('nxos_vpc', 'vrf_test_vpc_config')
        set_module_args(dict(
            domain=100,
            pkl_dest='192.168.1.1',
            pkl_vrf='my_vrf',
        ))
        self.execute_module(changed=False, device='_vrf_test')

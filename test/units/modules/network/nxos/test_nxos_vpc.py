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

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_vpc.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_run_commands = patch('ansible.modules.network.nxos.nxos_vpc.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestNxosVpcModule, self).tearDown()
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

        self.load_config.return_value = None
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

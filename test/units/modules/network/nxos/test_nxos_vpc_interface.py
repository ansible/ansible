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
from ansible.modules.network.nxos import nxos_vpc_interface
from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosVpcModule(TestNxosModule):

    module = nxos_vpc_interface

    def setUp(self):
        super(TestNxosVpcModule, self).setUp()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_vpc_interface.load_config')
        self.load_config = self.mock_load_config.start()

        self.mock_get_config = patch('ansible.modules.network.nxos.nxos_vpc_interface.get_config')
        self.get_config = self.mock_get_config.start()

        self.mock_run_commands = patch('ansible.modules.network.nxos.nxos_vpc_interface.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestNxosVpcModule, self).tearDown()
        self.mock_load_config.stop()
        self.mock_get_config.stop()
        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None, device=''):
        def load_from_file(*args, **kwargs):
            module, commands = args
            output = list()
            for command in commands:
                filename = str(command).split(' | ')[0].replace(' ', '_')
                output.append(load_fixture('nxos_vpc_interface', filename))
            return output

        self.run_commands.side_effect = load_from_file
        self.load_config.return_value = None

    def test_nxos_vpc_interface_absent(self):
        set_module_args(dict(portchannel=10, vpc=100, state='absent'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['interface port-channel10', 'no vpc'])

    def test_nxos_vpc_interface_present(self):
        set_module_args(dict(portchannel=20, vpc=200, state='present'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['interface port-channel20', 'vpc 200'])

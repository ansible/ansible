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
__metacl_interfaceass__ = type

import json

from ansible.compat.tests.mock import patch
from ansible.modules.network.nxos import nxos_acl_interface
from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosAclInterfaceModule(TestNxosModule):

    module = nxos_acl_interface

    def setUp(self):
        self.mock_run_commands = patch('ansible.modules.network.nxos.nxos_acl_interface.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_acl_interface.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        self.mock_run_commands.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, device=''):
        def load_from_file(*args, **kwargs):
            module, commands = args
            output = list()

            for item in commands:
                try:
                    command = item['command']
                except ValueError:
                    command = item
                filename = '%s.txt' % str(command).split(' | ')[0].replace(' ', '_')
                output.append(load_fixture('nxos_acl_interface', filename))
            return output

        self.run_commands.side_effect = load_from_file
        self.load_config.return_value = None

    def test_nxos_acl_interface(self):
        set_module_args(dict(name='ANSIBLE', interface='ethernet1/41', direction='egress'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['interface ethernet1/41', 'ip access-group ANSIBLE out'])

    def test_nxos_acl_interface_remove(self):
        set_module_args(dict(name='copp-system-p-acl-bgp', interface='ethernet1/41',
                             direction='egress', state='absent'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['interface ethernet1/41', 'no ip access-group copp-system-p-acl-bgp out'])

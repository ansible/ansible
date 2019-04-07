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

from units.compat.mock import patch
from ansible.modules.network.nxos import nxos_acl
from .nxos_module import TestNxosModule, load_fixture, set_module_args


class TestNxosAclModule(TestNxosModule):

    module = nxos_acl

    def setUp(self):
        super(TestNxosAclModule, self).setUp()

        self.mock_run_commands = patch('ansible.modules.network.nxos.nxos_acl.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_load_config = patch('ansible.modules.network.nxos.nxos_acl.load_config')
        self.load_config = self.mock_load_config.start()

    def tearDown(self):
        super(TestNxosAclModule, self).tearDown()
        self.mock_run_commands.stop()
        self.mock_load_config.stop()

    def load_fixtures(self, commands=None, device=''):
        def load_from_file(*args, **kwargs):
            module, commands = args
            output = list()

            for item in commands:
                try:
                    obj = json.loads(item)
                    command = obj['command']
                except ValueError:
                    command = item
                filename = '%s.txt' % str(command).split(' | ')[0].replace(' ', '_')
                output.append(load_fixture('nxos_acl', filename))
            return output

        self.run_commands.side_effect = load_from_file
        self.load_config.return_value = None

    def test_nxos_acl(self):
        set_module_args(dict(name='ANSIBLE', seq=10, action='permit',
                             proto='tcp', src='192.0.2.1/24', dest='any'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['ip access-list ANSIBLE', '10 permit tcp 192.0.2.1/24 any'])

    def test_nxos_acl_remove(self):
        set_module_args(dict(name='copp-system-p-acl-bgp', seq=10, state='absent'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['ip access-list copp-system-p-acl-bgp', 'no 10'])

    def test_nxos_acl_delete_acl(self):
        set_module_args(dict(name='copp-system-p-acl-bgp', state='delete_acl'))
        result = self.execute_module(changed=True)
        self.assertEqual(result['commands'], ['no ip access-list copp-system-p-acl-bgp'])

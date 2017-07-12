# (c) 2017 Red Hat Inc.
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
from ansible.modules.network.junos import junos_command
from .junos_module import TestJunosModule, load_fixture, set_module_args

RPC_CLI_MAP = {
    'get-software-information': 'show version'
}


class TestJunosCommandModule(TestJunosModule):

    module = junos_command

    def setUp(self):
        self.mock_send_request = patch('ansible.modules.network.junos.junos_command.send_request')
        self.send_request = self.mock_send_request.start()

    def tearDown(self):
        self.mock_send_request.stop()

    def load_fixtures(self, commands=None, format='text', changed=False):
        def load_from_file(*args, **kwargs):
            module, element = args

            if element.text:
                path = str(element.text)
            else:
                path = RPC_CLI_MAP[str(element.tag)]

            filename = path.replace(' ', '_')
            filename = '%s_%s.txt' % (filename, format)
            return load_fixture(filename)

        self.send_request.side_effect = load_from_file

    def test_junos_command_simple(self):
        set_module_args(dict(commands=['show version']))
        result = self.execute_module()
        self.assertEqual(len(result['stdout']), 1)
        self.assertTrue(result['stdout'][0].startswith('Hostname:'))

    def test_junos_command_multiple(self):
        set_module_args(dict(commands=['show version', 'show version']))
        result = self.execute_module()
        self.assertEqual(len(result['stdout']), 2)
        self.assertTrue(result['stdout'][0].startswith('Hostname:'))

    def test_junos_command_wait_for(self):
        wait_for = 'result[0] contains "Junos:"'
        set_module_args(dict(commands=['show version'], wait_for=wait_for))
        self.execute_module()

    def test_junos_command_wait_for_fails(self):
        wait_for = 'result[0] contains "test string"'
        set_module_args(dict(commands=['show version'], wait_for=wait_for))
        self.execute_module(failed=True)
        self.assertEqual(self.send_request.call_count, 10)

    def test_junos_command_retries(self):
        wait_for = 'result[0] contains "test string"'
        set_module_args(dict(commands=['show version'], wait_for=wait_for, retries=2))
        self.execute_module(failed=True)
        self.assertEqual(self.send_request.call_count, 2)

    def test_junos_command_match_any(self):
        wait_for = ['result[0] contains "Junos:"',
                    'result[0] contains "test string"']
        set_module_args(dict(commands=['show version'], wait_for=wait_for, match='any'))
        self.execute_module()

    def test_junos_command_match_all(self):
        wait_for = ['result[0] contains "Junos:"',
                    'result[0] contains "JUNOS Software Release"']
        set_module_args(dict(commands=['show version'], wait_for=wait_for, match='all'))
        self.execute_module()

    def test_junos_command_match_all_failure(self):
        wait_for = ['result[0] contains "Junos:"',
                    'result[0] contains "test string"']
        commands = ['show version', 'show version']
        set_module_args(dict(commands=commands, wait_for=wait_for, match='all'))
        self.execute_module(failed=True)

    def test_junos_command_simple_json(self):
        set_module_args(dict(commands=['show version'], display='json'))
        result = self.execute_module(format='json')
        self.assertEqual(len(result['stdout']), 1)
        self.assertTrue("software-information" in result['stdout'][0])

    def test_junos_command_simple_rpc_text(self):
        set_module_args(dict(rpcs=['get-software-information'], display='text'))
        result = self.execute_module(format='text')
        self.assertEqual(len(result['stdout']), 1)
        self.assertTrue(result['stdout'][0].startswith('Hostname:'))

    def test_junos_command_simple_rpc_json(self):
        set_module_args(dict(rpcs=['get-software-information'], display='json'))
        result = self.execute_module(format='json')
        self.assertEqual(len(result['stdout']), 1)
        self.assertTrue("software-information" in result['stdout'][0])

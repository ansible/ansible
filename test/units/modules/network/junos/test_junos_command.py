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

import os
import sys
import json
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes

jnpr_mock = MagicMock()
jxmlease_mock = MagicMock()
modules = {
    'jnpr': jnpr_mock,
    'jnpr.junos': jnpr_mock.junos,
    'jnpr.junos.utils': jnpr_mock.junos.utils,
    'jnpr.junos.utils.config': jnpr_mock.junos.utils.config,
    'jnpr.junos.version': jnpr_mock.junos.version,
    'jnpr.junos.exception': jnpr_mock.junos.execption,
    'jxmlease': jxmlease_mock
}
setattr(jnpr_mock.junos.version, 'VERSION', '2.0.0')
module_patcher = patch.dict('sys.modules', modules)
module_patcher.start()

from ansible.modules.network.junos import junos_command


def set_module_args(args):
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)

fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures')
fixture_data = {}


def load_fixture(name):
    path = os.path.join(fixture_path, name)

    if path in fixture_data:
        return fixture_data[path]

    with open(path) as f:
        data = f.read()

    try:
        data = json.loads(data)
    except:
        pass

    fixture_data[path] = data
    return data

rpc_command_map = {
    'get_software_information': 'show version'
}


class test_junosCommandModule(unittest.TestCase):

    def setUp(self):
        self.mock_run_commands = patch('ansible.module_utils.junos.Netconf.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_connect = patch('ansible.module_utils.junos.Netconf.connect')
        self.mock_connect.start()

        self.saved_stdout = sys.stdout

    def tearDown(self):
        self.mock_run_commands.stop()
        self.mock_connect.stop()
        sys.stdout = self.saved_stdout

    def execute_module(self, failed=False, changed=False, fmt='text', cmd_type='commands'):

        def load_from_file(*args, **kwargs):
            commands = args[0]
            output = list()

            for item in commands:
                try:
                    obj = json.loads(str(item))
                    command = obj['command']
                except ValueError:
                    command = item
                if cmd_type == 'rpcs':
                    command = rpc_command_map[str(command)]
                filename = os.path.join('output',
                                        str(command).replace(' ', '_') + '.{0}'.format(fmt))
                output.append(load_fixture(filename))

            return output

        self.run_commands.side_effect = load_from_file
        out = StringIO()
        sys.stdout = out

        with self.assertRaises(SystemExit):
            junos_command.main()

        result = json.loads(out.getvalue().strip())
        if failed:
            self.assertTrue(result.get('failed'))
        else:
            self.assertEqual(result.get('changed'), changed, result)

        return result

    def test_junos_command_format_text(self):
        set_module_args(dict(commands=['show version'], host='test', format='text'))
        result = self.execute_module()
        self.assertEqual(len(result['stdout']), 1)
        self.assertTrue(result['stdout'][0].startswith('Hostname'))

    def test_junos_command_multiple(self):
        set_module_args(dict(commands=['show version', 'show version'], host='test', format='text'))
        result = self.execute_module()
        self.assertEqual(len(result['stdout']), 2)
        self.assertTrue(result['stdout'][0].startswith('Hostname'))

    def test_junos_command_wait_for(self):
        wait_for = 'result[0] contains "Hostname"'
        set_module_args(dict(commands=['show version'], host='test', wait_for=wait_for, format='text'))
        self.execute_module()

    def test_junos_command_wait_for_fails(self):
        wait_for = 'result[0] contains "test string"'
        set_module_args(dict(commands=['show version'], host='test', wait_for=wait_for, format='text'))
        self.execute_module(failed=True)
        self.assertEqual(self.run_commands.call_count, 10)

    def test_junos_command_retries(self):
        wait_for = 'result[0] contains "test string"'
        set_module_args(dict(commands=['show version'], host='test', wait_for=wait_for, retries=2, format='text'))
        self.execute_module(failed=True)
        self.assertEqual(self.run_commands.call_count, 2)

    def test_junos_command_match_any(self):
        wait_for = ['result[0] contains "Hostname"',
                    'result[0] contains "test string"']
        set_module_args(dict(commands=['show version'], host='test', wait_for=wait_for, match='any', format='text'))
        self.execute_module()

    def test_junos_command_match_all(self):
        wait_for = ['result[0] contains "Hostname"',
                    'result[0] contains "Model"']
        set_module_args(dict(commands=['show version'], host='test', wait_for=wait_for, match='all', format='text'))
        self.execute_module()

    def test_junos_command_match_all_failure(self):
        wait_for = ['result[0] contains "Hostname"',
                    'result[0] contains "test string"']
        commands = ['show version', 'show version']
        set_module_args(dict(commands=commands, host='test', wait_for=wait_for, match='all', format='text'))
        self.execute_module(failed=True)

    def test_junos_command_rpc_format_text(self):
        set_module_args(dict(rpcs=['get_software_information'], host='test', format='text'))
        result = self.execute_module(fmt='text', cmd_type='rpcs')
        self.assertEqual(len(result['stdout']), 1)
        self.assertTrue(result['stdout'][0].startswith('Hostname'))

    def test_junos_command_rpc_format_text_multiple(self):
        set_module_args(dict(commands=['get_software_information', 'get_software_information'], host='test',
                             format='text'))
        result = self.execute_module(cmd_type='rpcs')
        self.assertEqual(len(result['stdout']), 2)
        self.assertTrue(result['stdout'][0].startswith('Hostname'))

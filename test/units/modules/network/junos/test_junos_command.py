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
from StringIO import StringIO

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch
from ansible.modules.network.junos import junos_command
from ansible.module_utils.junos import xml_to_json
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes


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


class test_junosCommandModule(unittest.TestCase):

    def setUp(self):
        self.mock_run_commands = patch('ansible.module_utils.junos.Netconf.run_commands')
        self.run_commands = self.mock_run_commands.start()

        self.mock_connect = patch('ansible.module_utils.junos.Netconf.connect')
        self.connect = self.mock_connect.start()

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

                filename = os.path.join(cmd_type,
                                        str(command).replace(' ', '_') + '.{0}'.format(fmt))
                if fmt == 'xml':
                    output.append(xml_to_json(load_fixture(filename)))
                else:
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
        set_module_args(dict(commands=['show version'], host='test'))
        result = self.execute_module()
        self.assertEqual(len(result['stdout']), 1)
        self.assertTrue(result['stdout'][0].startswith('Hostname'))

    def test_junos_command_format_xml(self):
        set_module_args(dict(commands=['show version'], host='test', format='xml'))
        result = self.execute_module(fmt='xml')
        self.assertEqual(len(result['stdout']), 1)
        self.assertTrue('software-information' in result['stdout'][0])

    def test_junos_command_multiple(self):
        set_module_args(dict(commands=['show version', 'show version'], host='test'))
        result = self.execute_module()
        self.assertEqual(len(result['stdout']), 2)
        self.assertTrue(result['stdout'][0].startswith('Hostname'))

    def test_junos_command_wait_for(self):
        wait_for = 'result[0] contains "Hostname"'
        set_module_args(dict(commands=['show version'], host='test', wait_for=wait_for))
        self.execute_module()

    def test_junos_command_wait_for_fails(self):
        wait_for = 'result[0] contains "test string"'
        set_module_args(dict(commands=['show version'], host='test', wait_for=wait_for))
        self.execute_module(failed=True)
        self.assertEqual(self.run_commands.call_count, 10)

    def test_junos_command_retries(self):
        wait_for = 'result[0] contains "test string"'
        set_module_args(dict(commands=['show version'], host='test', wait_for=wait_for, retries=2))
        self.execute_module(failed=True)
        self.assertEqual(self.run_commands.call_count, 2)

    def test_junos_command_match_any(self):
        wait_for = ['result[0] contains "Hostname"',
                    'result[0] contains "test string"']
        set_module_args(dict(commands=['show version'], host='test', wait_for=wait_for, match='any'))
        self.execute_module()

    def test_junos_command_match_all(self):
        wait_for = ['result[0] contains "Hostname"',
                    'result[0] contains "Model"']
        set_module_args(dict(commands=['show version'], host='test', wait_for=wait_for, match='all'))
        self.execute_module()

    def test_junos_command_match_all_failure(self):
        wait_for = ['result[0] contains "Hostname"',
                    'result[0] contains "test string"']
        commands = ['show version', 'show version']
        set_module_args(dict(commands=commands, host='test', wait_for=wait_for, match='all'))
        self.execute_module(failed=True)

    def test_junos_command_rpc_format_xml(self):
        set_module_args(dict(rpcs=['get_software_information'], host='test', format='xml'))
        result = self.execute_module(fmt='xml', cmd_type='rpcs')
        self.assertEqual(len(result['stdout']), 1)
        self.assertTrue('software-information' in result['stdout'][0])

    def test_junos_command_rpc_multiple(self):
        set_module_args(dict(commands=['get_software_information', 'get_software_information'], host='test'))
        result = self.execute_module(fmt='xml', cmd_type='rpcs')
        self.assertEqual(len(result['stdout']), 2)
        self.assertTrue('software-information' in result['stdout'][0])

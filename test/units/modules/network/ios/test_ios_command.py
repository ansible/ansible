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
import json

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock
from ansible.errors import AnsibleModuleExit
from ansible.modules.network.ios import ios_command
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


class test_iosCommandModule(unittest.TestCase):

    def setUp(self):
        self.mock_run_commands = patch('ansible.modules.network.ios.ios_command.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        self.mock_run_commands.stop()

    def execute_module(self, failed=False, changed=False):

        def load_from_file(*args, **kwargs):
            module, commands = args
            output = list()

            for item in commands:
                try:
                    obj = json.loads(item)
                    command = obj['command']
                except ValueError:
                    command = item
                filename = str(command).replace(' ', '_')
                output.append(load_fixture(filename))
            return output

        self.run_commands.side_effect = load_from_file

        with self.assertRaises(AnsibleModuleExit) as exc:
            ios_command.main()

        result = exc.exception.result

        if failed:
            self.assertTrue(result.get('failed'))
        else:
            self.assertEqual(result.get('changed'), changed, result)

        return result

    def test_ios_command_simple(self):
        set_module_args(dict(commands=['show version']))
        result = self.execute_module()
        self.assertEqual(len(result['stdout']), 1)
        self.assertTrue(result['stdout'][0].startswith('Cisco IOS Software'))

    def test_ios_command_multiple(self):
        set_module_args(dict(commands=['show version', 'show version']))
        result = self.execute_module()
        self.assertEqual(len(result['stdout']), 2)
        self.assertTrue(result['stdout'][0].startswith('Cisco IOS Software'))

    def test_ios_command_wait_for(self):
        wait_for = 'result[0] contains "Cisco IOS"'
        set_module_args(dict(commands=['show version'], wait_for=wait_for))
        self.execute_module()

    def test_ios_command_wait_for_fails(self):
        wait_for = 'result[0] contains "test string"'
        set_module_args(dict(commands=['show version'], wait_for=wait_for))
        self.execute_module(failed=True)
        self.assertEqual(self.run_commands.call_count, 10)

    def test_ios_command_retries(self):
        wait_for = 'result[0] contains "test string"'
        set_module_args(dict(commands=['show version'], wait_for=wait_for, retries=2))
        self.execute_module(failed=True)
        self.assertEqual(self.run_commands.call_count, 2)

    def test_ios_command_match_any(self):
        wait_for = ['result[0] contains "Cisco IOS"',
                    'result[0] contains "test string"']
        set_module_args(dict(commands=['show version'], wait_for=wait_for, match='any'))
        self.execute_module()

    def test_ios_command_match_all(self):
        wait_for = ['result[0] contains "Cisco IOS"',
                    'result[0] contains "IOSv Software"']
        set_module_args(dict(commands=['show version'], wait_for=wait_for, match='all'))
        self.execute_module()

    def test_ios_command_match_all_failure(self):
        wait_for = ['result[0] contains "Cisco IOS"',
                    'result[0] contains "test string"']
        commands = ['show version', 'show version']
        set_module_args(dict(commands=commands, wait_for=wait_for, match='all'))
        self.execute_module(failed=True)

#!/usr/bin/env python
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

import os
import json

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock
from ansible.errors import AnsibleModuleExit
from ansible.modules.network.basics import net_command
from ansible.module_utils import basic
from ansible.module_utils.local import LocalAnsibleModule
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


class TestNetCommandModule(unittest.TestCase):

    def execute_module(self, command_response=None, failed=False, changed=True):

        if not command_response:
            command_response = (256, '', 'no command response provided in test case')

        with patch.object(LocalAnsibleModule, 'exec_command') as mock_exec_command:
            mock_exec_command.return_value = command_response

            with self.assertRaises(AnsibleModuleExit) as exc:
                net_command.main()

        result = exc.exception.result

        if failed:
            self.assertTrue(result.get('failed'), result)
        else:
            self.assertEqual(result.get('changed'), changed, result)

        return result

    def test_net_command_string(self):
        """
        Test for all keys in the response
        """
        set_module_args({'_raw_params': 'show version'})
        result = self.execute_module((0, 'ok', ''))
        for key in ['rc', 'stdout', 'stderr', 'stdout_lines']:
            self.assertIn(key, result)

    def test_net_command_json(self):
        """
        The stdout_lines key should not be present when the return
        string is a json data structure
        """
        set_module_args({'_raw_params': 'show version'})
        result = self.execute_module((0, '{"key": "value"}', ''))
        for key in ['rc', 'stdout', 'stderr']:
            self.assertIn(key, result)
        self.assertNotIn('stdout_lines', result)

    def test_net_command_missing_command(self):
        """
        Test failure on missing command
        """
        set_module_args({'_raw_params': ''})
        self.execute_module(failed=True)

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
from ansible.module_utils import eos


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


class TestEosModuleUtil(unittest.TestCase):

    def setUp(self):
        eos._DEVICE_CONFIGS = {}

    def test_eos_get_config(self):
        mock_module = MagicMock(name='AnsibleModule')
        mock_module.exec_command.return_value = (0, ' sample config\n', '')

        self.assertFalse('show running-config' in eos._DEVICE_CONFIGS)

        out  = eos.get_config(mock_module)

        self.assertEqual(out, 'sample config')
        self.assertTrue('show running-config' in eos._DEVICE_CONFIGS)
        self.assertEqual(eos._DEVICE_CONFIGS['show running-config'], 'sample config')

    def test_eos_get_config_cached(self):
        mock_module = MagicMock(name='AnsibleModule')
        mock_module.exec_command.return_value = (0, ' sample config\n', '')

        eos._DEVICE_CONFIGS['show running-config'] = 'different config'

        out = eos.get_config(mock_module)

        self.assertEqual(out, 'different config')
        self.assertFalse(mock_module.exec_command.called)

    def test_eos_get_config_error(self):
        mock_module = MagicMock(name='AnsibleModule')
        mock_module.exec_command.return_value = (1, '', 'error')

        out = eos.get_config(mock_module, 'show running_config')

        self.assertTrue(mock_module.fail_json.called)

    def test_eos_supports_sessions_fail(self):
        mock_module = MagicMock(name='AnsibleModule')
        mock_module.exec_command.return_value = (1, '', '')
        self.assertFalse(eos.supports_sessions(mock_module))
        mock_module.exec_command.called_with_args(['show configuration sessions'])

    def test_eos_supports_sessions_pass(self):
        mock_module = MagicMock(name='AnsibleModule')
        mock_module.exec_command.return_value = (0, '', '')
        self.assertTrue(eos.supports_sessions(mock_module))
        mock_module.exec_command.called_with_args(['show configuration sessions'])

    def test_eos_run_commands(self):
        mock_module = MagicMock(name='AnsibleModule')
        mock_module.exec_command.return_value = (0, 'stdout', '')
        mock_module.from_json.side_effect = ValueError
        out = eos.run_commands(mock_module, 'command')
        self.assertEqual(out, ['stdout'])

    def test_eos_run_commands_returns_json(self):
        mock_module = MagicMock(name='AnsibleModule')
        mock_module.exec_command.return_value = (0, '{"key": "value"}', '')
        mock_module.from_json.return_value = json.loads('{"key": "value"}')
        out = eos.run_commands(mock_module, 'command')
        self.assertEqual(out, [{'key': 'value'}])

    def test_eos_run_commands_check_rc_fails(self):
        mock_module = MagicMock(name='AnsibleModule')
        mock_module.exec_command.return_value = (1, '', 'stderr')
        out = eos.run_commands(mock_module, 'command')
        mock_module.fail_json.called_with_args({'msg': 'stderr'})


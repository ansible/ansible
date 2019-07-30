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
from units.modules.utils import set_module_args
from ansible.modules.network.voss import voss_command
from .voss_module import TestVossModule, load_fixture


class TestVossCommandModule(TestVossModule):

    module = voss_command

    def setUp(self):
        super(TestVossCommandModule, self).setUp()

        self.mock_run_commands = patch('ansible.modules.network.voss.voss_command.run_commands')
        self.run_commands = self.mock_run_commands.start()

    def tearDown(self):
        super(TestVossCommandModule, self).tearDown()
        self.mock_run_commands.stop()

    def load_fixtures(self, commands=None):

        def load_from_file(*args, **kwargs):
            module, commands = args
            output = list()

            for item in commands:
                try:
                    obj = json.loads(item['command'])
                    command = obj['command']
                except ValueError:
                    command = item['command']
                filename = str(command).replace(' ', '_')
                output.append(load_fixture(filename))
            return output

        self.run_commands.side_effect = load_from_file

    def test_voss_command_simple(self):
        set_module_args(dict(commands=['show sys-info']))
        result = self.execute_module()
        self.assertEqual(len(result['stdout']), 1)
        self.assertTrue(result['stdout'][0].startswith('General Info'))

    def test_voss_command_multiple(self):
        set_module_args(dict(commands=['show sys-info', 'show sys-info']))
        result = self.execute_module()
        self.assertEqual(len(result['stdout']), 2)
        self.assertTrue(result['stdout'][0].startswith('General Info'))

    def test_voss_command_wait_for(self):
        wait_for = 'result[0] contains "General Info"'
        set_module_args(dict(commands=['show sys-info'], wait_for=wait_for))
        self.execute_module()

    def test_voss_command_wait_for_fails(self):
        wait_for = 'result[0] contains "test string"'
        set_module_args(dict(commands=['show sys-info'], wait_for=wait_for))
        self.execute_module(failed=True)
        self.assertEqual(self.run_commands.call_count, 10)

    def test_voss_command_retries(self):
        wait_for = 'result[0] contains "test string"'
        set_module_args(dict(commands=['show sys-info'], wait_for=wait_for, retries=2))
        self.execute_module(failed=True)
        self.assertEqual(self.run_commands.call_count, 2)

    def test_voss_command_match_any(self):
        wait_for = ['result[0] contains "General Info"',
                    'result[0] contains "test string"']
        set_module_args(dict(commands=['show sys-info'], wait_for=wait_for, match='any'))
        self.execute_module()

    def test_voss_command_match_all(self):
        wait_for = ['result[0] contains "General Info"',
                    'result[0] contains "Chassis Info"']
        set_module_args(dict(commands=['show sys-info'], wait_for=wait_for, match='all'))
        self.execute_module()

    def test_voss_command_match_all_failure(self):
        wait_for = ['result[0] contains "General Info"',
                    'result[0] contains "test string"']
        commands = ['show sys-info', 'show sys-info']
        set_module_args(dict(commands=commands, wait_for=wait_for, match='all'))
        self.execute_module(failed=True)

    def test_voss_command_configure_error(self):
        commands = ['configure terminal']
        set_module_args({
            'commands': commands,
            '_ansible_check_mode': True,
        })
        result = self.execute_module(failed=True)
        self.assertEqual(
            result['msg'],
            'voss_command does not support running config mode commands. Please use voss_config instead'
        )

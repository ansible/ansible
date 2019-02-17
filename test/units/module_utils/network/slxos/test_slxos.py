#
# (c) 2018 Extreme Networks Inc.
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
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from os import path
import json

from mock import MagicMock, patch, call

from units.compat import unittest
from ansible.module_utils.network.slxos import slxos


class TestPluginCLIConfSLXOS(unittest.TestCase):
    """ Test class for SLX-OS CLI Conf Methods
    """

    def test_get_connection_established(self):
        """ Test get_connection with established connection
        """
        module = MagicMock()
        connection = slxos.get_connection(module)
        self.assertEqual(connection, module.slxos_connection)

    @patch('ansible.module_utils.network.slxos.slxos.Connection')
    def test_get_connection_new(self, connection):
        """ Test get_connection with new connection
        """
        socket_path = "little red riding hood"
        module = MagicMock(spec=[
            'fail_json',
        ])
        module._socket_path = socket_path

        connection().get_capabilities.return_value = '{"network_api": "cliconf"}'
        returned_connection = slxos.get_connection(module)
        connection.assert_called_with(socket_path)
        self.assertEqual(returned_connection, module.slxos_connection)

    @patch('ansible.module_utils.network.slxos.slxos.Connection')
    def test_get_connection_incorrect_network_api(self, connection):
        """ Test get_connection with incorrect network_api response
        """
        socket_path = "little red riding hood"
        module = MagicMock(spec=[
            'fail_json',
        ])
        module._socket_path = socket_path
        module.fail_json.side_effect = TypeError

        connection().get_capabilities.return_value = '{"network_api": "nope"}'

        with self.assertRaises(TypeError):
            slxos.get_connection(module)

    @patch('ansible.module_utils.network.slxos.slxos.Connection')
    def test_get_capabilities(self, connection):
        """ Test get_capabilities
        """
        socket_path = "little red riding hood"
        module = MagicMock(spec=[
            'fail_json',
        ])
        module._socket_path = socket_path
        module.fail_json.side_effect = TypeError

        capabilities = {'network_api': 'cliconf'}

        connection().get_capabilities.return_value = json.dumps(capabilities)

        capabilities_returned = slxos.get_capabilities(module)

        self.assertEqual(capabilities, capabilities_returned)

    @patch('ansible.module_utils.network.slxos.slxos.Connection')
    def test_run_commands(self, connection):
        """ Test get_capabilities
        """
        module = MagicMock()

        commands = [
            'hello',
            'dolly',
            'well hello',
            'dolly',
            'its so nice to have you back',
            'where you belong',
        ]

        responses = [
            'Dolly, never go away again1',
            'Dolly, never go away again2',
            'Dolly, never go away again3',
            'Dolly, never go away again4',
            'Dolly, never go away again5',
            'Dolly, never go away again6',
        ]

        module.slxos_connection.get.side_effect = responses

        run_command_responses = slxos.run_commands(module, commands)

        calls = []

        for command in commands:
            calls.append(call(
                command,
                None,
                None
            ))

        module.slxos_connection.get.assert_has_calls(calls)

        self.assertEqual(responses, run_command_responses)

    @patch('ansible.module_utils.network.slxos.slxos.Connection')
    def test_load_config(self, connection):
        """ Test load_config
        """
        module = MagicMock()

        commands = [
            'what does it take',
            'to be',
            'number one?',
            'two is not a winner',
            'and three nobody remember',
        ]

        slxos.load_config(module, commands)

        module.slxos_connection.edit_config.assert_called_once_with(commands)

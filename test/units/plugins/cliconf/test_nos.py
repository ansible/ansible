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

from mock import MagicMock, call

from units.compat import unittest
from ansible.plugins.cliconf import nos

FIXTURE_DIR = b'%s/fixtures/nos' % (
    path.dirname(path.abspath(__file__)).encode('utf-8')
)


def _connection_side_effect(*args, **kwargs):
    try:
        if args:
            value = args[0]
        else:
            value = kwargs.get('command')

        fixture_path = path.abspath(
            b'%s/%s' % (FIXTURE_DIR, b'_'.join(value.split(b' ')))
        )
        with open(fixture_path, 'rb') as file_desc:
            return file_desc.read()
    except (OSError, IOError):
        if args:
            value = args[0]
            return value
        elif kwargs.get('command'):
            value = kwargs.get('command')
            return value

        return 'Nope'


class TestPluginCLIConfNOS(unittest.TestCase):
    """ Test class for NOS CLI Conf Methods
    """
    def setUp(self):
        self._mock_connection = MagicMock()
        self._mock_connection.send.side_effect = _connection_side_effect
        self._cliconf = nos.Cliconf(self._mock_connection)
        self.maxDiff = None

    def tearDown(self):
        pass

    def test_get_device_info(self):
        """ Test get_device_info
        """
        device_info = self._cliconf.get_device_info()

        mock_device_info = {
            'network_os': 'nos',
            'network_os_model': 'BR-VDX6740',
            'network_os_version': '7.2.0',
        }

        self.assertEqual(device_info, mock_device_info)

    def test_get_config(self):
        """ Test get_config
        """
        running_config = self._cliconf.get_config()

        fixture_path = path.abspath(b'%s/show_running-config' % FIXTURE_DIR)
        with open(fixture_path, 'rb') as file_desc:
            mock_running_config = file_desc.read()
            self.assertEqual(running_config, mock_running_config)

    def test_edit_config(self):
        """ Test edit_config
        """
        test_config_command = b'this\nis\nthe\nsong\nthat\nnever\nends'

        self._cliconf.edit_config(test_config_command)

        send_calls = []

        for command in [b'configure terminal', test_config_command, b'end']:
            send_calls.append(call(
                command=command,
                prompt_retry_check=False,
                sendonly=False,
                newline=True,
                check_all=False
            ))

        self._mock_connection.send.assert_has_calls(send_calls)

    def test_get_capabilities(self):
        """ Test get_capabilities
        """
        capabilities = json.loads(self._cliconf.get_capabilities())
        mock_capabilities = {
            'network_api': 'cliconf',
            'rpc': [
                'get_config',
                'edit_config',
                'get_capabilities',
                'get',
                'enable_response_logging',
                'disable_response_logging'
            ],
            'device_info': {
                'network_os_model': 'BR-VDX6740',
                'network_os_version': '7.2.0',
                'network_os': 'nos'
            }
        }

        self.assertEqual(
            mock_capabilities,
            capabilities
        )

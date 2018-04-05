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

import os
from mock import MagicMock, call

from ansible.compat.tests import unittest
from ansible.plugins.cliconf import slxos

FIXTURE_PATH = '%s/fixtures/slxos' % os.path.dirname(os.path.abspath(__file__))


def _connection_side_effect(*args, **kwargs):
    try:
        if args:
            value = args.pop(0)
        else:
            value = kwargs.get('command')
        with open('%s/%s' % (FIXTURE_PATH, '_'.join(value.split(' ')))) as file_desc:
            return file_desc.read()
    except:
        if args:
            value = args.pop(0)
        else:
            value = kwargs.get('command')
            return value

        return 'Nope'


class TestPluginCLIConfSLXOS(unittest.TestCase):

    def setUp(self):
        self._mock_connection = MagicMock()
        self._mock_connection.send.side_effect = _connection_side_effect
        self._cliconf = slxos.Cliconf(self._mock_connection)

    def tearDown(self):
        pass

    def test_get_device_info(self):
        device_info = self._cliconf.get_device_info()

        mock_device_info = {
            'network_os': 'slxos',
            'network_os_model': 'BR-SLX9140',
            'network_os_version': '17s.1.02',
        }

        self.assertEqual(device_info, mock_device_info)

    def test_get_config(self):
        running_config = self._cliconf.get_config()

        with open('%s/show_running-config' % FIXTURE_PATH) as file_desc:
            mock_running_config = file_desc.read()
            self.assertEqual(running_config, mock_running_config)

        startup_config = self._cliconf.get_config()

        with open('%s/show_startup-config' % FIXTURE_PATH) as file_desc:
            mock_startup_config = file_desc.read()
            self.assertEqual(startup_config, mock_startup_config)

    def test_edit_config(self):
        test_config_command = 'this\nis\nthe\nsong\nthat\nnever\nends'

        self._cliconf.edit_config(test_config_command)

        send_calls = []

        for command in ['configure terminal', test_config_command, 'end']:
            send_calls.append(call(
                command=command,
                prompt_retry_check=False,
                sendonly=False,
                newline=True
            ))

        self._mock_connection.send.assert_has_calls(send_calls)

    def test_get_capabilities(self):
        capabilities = self._cliconf.get_capabilities()

        self.assertEqual(
            '{"network_api": "cliconf", "rpc": ["get_config", "edit_config", '
            '"get_capabilities", "get"], "device_info": {"network_os_model": '
            '"BR-SLX9140", "network_os_version": "17s.1.02", "network_os": "s'
            'lxos"}}',
            capabilities
        )

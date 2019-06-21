#
# (c) 2019 Red Hat Inc.
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
from ansible.plugins.cliconf import ios
from ansible.module_utils._text import to_bytes


b_FIXTURE_DIR = b'%s/fixtures/ios' % (
    to_bytes(path.dirname(path.abspath(__file__)), errors='surrogate_or_strict')
)


def _connection_side_effect(*args, **kwargs):
    try:
        if args:
            value = args[0]
        else:
            value = kwargs.get('command')

        fixture_path = path.abspath(
            b'%s/%s' % (b_FIXTURE_DIR, b'_'.join(value.split(b' ')))
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


class TestPluginCLIConfIOS(unittest.TestCase):
    """ Test class for IOS CLI Conf Methods
    """
    def setUp(self):
        self._mock_connection = MagicMock()
        self._mock_connection.send.side_effect = _connection_side_effect
        self._cliconf = ios.Cliconf(self._mock_connection)
        self.maxDiff = None

    def tearDown(self):
        pass

    def test_get_device_info(self):
        """ Test get_device_info
        """
        device_info = self._cliconf.get_device_info()

        mock_device_info = {'network_os': 'ios',
                            'network_os_model': 'CSR1000V',
                            'network_os_version': '16.06.01',
                            'network_os_hostname': 'an-csr-01',
                            'network_os_image': 'bootflash:packages.conf'
                            }

        self.assertEqual(device_info, mock_device_info)

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
                'disable_response_logging',
                'edit_banner',
                'get_diff',
                'run_commands',
                'get_defaults_flag'
            ],
            'device_operations': {
                'supports_diff_replace': True,
                'supports_commit': False,
                'supports_rollback': False,
                'supports_defaults': True,
                'supports_onbox_diff': False,
                'supports_commit_comment': False,
                'supports_multiline_delimiter': True,
                'supports_diff_match': True,
                'supports_diff_ignore_lines': True,
                'supports_generate_diff': True,
                'supports_replace': False
            },
            'device_info': {
                'network_os_hostname': 'an-csr-01',
                'network_os_image': 'bootflash:packages.conf',
                'network_os_model': 'CSR1000V',
                'network_os_version': '16.06.01',
                'network_os': 'ios'
            },
            'format': ['text'],
            'diff_match': ['line', 'strict', 'exact', 'none'],
            'diff_replace': ['line', 'block'],
            'output': []
        }

        self.assertEqual(
            mock_capabilities,
            capabilities
        )

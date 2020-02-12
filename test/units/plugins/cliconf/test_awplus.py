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

from mock import MagicMock

from units.compat import unittest
from ansible.plugins.cliconf import awplus
from ansible.module_utils._text import to_bytes

b_FIXTURE_DIR = b'%s/fixtures/awplus' % (
    to_bytes(path.dirname(path.abspath(__file__)),
             errors='surrogate_or_strict')
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
            value - kwargs.get('command')
            return value

        return 'Nope'


class TestPluginCliConfAwplus(unittest.TestCase):
    """ Test class for Aw+ Cliconf methods
    """

    def setUp(self):
        self._mock_connection = MagicMock()
        self._mock_connection.send.side_effect = _connection_side_effect
        self._cliconf = awplus.Cliconf(self._mock_connection)
        self.maxDiff = None

    def tearDown(self):
        pass

    def test_get_device_info(self):
        """ Test get_device_info
        """
        device_info = self._cliconf.get_device_info()

        mock_device_info = {'network_os': 'awplus',
                            'network_os_model': 'AR2050V',
                            'network_os_version': 'main-20191128-1',
                            'network_os_hostname': 'aw1',
                            'network_os_image': 'flash:/default.cfg'}
        self.assertEqual(device_info, mock_device_info)

    def test_get_capabilities(self):
        """ Test get_capabilities
        """
        capabilities = json.loads(self._cliconf.get_capabilities())
        mock_capabilities = {
            u'network_api': u'cliconf',
            u'rpc': [
                u'get_config',
                u'edit_config',
                u'get_capabilities',
                u'get',
                u'enable_response_logging',
                u'disable_response_logging',
                u'edit_banner',
                u'get_diff',
                u'run_commands',
                u'get_defaults_flag'
            ],
            u'device_operations': {
                u'supports_diff_replace': True,
                u'supports_commit': False,
                u'supports_defaults': True,
                u'supports_onbox_diff': False,
                u'supports_commit_comment': False,
                u'supports_multiline_delimiter': True,
                u'supports_diff_match': True,
                u'supports_diff_ignore_lines': True,
                u'supports_generate_diff': True,
                u'supports_replace': False,
                u'supports_rollback': False,
            },
            u'device_info': {
                u'network_os_hostname': u'aw1',
                u'network_os_image': u'flash:/default.cfg',
                u'network_os_model': u'AR2050V',
                u'network_os_version': u'main-20191128-1',
                u'network_os': u'awplus'
            },
            u'format': [u'text'],
            u'diff_match': [u'line', u'strict', u'exact', u'none'],
            u'diff_replace': [u'line', u'block'],
            u'output': []
        }

        self.assertEqual(
            mock_capabilities,
            capabilities
        )

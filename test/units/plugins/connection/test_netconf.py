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

import sys
import re
import json
import pytest

from io import StringIO

from units.compat import unittest
from units.compat.mock import patch, MagicMock, PropertyMock
from ansible.errors import AnsibleConnectionFailure
from ansible.playbook.play_context import PlayContext

pytest.importorskip("ncclient")

PY3 = sys.version_info[0] == 3

builtin_import = __import__

mock_ncclient = MagicMock(name='ncclient')


def import_mock(name, *args):
    if name.startswith('ncclient'):
        return mock_ncclient
    return builtin_import(name, *args)


if PY3:
    with patch('builtins.__import__', side_effect=import_mock):
        from ansible.plugins.connection import netconf
        from ansible.plugins.loader import connection_loader
else:
    with patch('__builtin__.__import__', side_effect=import_mock):
        from ansible.plugins.connection import netconf
        from ansible.plugins.loader import connection_loader


class TestNetconfConnectionClass(unittest.TestCase):

    def test_netconf_init(self):
        pc = PlayContext()
        conn = connection_loader.get('netconf', pc, '/dev/null')

        self.assertEqual('default', conn._network_os)
        self.assertIsNone(conn._manager)
        self.assertFalse(conn._connected)

    @patch("ansible.plugins.connection.netconf.netconf_loader")
    def test_netconf__connect(self, mock_netconf_loader):
        pc = PlayContext()
        conn = connection_loader.get('netconf', pc, '/dev/null')

        mock_manager = MagicMock()
        mock_manager.session_id = '123456789'
        netconf.manager.connect = MagicMock(return_value=mock_manager)

        rc, out, err = conn._connect()

        self.assertEqual(0, rc)
        self.assertEqual(b'123456789', out)
        self.assertEqual(b'', err)
        self.assertTrue(conn._connected)

    def test_netconf_exec_command(self):
        pc = PlayContext()
        conn = connection_loader.get('netconf', pc, '/dev/null')

        conn._connected = True

        mock_reply = MagicMock(name='reply')
        type(mock_reply).data_xml = PropertyMock(return_value='<test/>')

        mock_manager = MagicMock(name='self._manager')
        mock_manager.rpc.return_value = mock_reply
        conn._manager = mock_manager

        out = conn.exec_command('<test/>')

        self.assertEqual('<test/>', out)

    def test_netconf_exec_command_invalid_request(self):
        pc = PlayContext()
        conn = connection_loader.get('netconf', pc, '/dev/null')

        conn._connected = True

        mock_manager = MagicMock(name='self._manager')
        conn._manager = mock_manager

        netconf.to_ele.return_value = None

        out = conn.exec_command('test string')

        self.assertEqual('unable to parse request', out)

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

from mock import MagicMock

from units.compat import unittest
from ansible.plugins.terminal import slxos
from ansible.errors import AnsibleConnectionFailure


class TestPluginTerminalSLXOS(unittest.TestCase):
    """ Test class for SLX-OS Terminal Module
    """
    def setUp(self):
        self._mock_connection = MagicMock()
        self._terminal = slxos.TerminalModule(self._mock_connection)

    def tearDown(self):
        pass

    def test_on_open_shell(self):
        """ Test on_open_shell
        """
        self._mock_connection.exec_command.side_effect = [
            b'Looking out my window I see a brick building, and people. Cool.',
        ]
        self._terminal.on_open_shell()
        self._mock_connection.exec_command.assert_called_with(u'terminal length 0')

    def test_on_open_shell_error(self):
        """ Test on_open_shell with error
        """
        self._mock_connection.exec_command.side_effect = [
            AnsibleConnectionFailure
        ]

        with self.assertRaises(AnsibleConnectionFailure):
            self._terminal.on_open_shell()

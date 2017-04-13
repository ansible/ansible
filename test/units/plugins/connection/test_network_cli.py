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

import re
import json

from io import StringIO

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock

from ansible.errors import AnsibleConnectionFailure
from ansible.playbook.play_context import PlayContext
from ansible.plugins.connection import network_cli


class TestConnectionClass(unittest.TestCase):

    @patch("ansible.plugins.connection.network_cli.terminal_loader")
    @patch("ansible.plugins.connection.network_cli._Connection._connect")
    def test_network_cli__connect(self, mocked_super, mocked_terminal_loader):
        pc = PlayContext()
        new_stdin = StringIO()

        conn = network_cli.Connection(pc, new_stdin)
        conn.ssh = None

        self.assertRaises(AnsibleConnectionFailure, conn._connect)

        mocked_terminal_loader.reset_mock()
        mocked_terminal_loader.get.return_value = None

        pc.network_os = 'invalid'
        self.assertRaises(AnsibleConnectionFailure, conn._connect)
        self.assertFalse(mocked_terminal_loader.all.called)

        mocked_terminal_loader.reset_mock()
        mocked_terminal_loader.get.return_value = 'valid'

        conn._connect()
        self.assertEqual(conn._terminal, 'valid')

    def test_network_cli_open_shell(self):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = network_cli.Connection(pc, new_stdin)

        conn.ssh = MagicMock()
        conn.receive = MagicMock()

        mock_terminal = MagicMock()
        conn._terminal = mock_terminal

        mock__connect = MagicMock()
        conn._connect = mock__connect

        conn.open_shell()

        self.assertTrue(mock__connect.called)
        self.assertTrue(mock_terminal.on_open_shell.called)
        self.assertFalse(mock_terminal.on_authorize.called)

        mock_terminal.reset_mock()

        conn._play_context.become = True
        conn._play_context.become_pass = 'password'

        conn.open_shell()

        self.assertTrue(mock__connect.called)
        mock_terminal.on_authorize.assert_called_with(passwd='password')

    def test_network_cli_close_shell(self):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = network_cli.Connection(pc, new_stdin)

        terminal = MagicMock(supports_multiplexing=False)
        conn._terminal = terminal

        conn.close_shell()

        conn._shell = MagicMock()

        conn.close_shell()
        self.assertTrue(terminal.on_close_shell.called)

        terminal.supports_multiplexing = True

        conn.close_shell()
        self.assertIsNone(conn._shell)

    def test_network_cli_exec_command(self):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = network_cli.Connection(pc, new_stdin)

        mock_open_shell = MagicMock()
        conn.open_shell = mock_open_shell

        mock_send = MagicMock(return_value='command response')
        conn.send = mock_send

        # test sending a single command and converting to dict
        rc, out, err = conn.exec_command('command')
        self.assertEqual(out, 'command response')
        self.assertTrue(mock_open_shell.called)
        mock_send.assert_called_with({'command': 'command'})

        mock_open_shell.reset_mock()

        # test sending a json string
        rc, out, err = conn.exec_command(json.dumps({'command': 'command'}))
        self.assertEqual(out, 'command response')
        mock_send.assert_called_with({'command': 'command'})
        self.assertTrue(mock_open_shell.called)

        mock_open_shell.reset_mock()
        conn._shell = MagicMock()

        # test _shell already open
        rc, out, err = conn.exec_command('command')
        self.assertEqual(out, 'command response')
        self.assertFalse(mock_open_shell.called)
        mock_send.assert_called_with({'command': 'command'})


    def test_network_cli_send(self):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = network_cli.Connection(pc, new_stdin)

        mock__terminal = MagicMock()
        mock__terminal.terminal_stdout_re = [re.compile('device#')]
        mock__terminal.terminal_stderr_re = [re.compile('^ERROR')]
        conn._terminal = mock__terminal

        mock__shell = MagicMock()
        conn._shell = mock__shell

        response = """device#command
        command response

        device#
        """

        mock__shell.recv.return_value = response

        output = conn.send({'command': 'command'})

        mock__shell.sendall.assert_called_with('command\r')
        self.assertEqual(output, 'command response')

        mock__shell.reset_mock()
        mock__shell.recv.return_value = "ERROR: error message"

        with self.assertRaises(AnsibleConnectionFailure) as exc:
            conn.send({'command': 'command'})
        self.assertEqual(str(exc.exception), 'ERROR: error message')


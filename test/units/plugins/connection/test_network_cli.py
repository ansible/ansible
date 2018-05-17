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
from ansible.plugins.loader import connection_loader


class TestConnectionClass(unittest.TestCase):

    @patch("ansible.plugins.connection.paramiko_ssh.Connection._connect")
    def test_network_cli__connect_error(self, mocked_super):
        pc = PlayContext()
        new_stdin = StringIO()

        conn = connection_loader.get('network_cli', pc, '/dev/null')
        conn.ssh = MagicMock()
        conn.receive = MagicMock()
        conn._terminal = MagicMock()
        pc.network_os = None
        self.assertRaises(AnsibleConnectionFailure, conn._connect)

    @patch("ansible.plugins.connection.paramiko_ssh.Connection._connect")
    def test_network_cli__invalid_os(self, mocked_super):
        pc = PlayContext()
        new_stdin = StringIO()

        conn = connection_loader.get('network_cli', pc, '/dev/null')
        conn.ssh = MagicMock()
        conn.receive = MagicMock()
        conn._terminal = MagicMock()
        pc.network_os = None
        self.assertRaises(AnsibleConnectionFailure, conn._connect)

    @patch("ansible.plugins.connection.network_cli.terminal_loader")
    @patch("ansible.plugins.connection.paramiko_ssh.Connection._connect")
    def test_network_cli__connect(self, mocked_super, mocked_terminal_loader):
        pc = PlayContext()
        new_stdin = StringIO()

        conn = connection_loader.get('network_cli', pc, '/dev/null')
        pc.network_os = 'ios'

        conn.ssh = MagicMock()
        conn.receive = MagicMock()
        conn._terminal = MagicMock()

        conn._connect()
        self.assertTrue(conn._terminal.on_open_shell.called)
        self.assertFalse(conn._terminal.on_become.called)

        conn._play_context.become = True
        conn._play_context.become_method = 'enable'
        conn._play_context.become_pass = 'password'
        conn._connected = False

        conn._connect()
        conn._terminal.on_become.assert_called_with(passwd='password')

    @patch("ansible.plugins.connection.paramiko_ssh.Connection.close")
    def test_network_cli_close(self, mocked_super):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = network_cli.Connection(pc, new_stdin)

        terminal = MagicMock(supports_multiplexing=False)
        conn._terminal = terminal
        conn._ssh_shell = MagicMock()
        conn.paramiko_conn = MagicMock()
        conn._connected = True

        conn.close()
        self.assertTrue(terminal.on_close_shell.called)
        self.assertIsNone(conn._ssh_shell)
        self.assertIsNone(conn.paramiko_conn)

    @patch("ansible.plugins.connection.paramiko_ssh.Connection._connect")
    def test_network_cli_exec_command(self, mocked_super):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = network_cli.Connection(pc, new_stdin)

        mock_send = MagicMock(return_value=b'command response')
        conn.send = mock_send
        conn._ssh_shell = MagicMock()

        # test sending a single command and converting to dict
        out = conn.exec_command('command')
        self.assertEqual(out, b'command response')
        mock_send.assert_called_with(command=b'command')

        # test sending a json string
        out = conn.exec_command(json.dumps({'command': 'command'}))
        self.assertEqual(out, b'command response')
        mock_send.assert_called_with(command=b'command')

    def test_network_cli_send(self):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = network_cli.Connection(pc, new_stdin)
        mock__terminal = MagicMock()
        mock__terminal.terminal_stdout_re = [re.compile(b'device#')]
        mock__terminal.terminal_stderr_re = [re.compile(b'^ERROR')]
        conn._terminal = mock__terminal

        mock__shell = MagicMock()
        conn._ssh_shell = mock__shell

        response = b"""device#command
        command response

        device#
        """

        mock__shell.recv.return_value = response

        output = conn.send(b'command', None, None, None)

        mock__shell.sendall.assert_called_with(b'command\r')
        self.assertEqual(output, 'command response')

        mock__shell.reset_mock()
        mock__shell.recv.return_value = b"ERROR: error message device#"

        with self.assertRaises(AnsibleConnectionFailure) as exc:
            conn.send(b'command', None, None, None)
        self.assertEqual(str(exc.exception), 'ERROR: error message device#')

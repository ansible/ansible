#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) 2015, Toshio Kuratomi <tkuratomi@ansible.com>
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

import pipes
import sys
from io import StringIO

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch, MagicMock, mock_open

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleConnectionFailure, AnsibleFileNotFound
from ansible.playbook.play_context import PlayContext
from ansible.plugins.connection import ssh
from ansible.utils.unicode import to_bytes, to_unicode

class TestConnectionBaseClass(unittest.TestCase):

    def test_plugins_connection_ssh_basic(self):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = ssh.Connection(pc, new_stdin)

        # connect just returns self, so assert that
        res = conn._connect()
        self.assertEqual(conn, res)

        ssh.SSHPASS_AVAILABLE = False
        self.assertFalse(conn._sshpass_available())

        ssh.SSHPASS_AVAILABLE = True
        self.assertTrue(conn._sshpass_available())

        with patch('subprocess.Popen') as p:
            ssh.SSHPASS_AVAILABLE = None
            p.return_value = MagicMock()
            self.assertTrue(conn._sshpass_available())

            ssh.SSHPASS_AVAILABLE = None
            p.return_value = None
            p.side_effect = OSError()
            self.assertFalse(conn._sshpass_available())

        conn.close()
        self.assertFalse(conn._connected)

    def test_plugins_connection_ssh__build_command(self):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = ssh.Connection(pc, new_stdin)
        conn._build_command('ssh')

    def test_plugins_connection_ssh__exec_command(self):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = ssh.Connection(pc, new_stdin)

        conn._build_command = MagicMock()
        conn._build_command.return_value = 'ssh something something'
        conn._run = MagicMock()
        conn._run.return_value = (0, 'stdout', 'stderr')

        res, stdout, stderr = conn._exec_command('ssh')
        res, stdout, stderr = conn._exec_command('ssh', 'this is some data')

    @patch('select.select')
    @patch('fcntl.fcntl')
    @patch('os.write')
    @patch('os.close')
    @patch('pty.openpty')
    @patch('subprocess.Popen')
    def test_plugins_connection_ssh__run(self, mock_Popen, mock_openpty, mock_osclose, mock_oswrite, mock_fcntl, mock_select):
        pc = PlayContext()
        new_stdin = StringIO()

        conn = ssh.Connection(pc, new_stdin)
        conn._send_initial_data = MagicMock()
        conn._examine_output = MagicMock()
        conn._terminate_process = MagicMock()
        conn.sshpass_pipe = [MagicMock(), MagicMock()]

        mock_popen_res = MagicMock()
        mock_popen_res.poll   = MagicMock()
        mock_popen_res.wait   = MagicMock()
        mock_popen_res.stdin  = MagicMock()
        mock_popen_res.stdin.fileno.return_value = 1000
        mock_popen_res.stdout = MagicMock()
        mock_popen_res.stdout.fileno.return_value = 1001
        mock_popen_res.stderr = MagicMock()
        mock_popen_res.stderr.fileno.return_value = 1002
        mock_popen_res.return_code = 0
        mock_Popen.return_value = mock_popen_res

        def _mock_select(rlist, wlist, elist, timeout=None):
            rvals = []
            if mock_popen_res.stdin in rlist:
                rvals.append(mock_popen_res.stdin)
            if mock_popen_res.stderr in rlist:
                rvals.append(mock_popen_res.stderr)
            return (rvals, [], [])

        mock_select.side_effect = _mock_select

        mock_popen_res.stdout.read.side_effect = ["some data", ""]
        mock_popen_res.stderr.read.side_effect = [""]
        conn._run("ssh", "this is input data")

        # test with a password set to trigger the sshpass write
        pc.password = '12345'
        mock_popen_res.stdout.read.side_effect = ["some data", "", ""]
        mock_popen_res.stderr.read.side_effect = [""]
        conn._run(["ssh", "is", "a", "cmd"], "this is more data")

        # test with password prompting enabled
        pc.password = None
        pc.prompt = True
        mock_popen_res.stdout.read.side_effect = ["some data", "", ""]
        mock_popen_res.stderr.read.side_effect = [""]
        conn._run("ssh", "this is input data")

        # test with some become settings
        pc.prompt = False
        pc.become = True
        pc.success_key = 'BECOME-SUCCESS-abcdefg'
        mock_popen_res.stdout.read.side_effect = ["some data", "", ""]
        mock_popen_res.stderr.read.side_effect = [""]
        conn._run("ssh", "this is input data")

        # simulate no data input
        mock_openpty.return_value = (98, 99)
        mock_popen_res.stdout.read.side_effect = ["some data", "", ""]
        mock_popen_res.stderr.read.side_effect = [""]
        conn._run("ssh", "")

        # simulate no data input but Popen using new pty's fails
        mock_Popen.return_value = None
        mock_Popen.side_effect = [OSError(), mock_popen_res]
        mock_popen_res.stdout.read.side_effect = ["some data", "", ""]
        mock_popen_res.stderr.read.side_effect = [""]
        conn._run("ssh", "")

    def test_plugins_connection_ssh__examine_output(self):
        pc = PlayContext()
        new_stdin = StringIO()

        conn = ssh.Connection(pc, new_stdin)

        conn.check_password_prompt    = MagicMock()
        conn.check_become_success     = MagicMock()
        conn.check_incorrect_password = MagicMock()
        conn.check_missing_password   = MagicMock()

        def _check_password_prompt(line):
            if 'foo' in line:
                return True
            return False

        def _check_become_success(line):
            if 'BECOME-SUCCESS-abcdefghijklmnopqrstuvxyz' in line:
                return True
            return False

        def _check_incorrect_password(line):
            if 'incorrect password' in line:
                return True
            return False

        def _check_missing_password(line):
            if 'bad password' in line:
                return True
            return False

        conn.check_password_prompt.side_effect    = _check_password_prompt
        conn.check_become_success.side_effect     = _check_become_success
        conn.check_incorrect_password.side_effect = _check_incorrect_password
        conn.check_missing_password.side_effect   = _check_missing_password

        # test examining output for prompt
        conn._flags = dict(
            become_prompt = False,
            become_success = False,
            become_error = False,
            become_nopasswd_error = False,
        )

        pc.prompt = True
        output, unprocessed = conn._examine_output('source', 'state', 'line 1\nline 2\nfoo\nline 3\nthis should be the remainder', False)
        self.assertEqual(output, 'line 1\nline 2\nline 3\n')
        self.assertEqual(unprocessed, 'this should be the remainder')
        self.assertTrue(conn._flags['become_prompt'])
        self.assertFalse(conn._flags['become_success'])
        self.assertFalse(conn._flags['become_error'])
        self.assertFalse(conn._flags['become_nopasswd_error'])

        # test examining output for become prompt
        conn._flags = dict(
            become_prompt = False,
            become_success = False,
            become_error = False,
            become_nopasswd_error = False,
        )

        pc.prompt = False
        pc.success_key = 'BECOME-SUCCESS-abcdefghijklmnopqrstuvxyz'
        output, unprocessed = conn._examine_output('source', 'state', 'line 1\nline 2\nBECOME-SUCCESS-abcdefghijklmnopqrstuvxyz\nline 3\n', False)
        self.assertEqual(output, 'line 1\nline 2\nline 3\n')
        self.assertEqual(unprocessed, '')
        self.assertFalse(conn._flags['become_prompt'])
        self.assertTrue(conn._flags['become_success'])
        self.assertFalse(conn._flags['become_error'])
        self.assertFalse(conn._flags['become_nopasswd_error'])

        # test examining output for become failure
        conn._flags = dict(
            become_prompt = False,
            become_success = False,
            become_error = False,
            become_nopasswd_error = False,
        )

        pc.prompt = False
        pc.success_key = None
        output, unprocessed = conn._examine_output('source', 'state', 'line 1\nline 2\nincorrect password\n', True)
        self.assertEqual(output, 'line 1\nline 2\nincorrect password\n')
        self.assertEqual(unprocessed, '')
        self.assertFalse(conn._flags['become_prompt'])
        self.assertFalse(conn._flags['become_success'])
        self.assertTrue(conn._flags['become_error'])
        self.assertFalse(conn._flags['become_nopasswd_error'])

        # test examining output for missing password
        conn._flags = dict(
            become_prompt = False,
            become_success = False,
            become_error = False,
            become_nopasswd_error = False,
        )

        pc.prompt = False
        pc.success_key = None
        output, unprocessed = conn._examine_output('source', 'state', 'line 1\nbad password\n', True)
        self.assertEqual(output, 'line 1\nbad password\n')
        self.assertEqual(unprocessed, '')
        self.assertFalse(conn._flags['become_prompt'])
        self.assertFalse(conn._flags['become_success'])
        self.assertFalse(conn._flags['become_error'])
        self.assertTrue(conn._flags['become_nopasswd_error'])

    @patch('time.sleep')
    def test_plugins_connection_ssh_exec_command(self, mock_sleep):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = ssh.Connection(pc, new_stdin)
        conn._build_command = MagicMock()
        conn._exec_command = MagicMock()

        C.ANSIBLE_SSH_RETRIES = 9

        # test a regular, successful execution
        conn._exec_command.return_value = (0, 'stdout', '')
        res = conn.exec_command('ssh', 'some data')

        # test a retry, followed by success
        conn._exec_command.return_value = None
        conn._exec_command.side_effect = [(255, '', ''), (0, 'stdout', '')]
        res = conn.exec_command('ssh', 'some data')

        # test multiple failures
        conn._exec_command.side_effect = [(255, '', '')]*10
        self.assertRaises(AnsibleConnectionFailure, conn.exec_command, 'ssh', 'some data')

        # test other failure from exec_command
        conn._exec_command.side_effect = [Exception('bad')]*10
        self.assertRaises(Exception, conn.exec_command, 'ssh', 'some data')

    @patch('os.path.exists')
    def test_plugins_connection_ssh_put_file(self, mock_ospe):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = ssh.Connection(pc, new_stdin)
        conn._build_command = MagicMock()
        conn._run = MagicMock()

        mock_ospe.return_value = True
        conn._build_command.return_value = 'some command to run'
        conn._run.return_value = (0, '', '')
        conn.host = "some_host"

        # test with C.DEFAULT_SCP_IF_SSH enabled
        C.DEFAULT_SCP_IF_SSH = True
        res = conn.put_file('/path/to/in/file', '/path/to/dest/file')
        conn._run.assert_called_with('some command to run', None)

        res = conn.put_file(u'/path/to/in/file/with/unicode-fö〩', u'/path/to/dest/file/with/unicode-fö〩')
        conn._run.assert_called_with('some command to run', None)

        # test with C.DEFAULT_SCP_IF_SSH disabled
        C.DEFAULT_SCP_IF_SSH = False
        expected_in_data = b' '.join((b'put', to_bytes(pipes.quote('/path/to/in/file')), to_bytes(pipes.quote('/path/to/dest/file')))) + b'\n'
        res = conn.put_file('/path/to/in/file', '/path/to/dest/file')
        conn._run.assert_called_with('some command to run', expected_in_data)

        expected_in_data = b' '.join((b'put', to_bytes(pipes.quote('/path/to/in/file/with/unicode-fö〩')), to_bytes(pipes.quote('/path/to/dest/file/with/unicode-fö〩')))) + b'\n'
        res = conn.put_file(u'/path/to/in/file/with/unicode-fö〩', u'/path/to/dest/file/with/unicode-fö〩')
        conn._run.assert_called_with('some command to run', expected_in_data)

        # test that a non-zero rc raises an error
        conn._run.return_value = (1, 'stdout', 'some errors')
        self.assertRaises(AnsibleError, conn.put_file, '/path/to/bad/file', '/remote/path/to/file')

        # test that a not-found path raises an error
        mock_ospe.return_value = False
        conn._run.return_value = (0, 'stdout', '')
        self.assertRaises(AnsibleFileNotFound, conn.put_file, '/path/to/bad/file', '/remote/path/to/file')

    def test_plugins_connection_ssh_fetch_file(self):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = ssh.Connection(pc, new_stdin)
        conn._build_command = MagicMock()
        conn._run = MagicMock()

        conn._build_command.return_value = 'some command to run'
        conn._run.return_value = (0, '', '')
        conn.host = "some_host"

        # test with C.DEFAULT_SCP_IF_SSH enabled
        C.DEFAULT_SCP_IF_SSH = True
        res = conn.fetch_file('/path/to/in/file', '/path/to/dest/file')
        conn._run.assert_called_with('some command to run', None)

        res = conn.fetch_file(u'/path/to/in/file/with/unicode-fö〩', u'/path/to/dest/file/with/unicode-fö〩')
        conn._run.assert_called_with('some command to run', None)

        # test with C.DEFAULT_SCP_IF_SSH disabled
        C.DEFAULT_SCP_IF_SSH = False
        expected_in_data = b' '.join((b'get', to_bytes(pipes.quote('/path/to/in/file')), to_bytes(pipes.quote('/path/to/dest/file')))) + b'\n'
        res = conn.fetch_file('/path/to/in/file', '/path/to/dest/file')
        conn._run.assert_called_with('some command to run', expected_in_data)

        expected_in_data = b' '.join((b'get', to_bytes(pipes.quote('/path/to/in/file/with/unicode-fö〩')), to_bytes(pipes.quote('/path/to/dest/file/with/unicode-fö〩')))) + b'\n'
        res = conn.fetch_file(u'/path/to/in/file/with/unicode-fö〩', u'/path/to/dest/file/with/unicode-fö〩')
        conn._run.assert_called_with('some command to run', expected_in_data)

        # test that a non-zero rc raises an error
        conn._run.return_value = (1, 'stdout', 'some errors')
        self.assertRaises(AnsibleError, conn.fetch_file, '/path/to/bad/file', '/remote/path/to/file')


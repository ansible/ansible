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

from __future__ import annotations

from io import StringIO
from selectors import SelectorKey, EVENT_READ
import pytest


import unittest
from unittest.mock import patch, MagicMock, PropertyMock
from ansible.errors import AnsibleError, AnsibleConnectionFailure, AnsibleFileNotFound
import shlex
from ansible.module_utils.common.text.converters import to_bytes
from ansible.playbook.play_context import PlayContext
from ansible.plugins.connection import ssh
from ansible.plugins.loader import connection_loader, become_loader


class TestConnectionBaseClass(unittest.TestCase):

    def test_plugins_connection_ssh_module(self):
        play_context = PlayContext()
        play_context.prompt = (
            '[sudo via ansible, key=ouzmdnewuhucvuaabtjmweasarviygqq] password: '
        )
        in_stream = StringIO()

        self.assertIsInstance(ssh.Connection(play_context, in_stream), ssh.Connection)

    def test_plugins_connection_ssh_basic(self):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = ssh.Connection(pc, new_stdin)

        # connect just returns self, so assert that
        res = conn._connect()
        self.assertEqual(conn, res)

        conn.close()
        self.assertFalse(conn._connected)

    def test_plugins_connection_ssh__build_command(self):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get('ssh', pc, new_stdin)
        conn.get_option = MagicMock()
        conn.get_option.return_value = ""
        conn._build_command('ssh', 'ssh')

    def test_plugins_connection_ssh_exec_command(self):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get('ssh', pc, new_stdin)

        conn._build_command = MagicMock()
        conn._build_command.return_value = 'ssh something something'
        conn._run = MagicMock()
        conn._run.return_value = (0, 'stdout', 'stderr')
        conn.get_option = MagicMock()
        conn.get_option.return_value = True

        res, stdout, stderr = conn.exec_command('ssh')
        res, stdout, stderr = conn.exec_command('ssh', 'this is some data')

    def test_plugins_connection_ssh__examine_output(self):
        pc = PlayContext()
        new_stdin = StringIO()
        become_success_token = b'BECOME-SUCCESS-abcdefghijklmnopqrstuvxyz'

        conn = connection_loader.get('ssh', pc, new_stdin)
        conn.set_become_plugin(become_loader.get('sudo'))

        conn.become.check_password_prompt = MagicMock()
        conn.become.check_success = MagicMock()
        conn.become.check_incorrect_password = MagicMock()
        conn.become.check_missing_password = MagicMock()

        def _check_password_prompt(line):
            return b'foo' in line

        def _check_become_success(line):
            return become_success_token in line

        def _check_incorrect_password(line):
            return b'incorrect password' in line

        def _check_missing_password(line):
            return b'bad password' in line

        # test examining output for prompt
        conn._flags = dict(
            become_prompt=False,
            become_success=False,
            become_error=False,
            become_nopasswd_error=False,
        )

        pc.prompt = True

        # override become plugin
        conn.become.prompt = True
        conn.become.check_password_prompt = MagicMock(side_effect=_check_password_prompt)
        conn.become.check_success = MagicMock(side_effect=_check_become_success)
        conn.become.check_incorrect_password = MagicMock(side_effect=_check_incorrect_password)
        conn.become.check_missing_password = MagicMock(side_effect=_check_missing_password)

        def get_option(option):
            assert option == 'become_pass'
            return 'password'

        conn.become.get_option = get_option
        output, unprocessed = conn._examine_output(u'source', u'state', b'line 1\nline 2\nfoo\nline 3\nthis should be the remainder', False)
        self.assertEqual(output, b'line 1\nline 2\nline 3\n')
        self.assertEqual(unprocessed, b'this should be the remainder')
        self.assertTrue(conn._flags['become_prompt'])
        self.assertFalse(conn._flags['become_success'])
        self.assertFalse(conn._flags['become_error'])
        self.assertFalse(conn._flags['become_nopasswd_error'])

        # test examining output for become prompt
        conn._flags = dict(
            become_prompt=False,
            become_success=False,
            become_error=False,
            become_nopasswd_error=False,
        )

        pc.prompt = False
        conn.become.prompt = False
        pc.success_key = str(become_success_token)
        conn.become.success = str(become_success_token)
        output, unprocessed = conn._examine_output(u'source', u'state', b'line 1\nline 2\n%s\nline 3\n' % become_success_token, False)
        self.assertEqual(output, b'line 1\nline 2\nline 3\n')
        self.assertEqual(unprocessed, b'')
        self.assertFalse(conn._flags['become_prompt'])
        self.assertTrue(conn._flags['become_success'])
        self.assertFalse(conn._flags['become_error'])
        self.assertFalse(conn._flags['become_nopasswd_error'])

        # test we dont detect become success from ssh debug: lines
        conn._flags = dict(
            become_prompt=False,
            become_success=False,
            become_error=False,
            become_nopasswd_error=False,
        )

        pc.prompt = False
        conn.become.prompt = True
        pc.success_key = str(become_success_token)
        conn.become.success = str(become_success_token)
        output, unprocessed = conn._examine_output(u'source', u'state', b'line 1\nline 2\ndebug1: %s\nline 3\n' % become_success_token, False)
        self.assertEqual(output, b'line 1\nline 2\ndebug1: %s\nline 3\n' % become_success_token)
        self.assertEqual(unprocessed, b'')
        self.assertFalse(conn._flags['become_success'])

        # test examining output for become failure
        conn._flags = dict(
            become_prompt=False,
            become_success=False,
            become_error=False,
            become_nopasswd_error=False,
        )

        pc.prompt = False
        conn.become.prompt = False
        pc.success_key = None
        output, unprocessed = conn._examine_output(u'source', u'state', b'line 1\nline 2\nincorrect password\n', True)
        self.assertEqual(output, b'line 1\nline 2\nincorrect password\n')
        self.assertEqual(unprocessed, b'')
        self.assertFalse(conn._flags['become_prompt'])
        self.assertFalse(conn._flags['become_success'])
        self.assertTrue(conn._flags['become_error'])
        self.assertFalse(conn._flags['become_nopasswd_error'])

        # test examining output for missing password
        conn._flags = dict(
            become_prompt=False,
            become_success=False,
            become_error=False,
            become_nopasswd_error=False,
        )

        pc.prompt = False
        conn.become.prompt = False
        pc.success_key = None
        output, unprocessed = conn._examine_output(u'source', u'state', b'line 1\nbad password\n', True)
        self.assertEqual(output, b'line 1\nbad password\n')
        self.assertEqual(unprocessed, b'')
        self.assertFalse(conn._flags['become_prompt'])
        self.assertFalse(conn._flags['become_success'])
        self.assertFalse(conn._flags['become_error'])
        self.assertTrue(conn._flags['become_nopasswd_error'])

    @patch('time.sleep')
    @patch('os.path.exists')
    def test_plugins_connection_ssh_put_file(self, mock_ospe, mock_sleep):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get('ssh', pc, new_stdin)
        conn._build_command = MagicMock()
        conn._bare_run = MagicMock()

        mock_ospe.return_value = True
        conn._build_command.return_value = 'some command to run'
        conn._bare_run.return_value = (0, '', '')
        conn.host = "some_host"

        conn.set_option('reconnection_retries', 9)
        conn.set_option('ssh_transfer_method', None)  # default is smart

        # Test when SFTP works
        expected_in_data = b' '.join((b'put', to_bytes(shlex.quote('/path/to/in/file')), to_bytes(shlex.quote('/path/to/dest/file')))) + b'\n'
        conn.put_file('/path/to/in/file', '/path/to/dest/file')
        conn._bare_run.assert_called_with('some command to run', expected_in_data, checkrc=False)

        # Test filenames with unicode
        expected_in_data = b' '.join((b'put',
                                      to_bytes(shlex.quote('/path/to/in/file/with/unicode-fö〩')),
                                      to_bytes(shlex.quote('/path/to/dest/file/with/unicode-fö〩')))) + b'\n'
        conn.put_file(u'/path/to/in/file/with/unicode-fö〩', u'/path/to/dest/file/with/unicode-fö〩')
        conn._bare_run.assert_called_with('some command to run', expected_in_data, checkrc=False)

        # Test when SFTP doesn't work but SCP does
        conn._bare_run.side_effect = [(1, 'stdout', 'some errors'), (0, '', '')]
        conn.put_file('/path/to/in/file', '/path/to/dest/file')
        conn._bare_run.assert_called_with('some command to run', None, checkrc=False)
        conn._bare_run.side_effect = None

        # Test that a non-zero rc raises an error
        conn.set_option('ssh_transfer_method', 'sftp')
        conn._bare_run.return_value = (1, 'stdout', 'some errors')
        self.assertRaises(AnsibleError, conn.put_file, '/path/to/bad/file', '/remote/path/to/file')

        # Test that rc=255 raises an error
        conn._bare_run.return_value = (255, 'stdout', 'some errors')
        self.assertRaises(AnsibleConnectionFailure, conn.put_file, '/path/to/bad/file', '/remote/path/to/file')

        # Test that rc=256 raises an error
        conn._bare_run.return_value = (256, 'stdout', 'some errors')
        self.assertRaises(AnsibleError, conn.put_file, '/path/to/bad/file', '/remote/path/to/file')

        # Test that a not-found path raises an error
        mock_ospe.return_value = False
        conn._bare_run.return_value = (0, 'stdout', '')
        self.assertRaises(AnsibleFileNotFound, conn.put_file, '/path/to/bad/file', '/remote/path/to/file')

    @patch('time.sleep')
    def test_plugins_connection_ssh_fetch_file(self, mock_sleep):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get('ssh', pc, new_stdin)
        conn._build_command = MagicMock()
        conn._bare_run = MagicMock()
        conn._load_name = 'ssh'

        conn._build_command.return_value = 'some command to run'
        conn._bare_run.return_value = (0, '', '')
        conn.host = "some_host"

        conn.set_option('reconnection_retries', 9)
        conn.set_option('ssh_transfer_method', None)  # default is smart

        # Test when SFTP works
        expected_in_data = b' '.join((b'get', to_bytes(shlex.quote('/path/to/in/file')), to_bytes(shlex.quote('/path/to/dest/file')))) + b'\n'
        conn.set_options({})
        conn.fetch_file('/path/to/in/file', '/path/to/dest/file')
        conn._bare_run.assert_called_with('some command to run', expected_in_data, checkrc=False)

        # Test when SFTP doesn't work but SCP does
        conn._bare_run.side_effect = [(1, 'stdout', 'some errors'), (0, '', '')]
        conn.fetch_file('/path/to/in/file', '/path/to/dest/file')
        conn._bare_run.assert_called_with('some command to run', None, checkrc=False)
        conn._bare_run.side_effect = None

        # Test when filename is unicode
        expected_in_data = b' '.join((b'get',
                                      to_bytes(shlex.quote('/path/to/in/file/with/unicode-fö〩')),
                                      to_bytes(shlex.quote('/path/to/dest/file/with/unicode-fö〩')))) + b'\n'
        conn.fetch_file(u'/path/to/in/file/with/unicode-fö〩', u'/path/to/dest/file/with/unicode-fö〩')
        conn._bare_run.assert_called_with('some command to run', expected_in_data, checkrc=False)
        conn._bare_run.side_effect = None

        # Test that a non-zero rc raises an error
        conn.set_option('ssh_transfer_method', 'sftp')
        conn._bare_run.return_value = (1, 'stdout', 'some errors')
        self.assertRaises(AnsibleError, conn.fetch_file, '/path/to/bad/file', '/remote/path/to/file')

        # Test that rc=255 raises an error
        conn._bare_run.return_value = (255, 'stdout', 'some errors')
        self.assertRaises(AnsibleConnectionFailure, conn.fetch_file, '/path/to/bad/file', '/remote/path/to/file')

        # Test that rc=256 raises an error
        conn._bare_run.return_value = (256, 'stdout', 'some errors')
        self.assertRaises(AnsibleError, conn.fetch_file, '/path/to/bad/file', '/remote/path/to/file')


class MockSelector(object):
    def __init__(self):
        self.files_watched = 0
        self.register = MagicMock(side_effect=self._register)
        self.unregister = MagicMock(side_effect=self._unregister)
        self.close = MagicMock()
        self.get_map = MagicMock()
        self.select = MagicMock()

    def _register(self, *args, **kwargs):
        self.files_watched += 1

    def _unregister(self, *args, **kwargs):
        self.files_watched -= 1


@pytest.fixture
def mock_run_env(request, mocker):
    pc = PlayContext()
    new_stdin = StringIO()

    conn = connection_loader.get('ssh', pc, new_stdin)
    conn.set_become_plugin(become_loader.get('sudo'))
    conn._send_initial_data = MagicMock()
    conn._examine_output = MagicMock()
    conn._terminate_process = MagicMock()
    conn._load_name = 'ssh'
    conn.sshpass_pipe = [MagicMock(), MagicMock()]

    request.cls.pc = pc
    request.cls.conn = conn

    mock_popen_res = MagicMock()
    mock_popen_res.poll = MagicMock()
    mock_popen_res.wait = MagicMock()
    mock_popen_res.stdin = MagicMock()
    mock_popen_res.stdin.fileno.return_value = 1000
    mock_popen_res.stdout = MagicMock()
    mock_popen_res.stdout.fileno.return_value = 1001
    mock_popen_res.stderr = MagicMock()
    mock_popen_res.stderr.fileno.return_value = 1002
    mock_popen_res.returncode = 0
    request.cls.mock_popen_res = mock_popen_res

    mock_popen = mocker.patch('subprocess.Popen', return_value=mock_popen_res)
    request.cls.mock_popen = mock_popen

    request.cls.mock_selector = MockSelector()
    mocker.patch('selectors.DefaultSelector', lambda: request.cls.mock_selector)

    request.cls.mock_openpty = mocker.patch('pty.openpty')

    mocker.patch('fcntl.fcntl')
    mocker.patch('os.write')
    mocker.patch('os.close')


@pytest.mark.usefixtures('mock_run_env')
class TestSSHConnectionRun(object):
    # FIXME:
    # These tests are little more than a smoketest.  Need to enhance them
    # a bit to check that they're calling the relevant functions and making
    # complete coverage of the code paths
    def test_no_escalation(self):
        self.mock_popen_res.stdout.read.side_effect = [b"my_stdout\n", b"second_line"]
        self.mock_popen_res.stderr.read.side_effect = [b"my_stderr"]
        self.mock_selector.select.side_effect = [
            [(SelectorKey(self.mock_popen_res.stdout, 1001, [EVENT_READ], None), EVENT_READ)],
            [(SelectorKey(self.mock_popen_res.stdout, 1001, [EVENT_READ], None), EVENT_READ)],
            [(SelectorKey(self.mock_popen_res.stderr, 1002, [EVENT_READ], None), EVENT_READ)],
            []]
        self.mock_selector.get_map.side_effect = lambda: True

        return_code, b_stdout, b_stderr = self.conn._run("ssh", "this is input data")
        assert return_code == 0
        assert b_stdout == b'my_stdout\nsecond_line'
        assert b_stderr == b'my_stderr'
        assert self.mock_selector.register.called is True
        assert self.mock_selector.register.call_count == 2
        assert self.conn._send_initial_data.called is True
        assert self.conn._send_initial_data.call_count == 1
        assert self.conn._send_initial_data.call_args[0][1] == 'this is input data'

    def _password_with_prompt_examine_output(self, sourice, state, b_chunk, sudoable):
        if state == 'awaiting_prompt':
            self.conn._flags['become_prompt'] = True
        else:
            assert state == 'awaiting_escalation'
            self.conn._flags['become_success'] = True
        return (b'', b'')

    def test_password_with_prompt(self):
        # test with password prompting enabled
        self.pc.password = None
        self.conn.become.prompt = b'Password:'
        self.conn._examine_output.side_effect = self._password_with_prompt_examine_output
        self.mock_popen_res.stdout.read.side_effect = [b"Password:", b"Success", b""]
        self.mock_popen_res.stderr.read.side_effect = [b""]
        self.mock_selector.select.side_effect = [
            [(SelectorKey(self.mock_popen_res.stdout, 1001, [EVENT_READ], None), EVENT_READ)],
            [(SelectorKey(self.mock_popen_res.stdout, 1001, [EVENT_READ], None), EVENT_READ)],
            [(SelectorKey(self.mock_popen_res.stderr, 1002, [EVENT_READ], None), EVENT_READ),
             (SelectorKey(self.mock_popen_res.stdout, 1001, [EVENT_READ], None), EVENT_READ)],
            []]
        self.mock_selector.get_map.side_effect = lambda: True

        return_code, b_stdout, b_stderr = self.conn._run("ssh", "this is input data")
        assert return_code == 0
        assert b_stdout == b''
        assert b_stderr == b''
        assert self.mock_selector.register.called is True
        assert self.mock_selector.register.call_count == 2
        assert self.conn._send_initial_data.called is True
        assert self.conn._send_initial_data.call_count == 1
        assert self.conn._send_initial_data.call_args[0][1] == 'this is input data'

    def test_password_with_become(self):
        # test with some become settings
        self.pc.prompt = b'Password:'
        self.conn.become.prompt = b'Password:'
        self.pc.become = True
        self.pc.success_key = 'BECOME-SUCCESS-abcdefg'
        self.conn.become._id = 'abcdefg'
        self.conn._examine_output.side_effect = self._password_with_prompt_examine_output
        self.mock_popen_res.stdout.read.side_effect = [b"Password:", b"BECOME-SUCCESS-abcdefg", b"abc"]
        self.mock_popen_res.stderr.read.side_effect = [b"123"]
        self.mock_selector.select.side_effect = [
            [(SelectorKey(self.mock_popen_res.stdout, 1001, [EVENT_READ], None), EVENT_READ)],
            [(SelectorKey(self.mock_popen_res.stdout, 1001, [EVENT_READ], None), EVENT_READ)],
            [(SelectorKey(self.mock_popen_res.stderr, 1002, [EVENT_READ], None), EVENT_READ)],
            [(SelectorKey(self.mock_popen_res.stdout, 1001, [EVENT_READ], None), EVENT_READ)],
            []]
        self.mock_selector.get_map.side_effect = lambda: True

        return_code, b_stdout, b_stderr = self.conn._run("ssh", "this is input data")
        self.mock_popen_res.stdin.flush.assert_called_once_with()
        assert return_code == 0
        assert b_stdout == b'abc'
        assert b_stderr == b'123'
        assert self.mock_selector.register.called is True
        assert self.mock_selector.register.call_count == 2
        assert self.conn._send_initial_data.called is True
        assert self.conn._send_initial_data.call_count == 1
        assert self.conn._send_initial_data.call_args[0][1] == 'this is input data'

    def test_password_without_data(self):
        # simulate no data input but Popen using new pty's fails
        self.mock_popen.return_value = None
        self.mock_popen.side_effect = [OSError(), self.mock_popen_res]

        # simulate no data input
        self.mock_openpty.return_value = (98, 99)
        self.mock_popen_res.stdout.read.side_effect = [b"some data", b"", b""]
        self.mock_popen_res.stderr.read.side_effect = [b""]
        self.mock_selector.select.side_effect = [
            [(SelectorKey(self.mock_popen_res.stdout, 1001, [EVENT_READ], None), EVENT_READ)],
            [(SelectorKey(self.mock_popen_res.stdout, 1001, [EVENT_READ], None), EVENT_READ)],
            [(SelectorKey(self.mock_popen_res.stderr, 1002, [EVENT_READ], None), EVENT_READ)],
            [(SelectorKey(self.mock_popen_res.stdout, 1001, [EVENT_READ], None), EVENT_READ)],
            []]
        self.mock_selector.get_map.side_effect = lambda: True

        return_code, b_stdout, b_stderr = self.conn._run("ssh", "")
        assert return_code == 0
        assert b_stdout == b'some data'
        assert b_stderr == b''
        assert self.mock_selector.register.called is True
        assert self.mock_selector.register.call_count == 2
        assert self.conn._send_initial_data.called is False


@pytest.mark.usefixtures('mock_run_env')
class TestSSHConnectionRetries(object):
    def test_retry_then_success(self, monkeypatch):
        self.conn.set_option('host_key_checking', False)
        self.conn.set_option('reconnection_retries', 3)

        monkeypatch.setattr('time.sleep', lambda x: None)

        self.mock_popen_res.stdout.read.side_effect = [b"", b"my_stdout\n", b"second_line"]
        self.mock_popen_res.stderr.read.side_effect = [b"", b"my_stderr"]
        type(self.mock_popen_res).returncode = PropertyMock(side_effect=[255] * 3 + [0] * 4)

        self.mock_selector.select.side_effect = [
            [(SelectorKey(self.mock_popen_res.stdout, 1001, [EVENT_READ], None), EVENT_READ)],
            [(SelectorKey(self.mock_popen_res.stderr, 1002, [EVENT_READ], None), EVENT_READ)],
            [],
            [(SelectorKey(self.mock_popen_res.stdout, 1001, [EVENT_READ], None), EVENT_READ)],
            [(SelectorKey(self.mock_popen_res.stdout, 1001, [EVENT_READ], None), EVENT_READ)],
            [(SelectorKey(self.mock_popen_res.stderr, 1002, [EVENT_READ], None), EVENT_READ)],
            []
        ]
        self.mock_selector.get_map.side_effect = lambda: True

        self.conn._build_command = MagicMock()
        self.conn._build_command.return_value = 'ssh'

        return_code, b_stdout, b_stderr = self.conn.exec_command('ssh', 'some data')
        assert return_code == 0
        assert b_stdout == b'my_stdout\nsecond_line'
        assert b_stderr == b'my_stderr'

    def test_multiple_failures(self, monkeypatch):
        self.conn.set_option('host_key_checking', False)
        self.conn.set_option('reconnection_retries', 9)

        monkeypatch.setattr('time.sleep', lambda x: None)

        self.mock_popen_res.stdout.read.side_effect = [b""] * 10
        self.mock_popen_res.stderr.read.side_effect = [b""] * 10
        type(self.mock_popen_res).returncode = PropertyMock(side_effect=[255] * 30)

        self.mock_selector.select.side_effect = [
            [(SelectorKey(self.mock_popen_res.stdout, 1001, [EVENT_READ], None), EVENT_READ)],
            [(SelectorKey(self.mock_popen_res.stderr, 1002, [EVENT_READ], None), EVENT_READ)],
            [],
        ] * 10
        self.mock_selector.get_map.side_effect = lambda: True

        self.conn._build_command = MagicMock()
        self.conn._build_command.return_value = 'ssh'

        pytest.raises(AnsibleConnectionFailure, self.conn.exec_command, 'ssh', 'some data')
        assert self.mock_popen.call_count == 10

    def test_abitrary_exceptions(self, monkeypatch):
        self.conn.set_option('host_key_checking', False)
        self.conn.set_option('reconnection_retries', 9)

        monkeypatch.setattr('time.sleep', lambda x: None)

        self.conn._build_command = MagicMock()
        self.conn._build_command.return_value = 'ssh'

        self.mock_popen.side_effect = [Exception('bad')] * 10
        pytest.raises(Exception, self.conn.exec_command, 'ssh', 'some data')
        assert self.mock_popen.call_count == 10

    def test_put_file_retries(self, monkeypatch):
        self.conn.set_option('host_key_checking', False)
        self.conn.set_option('reconnection_retries', 3)

        monkeypatch.setattr('time.sleep', lambda x: None)
        monkeypatch.setattr('ansible.plugins.connection.ssh.os.path.exists', lambda x: True)

        self.mock_popen_res.stdout.read.side_effect = [b"", b"my_stdout\n", b"second_line"]
        self.mock_popen_res.stderr.read.side_effect = [b"", b"my_stderr"]
        type(self.mock_popen_res).returncode = PropertyMock(side_effect=[255] * 4 + [0] * 4)

        self.mock_selector.select.side_effect = [
            [(SelectorKey(self.mock_popen_res.stdout, 1001, [EVENT_READ], None), EVENT_READ)],
            [(SelectorKey(self.mock_popen_res.stderr, 1002, [EVENT_READ], None), EVENT_READ)],
            [],
            [(SelectorKey(self.mock_popen_res.stdout, 1001, [EVENT_READ], None), EVENT_READ)],
            [(SelectorKey(self.mock_popen_res.stdout, 1001, [EVENT_READ], None), EVENT_READ)],
            [(SelectorKey(self.mock_popen_res.stderr, 1002, [EVENT_READ], None), EVENT_READ)],
            []
        ]
        self.mock_selector.get_map.side_effect = lambda: True

        self.conn._build_command = MagicMock()
        self.conn._build_command.return_value = 'sftp'

        return_code, b_stdout, b_stderr = self.conn.put_file('/path/to/in/file', '/path/to/dest/file')
        assert return_code == 0
        assert b_stdout == b"my_stdout\nsecond_line"
        assert b_stderr == b"my_stderr"
        assert self.mock_popen.call_count == 2

    def test_fetch_file_retries(self, monkeypatch):
        self.conn.set_option('host_key_checking', False)
        self.conn.set_option('reconnection_retries', 3)

        monkeypatch.setattr('time.sleep', lambda x: None)

        self.mock_popen_res.stdout.read.side_effect = [b"", b"my_stdout\n", b"second_line"]
        self.mock_popen_res.stderr.read.side_effect = [b"", b"my_stderr"]
        type(self.mock_popen_res).returncode = PropertyMock(side_effect=[255] * 4 + [0] * 4)

        self.mock_selector.select.side_effect = [
            [(SelectorKey(self.mock_popen_res.stdout, 1001, [EVENT_READ], None), EVENT_READ)],
            [(SelectorKey(self.mock_popen_res.stderr, 1002, [EVENT_READ], None), EVENT_READ)],
            [],
            [(SelectorKey(self.mock_popen_res.stdout, 1001, [EVENT_READ], None), EVENT_READ)],
            [(SelectorKey(self.mock_popen_res.stdout, 1001, [EVENT_READ], None), EVENT_READ)],
            [(SelectorKey(self.mock_popen_res.stderr, 1002, [EVENT_READ], None), EVENT_READ)],
            []
        ]
        self.mock_selector.get_map.side_effect = lambda: True

        self.conn._build_command = MagicMock()
        self.conn._build_command.return_value = 'sftp'

        return_code, b_stdout, b_stderr = self.conn.fetch_file('/path/to/in/file', '/path/to/dest/file')
        assert return_code == 0
        assert b_stdout == b"my_stdout\nsecond_line"
        assert b_stderr == b"my_stderr"
        assert self.mock_popen.call_count == 2

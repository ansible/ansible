from io import StringIO
import pytest

from ansible import constants as C
from ansible.errors import AnsibleAuthenticationFailure
from ansible.compat.selectors import SelectorKey, EVENT_READ
from units.compat import unittest
from units.compat.mock import patch, MagicMock, PropertyMock
from ansible.errors import AnsibleError, AnsibleConnectionFailure, AnsibleFileNotFound
from ansible.module_utils.six.moves import shlex_quote
from ansible.module_utils._text import to_bytes
from ansible.playbook.play_context import PlayContext
from ansible.plugins.connection import aws_ssm
from ansible.plugins.loader import connection_loader, become_loader




class TestConnectionBaseClass(unittest.TestCase):

    @patch('os.path.exists')
    @patch('subprocess.Popen')
    @patch('select.poll')
    def test_plugins_connection_aws_ssm_start_session(self, s_poll, s_popen, mock_ospe):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get('aws_ssm', pc, new_stdin)

        conn.get_option = MagicMock()
        conn.get_option.side_effect = ['i1234', 'executable', 'i1234', 'abcd']
        conn.host = 'abc'
        mock_ospe.return_value = True
        s_popen.return_value.stdin.write = MagicMock()
        s_poll.return_value = MagicMock()
        s_poll.return_value.register = MagicMock()
        s_popen.return_value.poll = MagicMock()
        s_popen.return_value.poll.return_value = None
        conn._stdin_readline = MagicMock()
        conn._stdin_readline.return_value = 'abc123'
        conn.SESSION_START = 'abc'

        conn.start_session()

        
    @patch('random.choice')
    def test_plugins_connection_aws_ssm_exec_command(self, r_choice):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get('aws_ssm', pc, new_stdin)

        r_choice.side_effect = ['a','a','a','a','a','b','b','b','b','b']

        conn._connected = True
        conn.MARK_LENGTH = 5
        conn._session = MagicMock()
        conn._session.stdin.write = MagicMock()
        conn._flush_stderr = MagicMock()
        conn._session.poll = MagicMock()
        conn._session.poll.return_value = None
        conn._poll_stdout = MagicMock()
        conn._poll_stdout.poll = MagicMock()
        conn._poll_stdout.poll.return_value = True
        conn._session.stdout = MagicMock()
        conn._session.stdout.readline = MagicMock()
        conn._session.stdout.readline.side_effect = iter(['aaaaa\n', 'Hi\n', '0\n', 'bbbbb\n'])
        conn.get_option = MagicMock()
        conn.get_option.return_value = 1

        res, stdout, stderr = conn.exec_command('aws_ssm')

    @patch('os.path.exists')
    def test_plugins_connection_aws_ssm_put_file(self, mock_ospe):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get('aws_ssm', pc, new_stdin)

        conn._connect = MagicMock()
        conn._file_transport_command = MagicMock()
        conn._file_transport_command.return_value = (0, 'stdout', 'stderr')

        res, stdout, stderr = conn.put_file('/in/file', '/out/file')

    def test_plugins_connection_aws_ssm_fetch_file(self):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get('aws_ssm', pc, new_stdin)

        conn._connect = MagicMock()
        conn._file_transport_command = MagicMock()
        conn._file_transport_command.return_value = (0, 'stdout', 'stderr')

        res, stdout, stderr = conn.fetch_file('/in/file', '/out/file')

    
    @patch('subprocess.check_output')
    def test_plugins_connection_aws_transport_command(self, s_check_output):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get('aws_ssm', pc, new_stdin)

        conn.get_option = MagicMock()
        conn.get_option.return_value = 1
        
        conn.exec_command = MagicMock()
        conn.exec_command.return_value = (0, 'stdout', 'stderr')

        res, stdout, stderr = conn._file_transport_command('/in/file', '/out/file', 'abc')


    @patch('subprocess.check_output')
    def test_plugins_connection_aws_ssm_close(self, s_check_output):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get('aws_ssm', pc, new_stdin)

        conn._session_id = True

        conn.get_option = MagicMock()
        conn.get_option.side_effect = ["i-12345","/abc", "pqr"]

        conn._session = MagicMock()
        conn._session.terminate = MagicMock()
        conn._session.communicate = MagicMock()

        conn.close()

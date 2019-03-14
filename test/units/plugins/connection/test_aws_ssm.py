from io import StringIO
import pytest
import sys
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

@pytest.mark.skipif(sys.version_info < (2,7), reason="requires python 2.7 or higher")
class TestConnectionBaseClass(unittest.TestCase):

    @patch('os.path.exists')
    @patch('subprocess.Popen')
    @patch('select.poll')
    @patch('boto3.client')
    def test_plugins_connection_aws_ssm_start_session(self, boto_client, s_poll, s_popen, mock_ospe):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get('aws_ssm', pc, new_stdin)
        conn.get_option = MagicMock()
        conn.get_option.side_effect = ['i1234', 'executable', 'abcd', 'i1234']
        conn.host = 'abc'
        mock_ospe.return_value = True
        boto3 = MagicMock()
        boto3.client('ssm').return_value = MagicMock()
        conn.start_session = MagicMock()
        conn._session_id = MagicMock()
        conn._session_id.return_value = 's1'
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
        r_choice.side_effect = ['a', 'a', 'a', 'a', 'a', 'b', 'b', 'b', 'b', 'b']
        conn._connected = True
        conn.MARK_LENGTH = 5
        conn._session = MagicMock()
        conn._session.stdin.write = MagicMock()
        conn._flush_stderr = MagicMock()
        conn._windows = MagicMock()
        conn._windows.return_value = True
        sudoable = True
        conn._session.poll = MagicMock()
        conn._session.poll.return_value = None
        remaining = 0
        conn._timeout = MagicMock()
        conn._poll_stdout = MagicMock()
        conn._poll_stdout.poll = MagicMock()
        conn._poll_stdout.poll.return_value = True
        conn._session.stdout = MagicMock()
        conn._session.stdout.readline = MagicMock()
        begin = True
        mark_end = 'a'
        line = ['a', 'b']
        conn._post_process = MagicMock()
        conn._post_process.return_value = 'test'
        conn._session.stdout.readline.side_effect = iter(['aaaaa\n', 'Hi\n', '0\n', 'bbbbb\n'])
        conn.get_option = MagicMock()
        conn.get_option.return_value = 1
        cmd = MagicMock()
        returncode = 'a'
        stdout = 'b'
        return (returncode, stdout, conn._flush_stderr)

    @patch('os.path.exists')
    def test_plugins_connection_aws_ssm_put_file(self, mock_ospe):
        skipif
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
    @patch('boto3.client')
    def test_plugins_connection_file_transport_command(self, boto_client, s_check_output):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get('aws_ssm', pc, new_stdin)
        conn.get_option = MagicMock()
        conn.get_option.side_effect = ['1', '2', '3', '4', '5']
        conn._get_url = MagicMock()
        conn._get_url.side_effect = ['url1', 'url2']
        boto3 = MagicMock()
        boto3.client('s3').return_value = MagicMock()
        conn.get_option.return_value = 1
        ssm_action = 'get'
        get_command = MagicMock()
        put_command = MagicMock()
        conn.exec_command = MagicMock()
        conn.exec_command.return_value = (put_command, None, False)
        conn.download_fileobj = MagicMock()
        (returncode, stdout, stderr) = conn.exec_command(put_command, in_data=None, sudoable=False)
        returncode = 0
        (returncode, stdout, stderr) = conn.exec_command(get_command, in_data=None, sudoable=False)

    @patch('subprocess.check_output')
    def test_plugins_connection_aws_ssm_close(self, s_check_output):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get('aws_ssm', pc, new_stdin)
        conn._session_id = True
        conn.get_option = MagicMock()
        conn.get_option.side_effect = ["i-12345", "/abc", "pqr"]
        conn._session = MagicMock()
        conn._session.terminate = MagicMock()
        conn._session.communicate = MagicMock()
        conn._terminate_session = MagicMock()
        conn._terminate_session.return_value = ''
        conn._session_id = MagicMock()
        conn._session_id.return_value = 'a'
        conn._client = MagicMock()
        conn.close()

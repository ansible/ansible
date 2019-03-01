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

    def test_plugins_connection_aws_transport_command(self):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get('aws_ssm', pc, new_stdin)

        

    def test_plugins_connection_aws_ssm_close(self):
        pc = PlayContext()
        new_stdin = StringIO()
        conn = connection_loader.get('aws_ssm', pc, new_stdin)

        conn._session_id = MagicMock()
        conn.get_option = MagicMock()
        conn._connect = MagicMock()

        conn.close()
        self.assertFalse(conn._connected)
        
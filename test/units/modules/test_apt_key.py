from __future__ import annotations

import os

from unittest.mock import patch, Mock
import unittest

from ansible.modules import apt_key


def returnc(x):
    return 'C'


class AptKeyTestCase(unittest.TestCase):

    @patch.object(apt_key, 'apt_key_bin', '/usr/bin/apt-key')
    @patch.object(apt_key, 'lang_env', returnc)
    @patch.dict(os.environ, {'HTTP_PROXY': 'proxy.example.com'})
    def test_import_key_with_http_proxy(self):
        m_mock = Mock()
        m_mock.run_command.return_value = (0, '', '')
        apt_key.import_key(
            m_mock, keyring=None, keyserver='keyserver.example.com',
            key_id='0xDEADBEEF')
        self.assertEqual(
            m_mock.run_command.call_args_list[0][0][0],
            '/usr/bin/apt-key adv --no-tty --keyserver keyserver.example.com'
            ' --keyserver-options http-proxy=proxy.example.com'
            ' --recv 0xDEADBEEF'
        )

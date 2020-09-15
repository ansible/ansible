# (c) 2018 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

from ansible.module_utils.six.moves.urllib.error import HTTPError
from units.compat import mock
from units.compat import unittest

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.connection import ConnectionError
from ansible.module_utils.six import BytesIO, StringIO
from ansible.plugins.httpapi.checkpoint import HttpApi

EXPECTED_BASE_HEADERS = {
    'Content-Type': 'application/json'
}


class FakeCheckpointHttpApiPlugin(HttpApi):
    def __init__(self, conn):
        super(FakeCheckpointHttpApiPlugin, self).__init__(conn)


class TestCheckpointHttpApi(unittest.TestCase):

    def setUp(self):
        self.connection_mock = mock.Mock()
        self.checkpoint_plugin = FakeCheckpointHttpApiPlugin(self.connection_mock)
        self.checkpoint_plugin._load_name = 'httpapi'

    def test_login_raises_exception_when_username_and_password_are_not_provided(self):
        with self.assertRaises(AnsibleConnectionFailure) as res:
            self.checkpoint_plugin.login(None, None)
        assert 'Username and password are required' in str(res.exception)

    def test_login_raises_exception_when_invalid_response(self):
        self.connection_mock.send.return_value = self._connection_response(
            {'NOSIDKEY': 'NOSIDVALUE'}
        )

        with self.assertRaises(ConnectionError) as res:
            self.checkpoint_plugin.login('foo', 'bar')

        assert 'Server returned response without token info during connection authentication' in str(res.exception)

    def test_send_request_should_return_error_info_when_http_error_raises(self):
        self.connection_mock.send.side_effect = HTTPError('http://testhost.com', 500, '', {},
                                                          StringIO('{"errorMessage": "ERROR"}'))

        resp = self.checkpoint_plugin.send_request('/test', None)

        assert resp == (500, {'errorMessage': 'ERROR'})

    @staticmethod
    def _connection_response(response, status=200):
        response_mock = mock.Mock()
        response_mock.getcode.return_value = status
        response_text = json.dumps(response) if type(response) is dict else response
        response_data = BytesIO(response_text.encode() if response_text else ''.encode())
        return response_mock, response_data

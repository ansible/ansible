# Copyright (c) 2018 Cisco and/or its affiliates.
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

import json

from ansible.module_utils.six.moves.urllib.error import HTTPError

from ansible.compat.tests import mock
from ansible.compat.tests import unittest

from ansible.compat.tests.mock import mock_open, patch
from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.connection import ConnectionError
from ansible.module_utils.network.ftd.common import HTTPMethod, ResponseParams
from ansible.module_utils.network.ftd.fdm_swagger_client import SpecProp, FdmSwaggerParser
from ansible.module_utils.six import BytesIO, PY3, StringIO
from ansible.plugins.httpapi.ftd import HttpApi

if PY3:
    BUILTINS_NAME = 'builtins'
else:
    BUILTINS_NAME = '__builtin__'

EXPECTED_BASE_HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}


class FakeFtdHttpApiPlugin(HttpApi):
    def __init__(self, conn):
        super(FakeFtdHttpApiPlugin, self).__init__(conn)
        self.hostvars = {
            'token_path': '/testLoginUrl',
            'spec_path': '/testSpecUrl'
        }

    def get_option(self, var):
        return self.hostvars[var]


class TestFtdHttpApi(unittest.TestCase):

    def setUp(self):
        self.connection_mock = mock.Mock()
        self.ftd_plugin = FakeFtdHttpApiPlugin(self.connection_mock)
        self.ftd_plugin.access_token = 'ACCESS_TOKEN'
        self.ftd_plugin._load_name = 'httpapi'

    def test_login_should_request_tokens_when_no_refresh_token(self):
        self.connection_mock.send.return_value = self._connection_response(
            {'access_token': 'ACCESS_TOKEN', 'refresh_token': 'REFRESH_TOKEN'}
        )

        self.ftd_plugin.login('foo', 'bar')

        assert 'ACCESS_TOKEN' == self.ftd_plugin.access_token
        assert 'REFRESH_TOKEN' == self.ftd_plugin.refresh_token
        assert {'Authorization': 'Bearer ACCESS_TOKEN'} == self.ftd_plugin.connection._auth
        expected_body = json.dumps({'grant_type': 'password', 'username': 'foo', 'password': 'bar'})
        self.connection_mock.send.assert_called_once_with(mock.ANY, expected_body, headers=mock.ANY, method=mock.ANY)

    def test_login_should_update_tokens_when_refresh_token_exists(self):
        self.ftd_plugin.refresh_token = 'REFRESH_TOKEN'
        self.connection_mock.send.return_value = self._connection_response(
            {'access_token': 'NEW_ACCESS_TOKEN', 'refresh_token': 'NEW_REFRESH_TOKEN'}
        )

        self.ftd_plugin.login('foo', 'bar')

        assert 'NEW_ACCESS_TOKEN' == self.ftd_plugin.access_token
        assert 'NEW_REFRESH_TOKEN' == self.ftd_plugin.refresh_token
        assert {'Authorization': 'Bearer NEW_ACCESS_TOKEN'} == self.ftd_plugin.connection._auth
        expected_body = json.dumps({'grant_type': 'refresh_token', 'refresh_token': 'REFRESH_TOKEN'})
        self.connection_mock.send.assert_called_once_with(mock.ANY, expected_body, headers=mock.ANY, method=mock.ANY)

    def test_login_should_use_host_variable_when_set(self):
        temp_token_path = self.ftd_plugin.hostvars['token_path']
        self.ftd_plugin.hostvars['token_path'] = '/testFakeLoginUrl'
        self.connection_mock.send.return_value = self._connection_response(
            {'access_token': 'ACCESS_TOKEN', 'refresh_token': 'REFRESH_TOKEN'}
        )

        self.ftd_plugin.login('foo', 'bar')

        self.connection_mock.send.assert_called_once_with('/testFakeLoginUrl', mock.ANY, headers=mock.ANY,
                                                          method=mock.ANY)
        self.ftd_plugin.hostvars['token_path'] = temp_token_path

    def test_login_raises_exception_when_no_refresh_token_and_no_credentials(self):
        with self.assertRaises(AnsibleConnectionFailure) as res:
            self.ftd_plugin.login(None, None)
        assert 'Username and password are required' in str(res.exception)

    def test_login_raises_exception_when_invalid_response(self):
        self.connection_mock.send.return_value = self._connection_response(
            {'no_access_token': 'ACCESS_TOKEN'}
        )

        with self.assertRaises(ConnectionError) as res:
            self.ftd_plugin.login('foo', 'bar')

        assert 'Server returned response without token info during connection authentication' in str(res.exception)

    def test_login_raises_exception_when_http_error(self):
        self.connection_mock.send.side_effect = HTTPError('http://testhost.com', 400, '', {},
                                                          StringIO('{"message": "Failed to authenticate user"}'))

        with self.assertRaises(ConnectionError) as res:
            self.ftd_plugin.login('foo', 'bar')

        assert 'Failed to authenticate user' in str(res.exception)

    def test_logout_should_revoke_tokens(self):
        self.ftd_plugin.access_token = 'ACCESS_TOKEN_TO_REVOKE'
        self.ftd_plugin.refresh_token = 'REFRESH_TOKEN_TO_REVOKE'
        self.connection_mock.send.return_value = self._connection_response(None)

        self.ftd_plugin.logout()

        assert self.ftd_plugin.access_token is None
        assert self.ftd_plugin.refresh_token is None
        expected_body = json.dumps({'grant_type': 'revoke_token', 'access_token': 'ACCESS_TOKEN_TO_REVOKE',
                                    'token_to_revoke': 'REFRESH_TOKEN_TO_REVOKE'})
        self.connection_mock.send.assert_called_once_with(mock.ANY, expected_body, headers=mock.ANY, method=mock.ANY)

    def test_send_request_should_send_correct_request(self):
        exp_resp = {'id': '123', 'name': 'foo'}
        self.connection_mock.send.return_value = self._connection_response(exp_resp)

        resp = self.ftd_plugin.send_request('/test/{objId}', HTTPMethod.PUT,
                                            body_params={'name': 'foo'},
                                            path_params={'objId': '123'},
                                            query_params={'at': 0})

        assert {ResponseParams.SUCCESS: True, ResponseParams.STATUS_CODE: 200,
                ResponseParams.RESPONSE: exp_resp} == resp
        self.connection_mock.send.assert_called_once_with('/test/123?at=0', '{"name": "foo"}', method=HTTPMethod.PUT,
                                                          headers=EXPECTED_BASE_HEADERS)

    def test_send_request_should_return_empty_dict_when_no_response_data(self):
        self.connection_mock.send.return_value = self._connection_response(None)

        resp = self.ftd_plugin.send_request('/test', HTTPMethod.GET)

        assert {ResponseParams.SUCCESS: True, ResponseParams.STATUS_CODE: 200, ResponseParams.RESPONSE: {}} == resp
        self.connection_mock.send.assert_called_once_with('/test', None, method=HTTPMethod.GET,
                                                          headers=EXPECTED_BASE_HEADERS)

    def test_send_request_should_return_error_info_when_http_error_raises(self):
        self.connection_mock.send.side_effect = HTTPError('http://testhost.com', 500, '', {},
                                                          StringIO('{"errorMessage": "ERROR"}'))

        resp = self.ftd_plugin.send_request('/test', HTTPMethod.GET)

        assert {ResponseParams.SUCCESS: False, ResponseParams.STATUS_CODE: 500,
                ResponseParams.RESPONSE: {'errorMessage': 'ERROR'}} == resp

    def test_send_request_raises_exception_when_invalid_response(self):
        self.connection_mock.send.return_value = self._connection_response('nonValidJson')

        with self.assertRaises(ConnectionError) as res:
            self.ftd_plugin.send_request('/test', HTTPMethod.GET)

        assert 'Invalid JSON response' in str(res.exception)

    def test_handle_httperror_should_update_tokens_and_retry_on_auth_errors(self):
        self.ftd_plugin.refresh_token = 'REFRESH_TOKEN'
        self.connection_mock.send.return_value = self._connection_response(
            {'access_token': 'NEW_ACCESS_TOKEN', 'refresh_token': 'NEW_REFRESH_TOKEN'}
        )

        retry = self.ftd_plugin.handle_httperror(HTTPError('http://testhost.com', 401, '', {}, None))

        assert retry
        assert 'NEW_ACCESS_TOKEN' == self.ftd_plugin.access_token
        assert 'NEW_REFRESH_TOKEN' == self.ftd_plugin.refresh_token

    def test_handle_httperror_should_not_retry_on_non_auth_errors(self):
        assert not self.ftd_plugin.handle_httperror(HTTPError('http://testhost.com', 500, '', {}, None))

    def test_handle_httperror_should_not_retry_when_ignoring_http_errors(self):
        self.ftd_plugin._ignore_http_errors = True
        assert not self.ftd_plugin.handle_httperror(HTTPError('http://testhost.com', 401, '', {}, None))

    @patch('os.path.isdir', mock.Mock(return_value=False))
    def test_download_file(self):
        self.connection_mock.send.return_value = self._connection_response('File content')

        open_mock = mock_open()
        with patch('%s.open' % BUILTINS_NAME, open_mock):
            self.ftd_plugin.download_file('/files/1', '/tmp/test.txt')

        open_mock.assert_called_once_with('/tmp/test.txt', 'wb')
        open_mock().write.assert_called_once_with(b'File content')

    @patch('os.path.isdir', mock.Mock(return_value=True))
    def test_download_file_should_extract_filename_from_headers(self):
        filename = 'test_file.txt'
        response = mock.Mock()
        response.info.return_value = {'Content-Disposition': 'attachment; filename="%s"' % filename}
        dummy, response_data = self._connection_response('File content')
        self.connection_mock.send.return_value = response, response_data

        open_mock = mock_open()
        with patch('%s.open' % BUILTINS_NAME, open_mock):
            self.ftd_plugin.download_file('/files/1', '/tmp/')

        open_mock.assert_called_once_with('/tmp/%s' % filename, 'wb')
        open_mock().write.assert_called_once_with(b'File content')

    @patch('os.path.basename', mock.Mock(return_value='test.txt'))
    @patch('ansible.plugins.httpapi.ftd.encode_multipart_formdata',
           mock.Mock(return_value=('--Encoded data--', 'multipart/form-data')))
    def test_upload_file(self):
        self.connection_mock.send.return_value = self._connection_response({'id': '123'})

        open_mock = mock_open()
        with patch('%s.open' % BUILTINS_NAME, open_mock):
            resp = self.ftd_plugin.upload_file('/tmp/test.txt', '/files')

        assert {'id': '123'} == resp
        exp_headers = dict(EXPECTED_BASE_HEADERS)
        exp_headers['Content-Length'] = len('--Encoded data--')
        exp_headers['Content-Type'] = 'multipart/form-data'
        self.connection_mock.send.assert_called_once_with('/files', data='--Encoded data--',
                                                          headers=exp_headers, method=HTTPMethod.POST)
        open_mock.assert_called_once_with('/tmp/test.txt', 'rb')

    @patch('os.path.basename', mock.Mock(return_value='test.txt'))
    @patch('ansible.plugins.httpapi.ftd.encode_multipart_formdata',
           mock.Mock(return_value=('--Encoded data--', 'multipart/form-data')))
    def test_upload_file_raises_exception_when_invalid_response(self):
        self.connection_mock.send.return_value = self._connection_response('invalidJsonResponse')

        open_mock = mock_open()
        with patch('%s.open' % BUILTINS_NAME, open_mock):
            with self.assertRaises(ConnectionError) as res:
                self.ftd_plugin.upload_file('/tmp/test.txt', '/files')

        assert 'Invalid JSON response' in str(res.exception)

    @patch.object(FdmSwaggerParser, 'parse_spec')
    def test_get_operation_spec(self, parse_spec_mock):
        self.connection_mock.send.return_value = self._connection_response(None)
        parse_spec_mock.return_value = {
            SpecProp.OPERATIONS: {'testOp': 'Specification for testOp'}
        }

        assert 'Specification for testOp' == self.ftd_plugin.get_operation_spec('testOp')
        assert self.ftd_plugin.get_operation_spec('nonExistingTestOp') is None

    @patch.object(FdmSwaggerParser, 'parse_spec')
    def test_get_model_spec(self, parse_spec_mock):
        self.connection_mock.send.return_value = self._connection_response(None)
        parse_spec_mock.return_value = {
            SpecProp.MODELS: {'TestModel': 'Specification for TestModel'}
        }

        assert 'Specification for TestModel' == self.ftd_plugin.get_model_spec('TestModel')
        assert self.ftd_plugin.get_model_spec('NonExistingTestModel') is None

    @patch.object(FdmSwaggerParser, 'parse_spec')
    def test_get_model_spec(self, parse_spec_mock):
        self.connection_mock.send.return_value = self._connection_response(None)
        operation1 = {'modelName': 'TestModel'}
        op_model_name_is_none = {'modelName': None}
        op_without_model_name = {'url': 'testUrl'}

        parse_spec_mock.return_value = {
            SpecProp.MODEL_OPERATIONS: {
                'TestModel': {
                    'testOp1': operation1,
                    'testOp2': 'spec2'
                },
                'TestModel2': {
                    'testOp10': 'spec10',
                    'testOp20': 'spec20'
                }
            },
            SpecProp.OPERATIONS: {
                'testOp1': operation1,
                'testOp10': {
                    'modelName': 'TestModel2'
                },
                'testOpWithoutModelName': op_without_model_name,
                'testOpModelNameIsNone': op_model_name_is_none
            }
        }

        assert {'testOp1': operation1, 'testOp2': 'spec2'} == self.ftd_plugin.get_operation_specs_by_model_name(
            'TestModel')
        assert None is self.ftd_plugin.get_operation_specs_by_model_name(
            'testOpModelNameIsNone')

        assert None is self.ftd_plugin.get_operation_specs_by_model_name(
            'testOpWithoutModelName')

        assert self.ftd_plugin.get_operation_specs_by_model_name('nonExistingOperation') is None

    @staticmethod
    def _connection_response(response, status=200):
        response_mock = mock.Mock()
        response_mock.getcode.return_value = status
        response_text = json.dumps(response) if type(response) is dict else response
        response_data = BytesIO(response_text.encode() if response_text else ''.encode())
        return response_mock, response_data

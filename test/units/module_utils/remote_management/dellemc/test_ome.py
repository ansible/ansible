# -*- coding: utf-8 -*-

#
# Dell EMC OpenManage Ansible Modules
# Version 2.0
# Copyright (C) 2019 Dell Inc.

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# All rights reserved. Dell, EMC, and other trademarks are trademarks of Dell Inc. or its subsidiaries.
# Other trademarks may be trademarks of their respective owners.
#

from __future__ import absolute_import

import pytest
from ansible.module_utils.urls import ConnectionError, SSLValidationError
from ansible.module_utils.six.moves.urllib.error import URLError, HTTPError
from ansible.module_utils.remote_management.dellemc.ome import RestOME
from units.compat.mock import MagicMock
import json


class TestRestOME(object):
    @pytest.fixture
    def mock_response(self):
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.headers = mock_response.getheaders.return_value = {'X-Auth-Token': 'token_id'}
        mock_response.read.return_value = json.dumps({"value": "data"})
        return mock_response

    def test_invoke_request_with_session(self, mock_response, mocker):
        mocker.patch('ansible.module_utils.remote_management.dellemc.ome.open_url',
                     return_value=mock_response)
        module_params = {'hostname': '192.168.0.1', 'username': 'username',
                         'password': 'password', "port": 443}
        req_session = True
        with RestOME(module_params, req_session) as obj:
            response = obj.invoke_request("/testpath", "GET")
        assert response.status_code == 200
        assert response.json_data == {"value": "data"}
        assert response.success is True

    def test_invoke_request_without_session(self, mock_response, mocker):
        mocker.patch('ansible.module_utils.remote_management.dellemc.ome.open_url',
                     return_value=mock_response)
        module_params = {'hostname': '192.168.0.1', 'username': 'username',
                         'password': 'password', "port": 443}
        req_session = False
        with RestOME(module_params, req_session) as obj:
            response = obj.invoke_request("/testpath", "GET")
        assert response.status_code == 200
        assert response.json_data == {"value": "data"}
        assert response.success is True

    @pytest.mark.parametrize("exc", [URLError, SSLValidationError, ConnectionError])
    def test_invoke_request_error_case_handling(self, exc, mock_response, mocker):
        open_url_mock = mocker.patch('ansible.module_utils.remote_management.dellemc.ome.open_url',
                                     return_value=mock_response)
        open_url_mock.side_effect = exc("test")
        module_params = {'hostname': '192.168.0.1', 'username': 'username',
                         'password': 'password', "port": 443}
        req_session = False
        with pytest.raises(exc) as e:
            with RestOME(module_params, req_session) as obj:
                obj.invoke_request("/testpath", "GET")

    def test_invoke_request_http_error_handling(self, mock_response, mocker):
        open_url_mock = mocker.patch('ansible.module_utils.remote_management.dellemc.ome.open_url',
                                     return_value=mock_response)
        open_url_mock.side_effect = HTTPError('http://testhost.com/', 400,
                                              'Bad Request Error', {}, None)
        module_params = {'hostname': '192.168.0.1', 'username': 'username',
                         'password': 'password', "port": 443}
        req_session = False
        with pytest.raises(HTTPError) as e:
            with RestOME(module_params, req_session) as obj:
                obj.invoke_request("/testpath", "GET")

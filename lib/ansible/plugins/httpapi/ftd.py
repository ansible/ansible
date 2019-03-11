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

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = """
---
author: Ansible Networking Team
httpapi : ftd
short_description: HttpApi Plugin for Cisco ASA Firepower device
description:
  - This HttpApi plugin provides methods to connect to Cisco ASA firepower
    devices over a HTTP(S)-based api.
version_added: "2.7"
options:
  token_path:
    type: str
    description:
      - Specifies the api token path of the FTD device
    vars:
      - name: ansible_httpapi_ftd_token_path
  spec_path:
    type: str
    description:
      - Specifies the api spec path of the FTD device
    default: '/apispec/ngfw.json'
    vars:
      - name: ansible_httpapi_ftd_spec_path
"""

import json
import os
import re

from ansible import __version__ as ansible_version

from ansible.module_utils.basic import to_text
from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.network.ftd.fdm_swagger_client import FdmSwaggerParser, SpecProp, FdmSwaggerValidator
from ansible.module_utils.network.ftd.common import HTTPMethod, ResponseParams
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.plugins.httpapi import HttpApiBase
from urllib3 import encode_multipart_formdata
from urllib3.fields import RequestField
from ansible.module_utils.connection import ConnectionError

BASE_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'User-Agent': 'FTD Ansible/%s' % ansible_version
}

TOKEN_EXPIRATION_STATUS_CODE = 408
UNAUTHORIZED_STATUS_CODE = 401
API_TOKEN_PATH_OPTION_NAME = 'token_path'
TOKEN_PATH_TEMPLATE = '/api/fdm/{0}/fdm/token'
GET_API_VERSIONS_PATH = '/api/versions'
DEFAULT_API_VERSIONS = ['v2', 'v1']

INVALID_API_TOKEN_PATH_MSG = ('The API token path is incorrect. Please, check correctness of '
                              'the `ansible_httpapi_ftd_token_path` variable in the inventory file.')
MISSING_API_TOKEN_PATH_MSG = ('Ansible could not determine the API token path automatically. Please, '
                              'specify the `ansible_httpapi_ftd_token_path` variable in the inventory file.')


class HttpApi(HttpApiBase):
    def __init__(self, connection):
        super(HttpApi, self).__init__(connection)
        self.connection = connection
        self.access_token = None
        self.refresh_token = None
        self._api_spec = None
        self._api_validator = None
        self._ignore_http_errors = False

    def login(self, username, password):
        def request_token_payload(username, password):
            return {
                'grant_type': 'password',
                'username': username,
                'password': password
            }

        def refresh_token_payload(refresh_token):
            return {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token
            }

        if self.refresh_token:
            payload = refresh_token_payload(self.refresh_token)
        elif username and password:
            payload = request_token_payload(username, password)
        else:
            raise AnsibleConnectionFailure('Username and password are required for login in absence of refresh token')

        response = self._lookup_login_url(payload)

        try:
            self.refresh_token = response['refresh_token']
            self.access_token = response['access_token']
            self.connection._auth = {'Authorization': 'Bearer %s' % self.access_token}
        except KeyError:
            raise ConnectionError(
                'Server returned response without token info during connection authentication: %s' % response)

    def _lookup_login_url(self, payload):
        """ Try to find correct login URL and get api token using this URL.

        :param payload: Token request payload
        :type payload: dict
        :return: token generation response
        """
        preconfigured_token_path = self._get_api_token_path()
        if preconfigured_token_path:
            token_paths = [preconfigured_token_path]
        else:
            token_paths = self._get_known_token_paths()

        for url in token_paths:
            try:
                response = self._send_login_request(payload, url)

            except ConnectionError as e:
                self.connection.queue_message('vvvv', 'REST:request to %s failed because of connection error: %s ' % (
                    url, e))
                # In the case of ConnectionError caused by HTTPError we should check response code.
                # Response code 400 returned in case of invalid credentials so we should stop attempts to log in and
                # inform the user.
                if hasattr(e, 'http_code') and e.http_code == 400:
                    raise
            else:
                if not preconfigured_token_path:
                    self._set_api_token_path(url)
                return response

        raise ConnectionError(INVALID_API_TOKEN_PATH_MSG if preconfigured_token_path else MISSING_API_TOKEN_PATH_MSG)

    def _send_login_request(self, payload, url):
        self._display(HTTPMethod.POST, 'login', url)
        response, response_data = self._send_auth_request(
            url, json.dumps(payload), method=HTTPMethod.POST, headers=BASE_HEADERS
        )
        self._display(HTTPMethod.POST, 'login:status_code', response.getcode())

        response = self._response_to_json(self._get_response_value(response_data))
        return response

    def logout(self):
        auth_payload = {
            'grant_type': 'revoke_token',
            'access_token': self.access_token,
            'token_to_revoke': self.refresh_token
        }

        url = self._get_api_token_path()

        self._display(HTTPMethod.POST, 'logout', url)
        response, dummy = self._send_auth_request(url, json.dumps(auth_payload), method=HTTPMethod.POST,
                                                  headers=BASE_HEADERS)
        self._display(HTTPMethod.POST, 'logout:status_code', response.getcode())

        self.refresh_token = None
        self.access_token = None

    def _send_auth_request(self, path, data, **kwargs):
        error_msg_prefix = 'Server returned an error during authentication request'
        return self._send_service_request(path, error_msg_prefix, data=data, **kwargs)

    def _send_service_request(self, path, error_msg_prefix, data=None, **kwargs):
        try:
            self._ignore_http_errors = True
            return self.connection.send(path, data, **kwargs)
        except HTTPError as e:
            # HttpApi connection does not read the error response from HTTPError, so we do it here and wrap it up in
            # ConnectionError, so the actual error message is displayed to the user.
            error_msg = self._response_to_json(to_text(e.read()))
            raise ConnectionError('%s: %s' % (error_msg_prefix, error_msg), http_code=e.code)
        finally:
            self._ignore_http_errors = False

    def update_auth(self, response, response_data):
        # With tokens, authentication should not be checked and updated on each request
        return None

    def send_request(self, url_path, http_method, body_params=None, path_params=None, query_params=None):
        url = construct_url_path(url_path, path_params, query_params)
        data = json.dumps(body_params) if body_params else None
        try:
            self._display(http_method, 'url', url)
            if data:
                self._display(http_method, 'data', data)

            response, response_data = self.connection.send(url, data, method=http_method, headers=BASE_HEADERS)

            value = self._get_response_value(response_data)
            self._display(http_method, 'response', value)

            return {
                ResponseParams.SUCCESS: True,
                ResponseParams.STATUS_CODE: response.getcode(),
                ResponseParams.RESPONSE: self._response_to_json(value)
            }
        # Being invoked via JSON-RPC, this method does not serialize and pass HTTPError correctly to the method caller.
        # Thus, in order to handle non-200 responses, we need to wrap them into a simple structure and pass explicitly.
        except HTTPError as e:
            error_msg = to_text(e.read())
            self._display(http_method, 'error', error_msg)
            return {
                ResponseParams.SUCCESS: False,
                ResponseParams.STATUS_CODE: e.code,
                ResponseParams.RESPONSE: self._response_to_json(error_msg)
            }

    def upload_file(self, from_path, to_url):
        url = construct_url_path(to_url)
        self._display(HTTPMethod.POST, 'upload', url)
        with open(from_path, 'rb') as src_file:
            rf = RequestField('fileToUpload', src_file.read(), os.path.basename(src_file.name))
            rf.make_multipart()
            body, content_type = encode_multipart_formdata([rf])

            headers = dict(BASE_HEADERS)
            headers['Content-Type'] = content_type
            headers['Content-Length'] = len(body)

            dummy, response_data = self.connection.send(url, data=body, method=HTTPMethod.POST, headers=headers)
            value = self._get_response_value(response_data)
            self._display(HTTPMethod.POST, 'upload:response', value)
            return self._response_to_json(value)

    def download_file(self, from_url, to_path, path_params=None):
        url = construct_url_path(from_url, path_params=path_params)
        self._display(HTTPMethod.GET, 'download', url)
        response, response_data = self.connection.send(url, data=None, method=HTTPMethod.GET, headers=BASE_HEADERS)

        if os.path.isdir(to_path):
            filename = extract_filename_from_headers(response.info())
            to_path = os.path.join(to_path, filename)

        with open(to_path, "wb") as output_file:
            output_file.write(response_data.getvalue())
        self._display(HTTPMethod.GET, 'downloaded', to_path)

    def handle_httperror(self, exc):
        is_auth_related_code = exc.code == TOKEN_EXPIRATION_STATUS_CODE or exc.code == UNAUTHORIZED_STATUS_CODE
        if not self._ignore_http_errors and is_auth_related_code:
            self.connection._auth = None
            self.login(self.connection.get_option('remote_user'), self.connection.get_option('password'))
            return True
        # False means that the exception will be passed further to the caller
        return False

    def _display(self, http_method, title, msg=''):
        self.connection.queue_message('vvvv', 'REST:%s:%s:%s\n%s' % (http_method, self.connection._url, title, msg))

    @staticmethod
    def _get_response_value(response_data):
        return to_text(response_data.getvalue())

    def _get_api_spec_path(self):
        return self.get_option('spec_path')

    def _get_known_token_paths(self):
        """Generate list of token generation urls based on list of versions supported by device(if exposed via API) or
        default list of API versions.

        :returns: list of token generation urls
        :rtype: generator
        """
        try:
            api_versions = self._get_supported_api_versions()
        except ConnectionError:
            # API versions API is not supported we need to check all known version
            api_versions = DEFAULT_API_VERSIONS

        return [TOKEN_PATH_TEMPLATE.format(version) for version in api_versions]

    def _get_supported_api_versions(self):
        """
        Fetch list of API versions supported by device.

        :return: list of API versions suitable for device
        :rtype: list
        """
        # Try to fetch supported API version
        http_method = HTTPMethod.GET
        response, response_data = self._send_service_request(
            path=GET_API_VERSIONS_PATH,
            error_msg_prefix="Can't fetch list of supported api versions",
            method=http_method,
            headers=BASE_HEADERS
        )

        value = self._get_response_value(response_data)
        self._display(http_method, 'response', value)
        api_versions_info = self._response_to_json(value)
        return api_versions_info["supportedVersions"]

    def _get_api_token_path(self):
        return self.get_option(API_TOKEN_PATH_OPTION_NAME)

    def _set_api_token_path(self, url):
        return self.set_option(API_TOKEN_PATH_OPTION_NAME, url)

    @staticmethod
    def _response_to_json(response_text):
        try:
            return json.loads(response_text) if response_text else {}
        # JSONDecodeError only available on Python 3.5+
        except getattr(json.decoder, 'JSONDecodeError', ValueError):
            raise ConnectionError('Invalid JSON response: %s' % response_text)

    def get_operation_spec(self, operation_name):
        return self.api_spec[SpecProp.OPERATIONS].get(operation_name, None)

    def get_operation_specs_by_model_name(self, model_name):
        if model_name:
            return self.api_spec[SpecProp.MODEL_OPERATIONS].get(model_name, None)
        else:
            return None

    def get_model_spec(self, model_name):
        return self.api_spec[SpecProp.MODELS].get(model_name, None)

    def validate_data(self, operation_name, data):
        return self.api_validator.validate_data(operation_name, data)

    def validate_query_params(self, operation_name, params):
        return self.api_validator.validate_query_params(operation_name, params)

    def validate_path_params(self, operation_name, params):
        return self.api_validator.validate_path_params(operation_name, params)

    @property
    def api_spec(self):
        if self._api_spec is None:
            spec_path_url = self._get_api_spec_path()
            response = self.send_request(url_path=spec_path_url, http_method=HTTPMethod.GET)
            if response[ResponseParams.SUCCESS]:
                self._api_spec = FdmSwaggerParser().parse_spec(response[ResponseParams.RESPONSE])
            else:
                raise ConnectionError('Failed to download API specification. Status code: %s. Response: %s' % (
                    response[ResponseParams.STATUS_CODE], response[ResponseParams.RESPONSE]))
        return self._api_spec

    @property
    def api_validator(self):
        if self._api_validator is None:
            self._api_validator = FdmSwaggerValidator(self.api_spec)
        return self._api_validator


def construct_url_path(path, path_params=None, query_params=None):
    url = path
    if path_params:
        url = url.format(**path_params)
    if query_params:
        url += "?" + urlencode(query_params)
    return url


def extract_filename_from_headers(response_info):
    content_header_regex = r'attachment; ?filename="?([^"]+)'
    match = re.match(content_header_regex, response_info.get('Content-Disposition'))
    if match:
        return match.group(1)
    else:
        raise ValueError("No appropriate Content-Disposition header is specified.")

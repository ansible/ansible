# Copyright Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os
import re
import shutil

from ansible.module_utils._text import to_text
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.plugins.httpapi import HttpApiBase
from ansible.module_utils.six import wraps
from urllib3 import encode_multipart_formdata
from urllib3.fields import RequestField
from ansible.module_utils.connection import ConnectionError
from ansible.errors import AnsibleConnectionFailure

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

BASE_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}
API_PREFIX = "/api/fdm/v2"
API_TOKEN_PATH = "/fdm/token"

TOKEN_EXPIRATION_STATUS_CODE = 408
UNAUTHORIZED_STATUS_CODE = 401


class HttpApi(HttpApiBase):
    def __init__(self, connection):
        self.connection = connection
        self.access_token = False
        self.refresh_token = False

    def login(self, username=None, password=None):
        # Clean any old auth if present in connection plugin
        self.connection._auth = None

        if self.refresh_token:
            payload = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token
            }
        else:
            if username and password:
                payload = {
                    'grant_type': 'password',
                    'username': username,
                    'password': password
                }
            else:
                raise AnsibleConnectionFailure(
                    'username and password are required for login'
                    'in absence of refresh token'
                )
        response, response_data = self.connection.send(
            API_PREFIX + API_TOKEN_PATH,
            json.dumps(payload), method='POST', headers=BASE_HEADERS
        )
        try:
            self._set_token_info(response_data)
        except ValueError as vexc:
            raise ConnectionError('Did not receive access_token during Auth got'
                                  '{0}'.format(to_text(vexc)))

    def send_request(self, url_path, http_method, body_params=None, path_params=None, query_params=None):
        url = construct_url_path(url_path, path_params, query_params)
        data = json.dumps(body_params) if body_params else None

        response, response_data = self.connection.send(
            url, data, method=http_method,
            headers=self._authorized_headers()
        )
        try:
            ret = json.loads(to_text(response_data.getvalue()))
        except:
            raise ConnectionError('Response was not valid JSON, got {0}'
                                  .format(response_data.getvalue()))
        return ret

    def upload_file(self, from_path, to_url):
        url = construct_url_path(to_url)
        with open(from_path, 'rb') as src_file:
            rf = RequestField('fileToUpload', src_file.read(), os.path.basename(src_file.name))
            rf.make_multipart()
            body, content_type = encode_multipart_formdata([rf])
            headers = self._authorized_headers()
            headers['Content-Type'] = content_type
            headers['Content-Length'] = len(body)
            response, response_data = self.connection.send(
                url, data=body, method='POST', headers=headers
            )
            try:
                ret = json.loads(to_text(response_data.getvalue()))
            except:
                raise ConnectionError('Response was not valid JSON, got {0}'
                                      .format(response_data.getvalue()))
            return ret

    def download_file(self, from_url, to_path):
        url = construct_url_path(from_url)
        response, response_data = self.connection.send(
            url, data=None, method='GET',
            headers=self._authorized_headers()
        )
        if os.path.isdir(to_path):
            filename = extract_filename_from_headers(response.info())
            to_path = os.path.join(to_path, filename)

        with open(to_path, "wb") as output_file:
            output_file.write(to_text(response_data.getvalue()))

    def update_auth(self, response, response_data):
        return None

    def _set_token_info(self, response_data):
        try:
            token_info = json.loads(to_text(response_data.getvalue()))
        except ValueError:
            raise
        if 'refresh_token' in token_info:
            self.refresh_token = token_info['refresh_token']
        if 'access_token' in token_info:
            self.access_token = token_info['access_token']

    def handle_httperror(self, exc):
        # Called by connection plugin when it gets HTTP Error for a request.
        # Connection plugin will resend this request if we return true here.
        if (exc.code == TOKEN_EXPIRATION_STATUS_CODE or
           exc.code == UNAUTHORIZED_STATUS_CODE):
            # Stored auth appears to be invalid, clear and retry
            self.connection._auth = None
            self.login(self.connection.get_option('remote_user'),
                       self.connection.get_option('password'))
            return True

        return False

    def _authorized_headers(self):
        headers = dict(BASE_HEADERS)
        headers['Authorization'] = 'Bearer %s' % self.access_token
        return headers

    def logout(self):
        # Revoke the tokens
        auth_payload = {
            'grant_type': 'revoke_token',
            'access_token': self.access_token,
            'token_to_revoke': self.refresh_token
        }
        self.connection.send(
            API_PREFIX + API_TOKEN_PATH, json.dumps(auth_payload),
            method='POST', headers=self._authorized_headers()
        )
        # HTTP error would cause exception Connection failure in connection
        # plugin
        self.refresh_token = False
        self.access_token = False
        display.vvvv("logged out successfully")


def construct_url_path(path, path_params=None, query_params=None):
    url = API_PREFIX + path
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

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
httpapi : checkpoint
short_description: HttpApi Plugin for Checkpoint devices
description:
  - This HttpApi plugin provides methods to connect to Checkpoint
    devices over a HTTP(S)-based api.
version_added: "2.8"
"""

import json
import os
import re

from ansible.module_utils.basic import to_text
from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.plugins.httpapi import HttpApiBase
from urllib3 import encode_multipart_formdata
from urllib3.fields import RequestField
from ansible.module_utils.connection import ConnectionError
from ansible.utils.display import Display

BASE_HEADERS = {
    'Content-Type': 'application/json',
}

display = Display()


class HttpApi(HttpApiBase):
    def login(self, username, password):
        if username and password:
            payload = {'user': username, 'password': password}
            url = '/web_api/login'
            response, response_data = self._send_auth_request(
                url, json.dumps(payload), method='POST', headers=BASE_HEADERS
            )
            response = self._response_to_json(self._get_response_value(response_data))
        else:
            raise AnsibleConnectionFailure('Username and password are required for login')

        try:
            self._auth = response['sid']
        except KeyError:
            raise ConnectionError(
                'Server returned response without token info during connection authentication: %s' % response)

    def logout(self):
        auth_payload = {
            'grant_type': 'revoke_token',
            'access_token': self.access_token,
            'token_to_revoke': self.refresh_token
        }

        url = self._get_api_token_path()

        response, dummy = self._send_auth_request(url, json.dumps(auth_payload), method='post',
                                                  headers=BASE_HEADERS)

        self.refresh_token = None
        self.access_token = None

    def _send_auth_request(self, path, data, **kwargs):
        try:
            return self.connection.send(path, data, **kwargs)
        except HTTPError as e:
            # HttpApi connection does not read the error response from HTTPError, so we do it here and wrap it up in
            # ConnectionError, so the actual error message is displayed to the user.
            error_msg = self._response_to_json(to_text(e.read()))
            raise ConnectionError('Server returned an error during authentication request: %s' % error_msg)

    def send_request(self, path, body_params):
        data = json.dumps(body_params) if body_params else '{}'
        headers = {'Content-Type': 'application/json', 'X-chkp-sid': self._auth}

        try:
            self._display_request()
            response, response_data = self.connection.send(path, data, method='POST', headers=headers)
            value = self._get_response_value(response_data)

            return response.getcode(), self._response_to_json(value)
        except HTTPError as e:
            error = json.loads(e.read())
            return error['code'], error['message']

    def handle_httperror(self, exc):
        False

    def _display_request(self):
        display.vvvv('Web Services: %s %s' % ('POST', self.connection._url))

    @staticmethod
    def _get_response_value(response_data):
        return to_text(response_data.getvalue())

    @staticmethod
    def _response_to_json(response_text):
        try:
            return json.loads(response_text) if response_text else {}
        # JSONDecodeError only available on Python 3.5+
        except getattr(json.decoder, 'JSONDecodeError', ValueError):
            raise ConnectionError('Invalid JSON response: %s' % response_text)

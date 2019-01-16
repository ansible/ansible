# (c) 2018 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

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

from ansible.module_utils.basic import to_text
from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.plugins.httpapi import HttpApiBase
from ansible.module_utils.connection import ConnectionError

BASE_HEADERS = {
    'Content-Type': 'application/json',
}


class HttpApi(HttpApiBase):
    def login(self, username, password):
        if username and password:
            payload = {'user': username, 'password': password}
            url = '/web_api/login'
            response, response_data = self.send_request(url, payload)
        else:
            raise AnsibleConnectionFailure('Username and password are required for login')

        try:
            self.connection._auth = {'X-chkp-sid': response_data['sid']}
            self.connection._session_uid = response_data['uid']
        except KeyError:
            raise ConnectionError(
                'Server returned response without token info during connection authentication: %s' % response)

    def logout(self):
        url = '/web_api/logout'

        response, dummy = self.send_request(url, None)

    def get_session_uid(self):
        return self.connection._session_uid

    def send_request(self, path, body_params):
        data = json.dumps(body_params) if body_params else '{}'

        try:
            self._display_request()
            response, response_data = self.connection.send(path, data, method='POST', headers=BASE_HEADERS)
            value = self._get_response_value(response_data)

            return response.getcode(), self._response_to_json(value)
        except AnsibleConnectionFailure as e:
            return 404, 'Object not found'
        except HTTPError as e:
            error = json.loads(e.read())
            return e.code, error

    def _display_request(self):
        self.connection.queue_message('vvvv', 'Web Services: %s %s' % ('POST', self.connection._url))

    def _get_response_value(self, response_data):
        return to_text(response_data.getvalue())

    def _response_to_json(self, response_text):
        try:
            return json.loads(response_text) if response_text else {}
        # JSONDecodeError only available on Python 3.5+
        except ValueError:
            raise ConnectionError('Invalid JSON response: %s' % response_text)

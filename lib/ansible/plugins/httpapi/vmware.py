# Copyright: (c) 2018 Red Hat Inc.
# Copyright: (c) 2019, Ansible Project
# Copyright: (c) 2019, Abhijeet Kasurde <akasurde@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
---
author: Abhijeet Kasurde (Akasurde)
httpapi : vmware
short_description: HttpApi Plugin for VMware REST API
description:
  - This HttpApi plugin provides methods to connect to VMware vCenter over a HTTP(S)-based APIs.
version_added: "2.10"
"""

import json

from ansible.module_utils.basic import to_text
from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.plugins.httpapi import HttpApiBase
from ansible.module_utils.connection import ConnectionError

BASE_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}


class HttpApi(HttpApiBase):
    def login(self, username, password):
        if username and password:
            payload = {}
            url = '/rest/com/vmware/cis/session'
            response, response_data = self.send_request(url, payload)
        else:
            raise AnsibleConnectionFailure('Username and password are required for login')

        if response == 404:
            raise ConnectionError(response_data)

        if not response_data.get('value'):
            raise ConnectionError('Server returned response without token info during connection authentication: %s' % response)

        self.connection._session_uid = "vmware-api-session-id:%s" % response_data['value']
        self.connection._token = response_data['value']

    def logout(self):
        response, dummy = self.send_request('/rest/com/vmware/cis/session', None, method='DELETE')

    def get_session_uid(self):
        return self.connection._session_uid

    def get_session_token(self):
        return self.connection._token

    def send_request(self, path, body_params, method='POST'):
        data = json.dumps(body_params) if body_params else '{}'

        try:
            self._display_request(method=method)
            response, response_data = self.connection.send(path, data, method=method, headers=BASE_HEADERS, force_basic_auth=True)
            response_value = self._get_response_value(response_data)

            return response.getcode(), self._response_to_json(response_value)
        except AnsibleConnectionFailure as e:
            return 404, 'Object not found'
        except HTTPError as e:
            return e.code, json.loads(e.read())

    def _display_request(self, method='POST'):
        self.connection.queue_message('vvvv', 'Web Services: %s %s' % (method, self.connection._url))

    def _get_response_value(self, response_data):
        return to_text(response_data.getvalue())

    def _response_to_json(self, response_text):
        try:
            return json.loads(response_text) if response_text else {}
        # JSONDecodeError only available on Python 3.5+
        except ValueError:
            raise ConnectionError('Invalid JSON response: %s' % response_text)

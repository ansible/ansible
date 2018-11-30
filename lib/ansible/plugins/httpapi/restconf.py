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

import json

from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.connection import ConnectionError
from ansible.plugins.httpapi import HttpApiBase


class HttpApi(HttpApiBase):
    def __init__(self, connection):
        super(HttpApi, self).__init__(connection)

        self._root = '/restconf'
        self._content_type = 'application/yang.data+json'
        self._accept = 'application/yang.data+json'

    def send_request(self, data, **message_kwargs):
        if data:
            data = json.dumps(data)

        path = self._root + message_kwargs.get('path', '')

        headers = {
            'Content-Type': message_kwargs.get('content_type') or self._content_type,
            'Accept': message_kwargs.get('accept') or self._accept,
        }
        response = self.connection.send(path, data, headers=headers, method=message_kwargs.get('method'))

        return handle_response(response)

    def handle_httperror(self, exc):
        try:
            error_response = json.loads(exc.read())
        except ValueError:
            raise ConnectionError(exc.reason, code=exc.code)

        errors = error_response.get('errors')
        message = []
        if errors:
            for item in to_list(errors.get('error')):
                message.append(item.get('error-message'))
            raise ConnectionError(json.dumps(message), code=exc.code)

        raise ConnectionError(exc.reason, code=exc.code)


def handle_response(response):
    if 'error' in response and 'jsonrpc' not in response:
        error = response['error']

        error_text = []
        for data in error['data']:
            error_text.extend(data.get('errors', []))
        error_text = '\n'.join(error_text) or error['message']

        raise ConnectionError(error_text, code=error['code'])

    return response

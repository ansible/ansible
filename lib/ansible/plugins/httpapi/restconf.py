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
httpapi: restconf
short_description: HttpApi Plugin for devices supporting Restconf API
description:
  - This HttpApi plugin provides methods to connect to Restconf API
    endpoints.
version_added: "2.8"
options:
  root_path:
    type: str
    description:
      - Specifies the location of the Restconf root.
    default: '/restconf'
    vars:
      - name: ansible_httpapi_restconf_root
"""

import json

from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.connection import ConnectionError
from ansible.plugins.httpapi import HttpApiBase


CONTENT_TYPE = 'application/yang.data+json'


class HttpApi(HttpApiBase):
    def send_request(self, data, **message_kwargs):
        if data:
            data = json.dumps(data)

        path = self.get_option('root_path') + message_kwargs.get('path', '')

        headers = {
            'Content-Type': message_kwargs.get('content_type') or CONTENT_TYPE,
            'Accept': message_kwargs.get('accept') or CONTENT_TYPE,
        }
        response, response_data = self.connection.send(path, data, headers=headers, method=message_kwargs.get('method'))

        return handle_response(response_data.read())


def handle_response(response):
    if 'error' in response and 'jsonrpc' not in response:
        error = response['error']

        error_text = []
        for data in error['data']:
            error_text.extend(data.get('errors', []))
        error_text = '\n'.join(error_text) or error['message']

        raise ConnectionError(error_text, code=error['code'])

    return response

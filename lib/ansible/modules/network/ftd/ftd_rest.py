#!/usr/bin/python
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
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: ftd_rest
version_added: "2.7"
author: "Deepak Agrawal (@dagrawal)"
short_description: Manage the collection of Firepower resources on Cisco
                   firepower devices
description:
  - This module provides a REST interface to Cisco Firepower device over
  HTTP transport
notes:
  - Tested against FTD 6.1.0
options:
  url_path:
    description:
      - Specified the Path of the resource.
    required: true
  query_params:
    description:
      - Specifies query params to be placeed in resource path
  http_method:
    description:
      - Specifies http method to be executed on a resource
    choices: ['GET', 'POST', 'POST', 'DELETE']
  content:
    description:
      - Specifies the HTML body content in a dict format
"""

EXAMPLES = """
- name: Create a access rule
  ftd_rest:
    url_path: '/policy/accesspolicies/default/accessrules'
    query_params: {'at': 0}
    http_operation: 'POST'
    content:
     {
        "name": "Ansible AccessRule"
        "sourceNetworks": ["{{ networkObject }}"]
        "type": "accessrule"
     }
"""

RETURN = """
response:
  description: HTTP response returned from the API call.
  returned: success
  type: dict
error_code:
  description: HTTP error code returned from the server.
  returned: error
  type: int
msg:
  description: Error message returned from the server.
  returned: error
  type: dict
"""
import json

from ansible.module_utils.basic import AnsibleModule, to_text
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils.connection import Connection, ConnectionError
from ansible.module_utils.network.common.rest import RestApi

#FIXME
import q

class FtdRestApi(RestApi):

    def __init__(self, module_path, params):
        super(FtdRestApi, self).__init__(module_path, idempotency_support=False)
        self._params = params
        self._query_params = None

        @property
        def url_path(self):
            return self._url_path

        @url_path.setter
        def url_path(self, v):
            self._url_path = v

    def build_params_from_args(self):
        op = self._params['operation']
        res = self._params['resource']
        content = self._params['content']
        if res == 'NetworkObject':
            self.url_path = '/objects/networks/'
        elif res == 'AccessRules':
            if 'parentId' in content:
                pId = content['parentId']
                self.url_path = '/policy/accesspolicies/' + pId + '/accessrules'
                del content['parentId']
            else:
                raise ValueError('parentId is unknow for AccessRule')
            if op == 'add' or op == 'get':
                query_params = dict()
                query_params['filter'] = 'name:%s' % self._params['content'].get('name', {})
                self._query_params = query_params
            if op == 'edit' or op == 'delete':
                if 'id' in content:
                    self.url_path = self.url_path + '/' + self._params['content'].get('id', {})
                    del content['id']
                else:
                    raise ValueError('Access rule id is required for op=%s' %
                                    op)
        else:
            raise ValueError('Unknow Resource: %s' % res)

    def _handle_request(self, func, url_path, **kwargs):
        try:
           (changed, res) = func(url_path, **kwargs)
        except ConnectionError as exc:
            if to_text(exc).find('Response was not valid JSON') != -1:
                return (True, None)
            else:
                raise
        return (changed, res)

    def run(self):
        self.build_params_from_args()
        content = self._params['content']
        op = self._params['operation']
        if op == 'add':
            return self._handle_request(
                self.addResource, self.url_path,
                content=content, primary_keys=['name', 'sourceNetworks'],
                query_params=self._query_params
            )
        if op == 'get':
            return self._handle_request(self.getResource, self.url_path,
                                       query_params=self._query_params)
        if op == 'edit':
            return self._handle_request(self.editResource, self.url_path,
                                       content=content)
        if op == 'delete':
            return self._handle_request(self.deleteResource, self.url_path)

def main():
    fields = dict(
        resource=dict(type='str'),
        operation=dict(type='str', choices=['add', 'delete', 'edit', 'get',
                      'getList', 'getByName', 'upsert', 'editByName',
                      'deleteByName']),
        content=dict(type='dict'),
    )
    result = {'changed': False}

    module = AnsibleModule(argument_spec=fields, supports_check_mode=True)
    params = module.params

    try:
        ftd_rest = FtdRestApi(module._socket_path, params)
        changed, response = ftd_rest.run()

        result.update({
            'changed': changed,
            'response': response
        })
        module.exit_json(**result)
    except Exception as e:
        module.fail_json(changed=False, msg=str(e))
    except ValueError as exc:
        module.fail_json(changed=False, msg=str(exc))

if __name__ == '__main__':
    main()

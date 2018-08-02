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
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.common.rest import RestApi


class FtdRestApi(RestApi):

    def __init__(self, module_path, params):
        super(FtdRestApi, self).__init__(module_path, idempotency_support=False)
        self._params = params

    def build_url_from_resource(self):
        op = self._params['operation']
        res = self._params['resource']
        content = self._params['content']
        if res == 'NetworkObject':
            url_path = '/objects/networks/'
        elif res == 'AccessRules':
            if 'parentId' in content:
                pId = content['parentId']
                url_path = '/policy/accesspolicies/' + pId + '/accessrules'
                del content['parentId']
        else:
            module.fail_json(msg='Unknow Resouce: %s' % res)
        return url_path

    def run(self):
        url = self.build_url_from_resource()
        content = self._params['content']
        op = self._params['operation']
        if op == 'add':
            return self.addResource(url, content=content)


def main():
    fields = dict(
        resource=dict(type='str'),
        operation=dict(type='str', choices=['add', 'delete', 'edit', 'get',
                      'getList', 'getByName', 'upsert', 'editByName',
                      'deleteByName']),
        content=dict(type='dict'),
    )
    result = {'changed': False}

    module = AnsibleModule(argument_spec=fields)
    params = module.params

    try:
        ftd_rest = FtdRestApi(module._socket_path, params)
        (changed, response) = ftd_rest.run()

        result.update({
            'changed': changed,
            'response': response
        })
        module.exit_json(**result)
    except Exception as e:
        module.fail_json(changed=False, msg=str(e))


if __name__ == '__main__':
    main()

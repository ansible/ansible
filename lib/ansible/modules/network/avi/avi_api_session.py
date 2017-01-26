#!/usr/bin/python
"""
# Created on Aug 12, 2016
#
# @author: Gaurav Rastogi (grastogi@avinetworks.com) GitHub ID: grastogi23
#
# module_check: not supported
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
"""

import json
import time
from ansible.module_utils.basic import AnsibleModule
from copy import deepcopy

HAS_AVI = True
try:
    from avi.sdk.avi_api import ApiSession, ObjectNotFound
    from avi.sdk.utils.ansible_utils import (
        ansible_return, avi_obj_cmp, cleanup_absent_fields,
        avi_common_argument_spec)
except ImportError:
    HAS_AVI = False


DOCUMENTATION = '''
---
module: avi_api
author: Gaurav Rastogi (grastogi@avinetworks.com)

short_description: Avi API Module.
description:
    - This module can be used for calling any resources defined in Avi REST API. This module is useful for invoking HTTP Patch methods and accessing resources that do not have an REST object associated with them.
version_added: 2.3
requirements: [ avisdk ]
options:
    http_method:
        description:
            - Allowed HTTP methods for RESTful services and are supported by Avi Controller.
        choices: ["get", "put", "post", "patch", "delete"]
        required: true
    data:
        description:
            - HTTP body in YAML format.
    data_json:
        description:
            - HTTP body in JSON format.
    params:
        description:
            - Query parameters passed to the HTTP API.
    path:
        description:
            - Path for Avi API resource. For example, C(path: virtualservice) will translate to C(api/virtualserivce).
    timeout:
        description:
            - Timeout for Avi API calls.
extends_documentation_fragment:
    - avi
'''

EXAMPLES = '''
# Get Pool Information using avi_api_session
- avi_api_session:
    # get pool information
    controller: "{{ controller }}"
    username: "{{ username }}"
    password: "{{ password }}"
    http_method: get
    path: pool
    params:
      name: "{{ pool_name }}"
  register: pool_results

# Patch Pool with list of servers
  - avi_api_session:
      controller: "{{ controller }}"
      username: "{{ username }}"
      password: "{{ password }}"
      http_method: patch
      path: "{{ pool_path }}"
      data:
        add:
          servers:
            - ip:
                addr: 10.10.10.10
                type: V4
            - ip:
                addr: 20.20.20.20
                type: V4
'''


RETURN = '''
obj:
    description: Avi REST resource
    returned: success, changed
    type: dict
'''


def main():
    argument_specs = dict(
        http_method=dict(required=True,
                         choices=['get', 'put', 'post', 'patch',
                                  'delete']),
        path=dict(required=True),
        params=dict(type='dict'),
        data=dict(type='dict'),
        data_json=dict(type='str'),
        timeout=dict(default=60)
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(argument_spec=argument_specs)

    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    tenant_uuid = module.params.get('tenant_uuid', None)
    api = ApiSession.get_session(
        module.params['controller'], module.params['username'],
        module.params['password'], tenant=module.params['tenant'],
        tenant_uuid=tenant_uuid)

    tenant = module.params.get('tenant', '')
    timeout = int(module.params.get('timeout', 60))
    path = module.params.get('path', '')
    params = module.params.get('params', None)
    data = module.params.get('data', None)
    if ((data is None) and
            (module.params.get('data_json', None) is not None)):
        data = json.loads(module.params.get('data_json', None))
    method = module.params['http_method']

    existing_obj = None
    changed = method != 'get'
    if method == 'put':
        gparams = deepcopy(params) if params else {}
        gparams.update({'include_refs': '', 'include_name': ''})
        rsp = api.get(path, tenant=tenant, tenant_uuid=tenant_uuid,
                      params=gparams)
        if rsp.status_code == 404:
            method = 'post'
        else:
            existing_obj = rsp.json()
            changed = not avi_obj_cmp(data, existing_obj)
            cleanup_absent_fields(data)
    if method == 'patch':
        gparams = deepcopy(params) if params else {}
        gparams.update({'include_refs': '', 'include_name': ''})
        rsp = api.get(path, tenant=tenant, tenant_uuid=tenant_uuid,
                      params=gparams)
        existing_obj = rsp.json()
    fn = getattr(api, method)
    rsp = fn(path, tenant=tenant, tenant_uuid=tenant, timeout=timeout,
             params=params, data=data)
    if method == 'delete' and rsp.status_code == 404:
        changed = False
        rsp.status_code = 200
    if method == 'patch' and existing_obj and rsp.status_code < 299:
        # Ideally the comparison should happen with the return values
        # from the patch API call. However, currently Avi API are
        # returning different hostname when GET is used vs Patch.
        # tracked as AV-12561
        if path.startswith('pool'):
            time.sleep(1)
        gparams = deepcopy(params) if params else {}
        gparams.update({'include_refs': '', 'include_name': ''})
        rsp = api.get(path, tenant=tenant, tenant_uuid=tenant_uuid,
                      params=gparams)
        new_obj = rsp.json()
        changed = not avi_obj_cmp(new_obj, existing_obj)
    return ansible_return(module, rsp, changed, req=data)


if __name__ == '__main__':
    main()

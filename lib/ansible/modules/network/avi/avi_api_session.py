#!/usr/bin/python
"""
# Created on Aug 12, 2016
#
# @author: Gaurav Rastogi (grastogi@avinetworks.com) GitHub ID: grastogi23
#
# module_check: not supported
#
# Copyright: (c) 2017 Gaurav Rastogi, <grastogi@avinetworks.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
"""

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: avi_api_session
author: Gaurav Rastogi (@grastogi23) <grastogi@avinetworks.com>

short_description: Avi API Module
description:
    - This module can be used for calling any resources defined in Avi REST API. U(https://avinetworks.com/)
    - This module is useful for invoking HTTP Patch methods and accessing resources that do not have an REST object associated with them.
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
            - HTTP body in YAML or JSON format.
    params:
        description:
            - Query parameters passed to the HTTP API.
    path:
        description:
            - 'Path for Avi API resource. For example, C(path: virtualservice) will translate to C(api/virtualserivce).'
    timeout:
        description:
            - Timeout (in seconds) for Avi API calls.
        default: 60
extends_documentation_fragment:
    - avi
'''

EXAMPLES = '''

  - name: Get Pool Information using avi_api_session
    avi_api_session:
      controller: "{{ controller }}"
      username: "{{ username }}"
      password: "{{ password }}"
      http_method: get
      path: pool
      params:
        name: "{{ pool_name }}"
      api_version: 16.4
    register: pool_results

  - name: Patch Pool with list of servers
    avi_api_session:
      controller: "{{ controller }}"
      username: "{{ username }}"
      password: "{{ password }}"
      http_method: patch
      path: "{{ pool_path }}"
      api_version: 16.4
      data:
        add:
          servers:
            - ip:
                addr: 10.10.10.10
                type: V4
            - ip:
                addr: 20.20.20.20
                type: V4
    register: updated_pool

  - name: Fetch Pool metrics bandwidth and connections rate
    avi_api_session:
      controller: "{{ controller }}"
      username: "{{ username }}"
      password: "{{ password }}"
      http_method: get
      path: analytics/metrics/pool
      api_version: 16.4
      params:
        name: "{{ pool_name }}"
        metric_id: l4_server.avg_bandwidth,l4_server.avg_complete_conns
        step: 300
        limit: 10
    register: pool_metrics

'''


RETURN = '''
obj:
    description: Avi REST resource
    returned: success, changed
    type: dict
'''

import json
import time
from ansible.module_utils.basic import AnsibleModule
from copy import deepcopy

try:
    from ansible.module_utils.network.avi.avi import (
        avi_common_argument_spec, ansible_return, HAS_AVI)
    from avi.sdk.avi_api import ApiSession, AviCredentials
    from avi.sdk.utils.ansible_utils import avi_obj_cmp, cleanup_absent_fields

except ImportError:
    HAS_AVI = False


def main():
    argument_specs = dict(
        http_method=dict(required=True,
                         choices=['get', 'put', 'post', 'patch',
                                  'delete']),
        path=dict(type='str', required=True),
        params=dict(type='dict'),
        data=dict(type='jsonarg'),
        timeout=dict(type='int', default=60)
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(argument_spec=argument_specs)

    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))

    api_creds = AviCredentials()
    api_creds.update_from_ansible_module(module)
    api = ApiSession.get_session(
        api_creds.controller, api_creds.username, password=api_creds.password,
        timeout=api_creds.timeout, tenant=api_creds.tenant,
        tenant_uuid=api_creds.tenant_uuid, token=api_creds.token,
        port=api_creds.port)

    tenant_uuid = api_creds.tenant_uuid
    tenant = api_creds.tenant
    timeout = int(module.params.get('timeout'))
    # path is a required argument
    path = module.params.get('path', '')
    params = module.params.get('params', None)
    data = module.params.get('data', None)
    # Get the api_version from module.
    api_version = api_creds.api_version
    if data is not None:
        data = json.loads(data)
    method = module.params['http_method']

    existing_obj = None
    changed = method != 'get'
    gparams = deepcopy(params) if params else {}
    gparams.update({'include_refs': '', 'include_name': ''})

    if method == 'post':
        # need to check if object already exists. In that case
        # change the method to be put
        try:
            using_collection = False
            if not path.startswith('cluster'):
                gparams['name'] = data['name']
                using_collection = True
            rsp = api.get(path, tenant=tenant, tenant_uuid=tenant_uuid,
                          params=gparams, api_version=api_version)
            existing_obj = rsp.json()
            if using_collection:
                existing_obj = existing_obj['results'][0]
        except IndexError:
            # object is not found
            pass
        else:
            # object is present
            method = 'put'
            path += '/' + existing_obj['uuid']

    if method == 'put':
        # put can happen with when full path is specified or it is put + post
        if existing_obj is None:
            using_collection = False
            if ((len(path.split('/')) == 1) and ('name' in data) and
                    (not path.startswith('cluster'))):
                gparams['name'] = data['name']
                using_collection = True
            rsp = api.get(path, tenant=tenant, tenant_uuid=tenant_uuid,
                          params=gparams, api_version=api_version)
            rsp_data = rsp.json()
            if using_collection:
                if rsp_data['results']:
                    existing_obj = rsp_data['results'][0]
                    path += '/' + existing_obj['uuid']
                else:
                    method = 'post'
            else:
                if rsp.status_code == 404:
                    method = 'post'
                else:
                    existing_obj = rsp_data
        if existing_obj:
            changed = not avi_obj_cmp(data, existing_obj)
            cleanup_absent_fields(data)
    if method == 'patch':
        rsp = api.get(path, tenant=tenant, tenant_uuid=tenant_uuid,
                      params=gparams, api_version=api_version)
        existing_obj = rsp.json()

    if (method == 'put' and changed) or (method != 'put'):
        fn = getattr(api, method)
        rsp = fn(path, tenant=tenant, tenant_uuid=tenant, timeout=timeout,
                 params=params, data=data, api_version=api_version)
    else:
        rsp = None
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
                      params=gparams, api_version=api_version)
        new_obj = rsp.json()
        changed = not avi_obj_cmp(new_obj, existing_obj)
    if rsp is None:
        return module.exit_json(changed=changed, obj=existing_obj)
    return ansible_return(module, rsp, changed, req=data)


if __name__ == '__main__':
    main()

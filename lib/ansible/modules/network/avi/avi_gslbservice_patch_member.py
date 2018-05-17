#!/usr/bin/python
"""
# Created on Aug 12, 2016
#
# @author: Gaurav Rastogi (grastogi@avinetworks.com) GitHub ID: grastogi23
#
# module_check: supported
#
# Copyright: (c) 2016 Gaurav Rastogi, <grastogi@avinetworks.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
"""

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: avi_gslbservice_patch_member
author: Gaurav Rastogi (grastogi@avinetworks.com)

short_description: Avi API Module
description:
    - This module can be used for calling any resources defined in Avi REST API. U(https://avinetworks.com/)
    - This module is useful for invoking HTTP Patch methods and accessing resources that do not have an REST object associated with them.
version_added: 2.5
requirements: [ avisdk ]
options:
    data:
        description:
            - HTTP body of GSLB Service Member in YAML or JSON format.
    params:
        description:
            - Query parameters passed to the HTTP API.
    name:
        description:
            - Name of the GSLB Service
        required: true
    state:
        description:
            - The state that should be applied to the member. Member is
            - identified using field member.ip.addr.
        default: present
        choices: ["absent","present"]
extends_documentation_fragment:
    - avi
'''

EXAMPLES = '''
  - name: Patch GSLB Service to add a new member and group
    avi_gslbservice_patch_member:
      controller: "{{ controller }}"
      username: "{{ username }}"
      password: "{{ password }}"
      name: gs-3
      api_version: 17.2.1
      data:
        group:
          name: newfoo
          priority: 60
          members:
            - enabled: true
              ip:
                addr:  10.30.10.66
                type: V4
              ratio: 3
  - name: Patch GSLB Service to delete an existing member
    avi_gslbservice_patch_member:
      controller: "{{ controller }}"
      username: "{{ username }}"
      password: "{{ password }}"
      name: gs-3
      state: absent
      api_version: 17.2.1
      data:
        group:
          name: newfoo
          members:
            - enabled: true
              ip:
                addr:  10.30.10.68
                type: V4
              ratio: 3
  - name: Update priority of GSLB Service Pool
    avi_gslbservice_patch_member:
      controller: ""
      username: ""
      password: ""
      name: gs-3
      state: present
      api_version: 17.2.1
      data:
        group:
          name: newfoo
          priority: 42
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

HAS_AVI = True
try:
    from ansible.module_utils.network.avi.avi import (
        avi_common_argument_spec, HAS_AVI)
    from avi.sdk.avi_api import ApiSession
    from avi.sdk.utils.ansible_utils import (
        avi_obj_cmp, cleanup_absent_fields, ansible_return,
        AviCheckModeResponse, AviCredentials)
except ImportError:
    HAS_AVI = False


def delete_member(module, check_mode, api, tenant, tenant_uuid,
                  existing_obj, data, api_version):
    members = data.get('group', {}).get('members', [])
    patched_member_ids = set([m['ip']['addr'] for m in members if 'fqdn' not in m])
    patched_member_fqdns = set([m['fqdn'] for m in members if 'fqdn' in m])

    changed = False
    rsp = None

    if existing_obj and (patched_member_ids or patched_member_fqdns):
        groups = [group for group in existing_obj.get('groups', [])
                  if group['name'] == data['group']['name']]
        if groups:
            changed = any(
                [(lambda g: g['ip']['addr'] in patched_member_ids)(m)
                    for m in groups[0].get('members', []) if 'fqdn' not in m])
            changed = changed or any(
                [(lambda g: g['fqdn'] in patched_member_fqdns)(m)
                    for m in groups[0].get('members', []) if 'fqdn' in m])
    if check_mode or not changed:
        return changed, rsp
    # should not come here if not found
    group = groups[0]
    new_members = []
    for m in group.get('members', []):
        if 'fqdn' in m:
            if m['fqdn'] not in patched_member_fqdns:
                new_members.append(m)
        elif 'ip' in m:
            if m['ip']['addr'] not in patched_member_ids:
                new_members.append(m)
    group['members'] = new_members
    if not group['members']:
        # Delete this group from the existing objects if it is empty.
        # Controller also does not allow empty group.
        existing_obj['groups'] = [
            grp for grp in existing_obj.get('groups', []) if
            grp['name'] != data['group']['name']]
    # remove the members that are part of the list
    # update the object
    # added api version for AVI api call.
    rsp = api.put('gslbservice/%s' % existing_obj['uuid'], data=existing_obj,
                  tenant=tenant, tenant_uuid=tenant_uuid, api_version=api_version)
    return changed, rsp


def add_member(module, check_mode, api, tenant, tenant_uuid,
               existing_obj, data, name, api_version):
    rsp = None
    if not existing_obj:
        # create the object
        changed = True
        if check_mode:
            rsp = AviCheckModeResponse(obj=None)
        else:
            # creates group with single member
            req = {'name': name,
                   'groups': [data['group']]
                   }
            # added api version for AVI api call.
            rsp = api.post('gslbservice', data=req, tenant=tenant,
                           tenant_uuid=tenant_uuid, api_version=api_version)
    else:
        # found GSLB object
        req = deepcopy(existing_obj)
        if 'groups' not in req:
            req['groups'] = []
        groups = [group for group in req['groups']
                  if group['name'] == data['group']['name']]
        if not groups:
            # did not find the group
            req['groups'].append(data['group'])
        else:
            # just update the existing group with members
            group = groups[0]
            group_info_wo_members = deepcopy(data['group'])
            group_info_wo_members.pop('members', None)
            group.update(group_info_wo_members)
            if 'members' not in group:
                group['members'] = []
            new_members = []
            for patch_member in data['group'].get('members', []):
                found = False
                for m in group['members']:
                    if 'fqdn' in patch_member and m.get('fqdn', '') == patch_member['fqdn']:
                        found = True
                        break
                    elif m['ip']['addr'] == patch_member['ip']['addr']:
                        found = True
                        break
                if not found:
                    new_members.append(patch_member)
                else:
                    m.update(patch_member)
            # add any new members
            group['members'].extend(new_members)
        cleanup_absent_fields(req)
        changed = not avi_obj_cmp(req, existing_obj)
        if changed and not check_mode:
            obj_path = '%s/%s' % ('gslbservice', existing_obj['uuid'])
            # added api version for AVI api call.
            rsp = api.put(obj_path, data=req, tenant=tenant,
                          tenant_uuid=tenant_uuid, api_version=api_version)
    return changed, rsp


def main():
    argument_specs = dict(
        params=dict(type='dict'),
        data=dict(type='dict'),
        name=dict(type='str', required=True),
        state=dict(default='present',
                   choices=['absent', 'present'])
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

    tenant = api_creds.tenant
    tenant_uuid = api_creds.tenant_uuid
    params = module.params.get('params', None)
    data = module.params.get('data', None)
    gparams = deepcopy(params) if params else {}
    gparams.update({'include_refs': '', 'include_name': ''})
    name = module.params.get('name', '')
    state = module.params['state']
    # Get the api version from module.
    api_version = api_creds.api_version
    """
    state: present
    1. Check if the GSLB service is present
    2.    If not then create the GSLB service with the member
    3. Check if the group exists
    4.    if not then create the group with the member
    5. Check if the member is present
          if not then add the member
    state: absent
    1. check if GSLB service is present if not then exit
    2. check if group is present. if not then exit
    3. check if member is present. if present then remove it.
    """
    obj_type = 'gslbservice'
    # Added api version to call
    existing_obj = api.get_object_by_name(
        obj_type, name, tenant=tenant, tenant_uuid=tenant_uuid,
        params={'include_refs': '', 'include_name': ''}, api_version=api_version)
    check_mode = module.check_mode
    if state == 'absent':
        # Added api version to call
        changed, rsp = delete_member(module, check_mode, api, tenant,
                                     tenant_uuid, existing_obj, data, api_version)
    else:
        # Added api version to call
        changed, rsp = add_member(module, check_mode, api, tenant, tenant_uuid,
                                  existing_obj, data, name, api_version)
    if check_mode or not changed:
        return module.exit_json(changed=changed, obj=existing_obj)
    return ansible_return(module, rsp, changed, req=data)


if __name__ == '__main__':
    main()

#!/usr/bin/python
# coding: utf-8 -*-

# Copyright (c) 2016, Mario Santos <mario.rf.santos@gmail.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.


try:
    import shade
    from shade import meta

    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

DOCUMENTATION = '''
---
module: os_server_metadata
short_description: Add/Update/Delete Metadata in Compute Instances from
OpenStack extends_documentation_fragment: openstack
version_added: "2.2"
author: "Mario Santos (@_RuiZinK_)"
description:
   - Add, Update or Remove metadata in compute instances from OpenStack.
options:
   name:
     description:
        - Name of the instance to update the metadata
     required: true
   meta:
     description:
        - 'A list of key value pairs that should be provided as a metadata to
          the instance or a string containing a list of key-value pairs.
          Eg:  meta: "key1=value1,key2=value2"'
     required: true
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
requirements:
    - "python >= 2.6"
    - "shade"
'''

EXAMPLES = '''
# Creates or updates hostname=test1 as metadata of the server instance vm1
- name: add metadata to compute instance
  hosts: localhost
  tasks:
  - name: add metadata to instance
    os_server_metadata:
        state: present
        auth:
            auth_url: https://openstack-api.example.com:35357/v2.0/
            username: admin
            password: admin
            project_name: admin
        name: vm1
        meta:
            hostname: test1
            group: uge_master

# Removes the keys under meta from the instance named vm1
- name: delete metadata from compute instance
  hosts: localhost
  tasks:
  - name: delete metadata from instance
    os_server_metadata:
        state: absent
        auth:
            auth_url: https://openstack-api.example.com:35357/v2.0/
            username: admin
            password: admin
            project_name: admin
        name: vm1
        meta:
            hostname:
            group:
'''


def _needs_update(server_metadata={}, metadata={}):
    return len(set(metadata.items()) - set(server_metadata.items())) != 0


def _get_keys_to_delete(server_metadata_keys=[], metadata_keys=[]):
    return set(server_metadata_keys) & set(metadata_keys)


def main():
    argument_spec = openstack_full_argument_spec(
        server=dict(required=True),
        meta=dict(required=True),
        state=dict(default='present', choices=['absent', 'present']),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    state = module.params['state']
    server_param = module.params['server']
    meta_param = module.params['meta']
    changed = False

    try:
        cloud_params = dict(module.params)
        cloud = shade.openstack_cloud(**cloud_params)

        server = cloud.get_server(server_param)
        if not server:
            module.fail_json(
                msg='Could not find server %s' % server_param)

        # convert the metadata to dict, in case it was provided as CSV
        if type(meta_param) is str:
            metas = {}
            for kv_str in meta_param.split(","):
                k, v = kv_str.split("=")
                metas[k] = v
            meta_param = metas

        if state == 'present':
            # check if it needs update
            if _needs_update(server_metadata=server.metadata,
                             metadata=meta_param):
                cloud.server_set_metadata(server_param,
                                          meta_param)
                changed = True
        elif state == 'absent':
            # remove from params the keys that do not exist in the server
            keys_to_delete = _get_keys_to_delete(server.metadata.keys(),
                                                 meta_param.keys())
            if len(keys_to_delete) > 0:
                cloud.server_delete_metadata(server_param, keys_to_delete)
                changed = True

        if changed:
            server = cloud.get_server(server_param)

        module.exit_json(
            changed=changed, server_id=server.id, metadata=server.metadata)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=e.message, extra_data=e.extra_data)


# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *

if __name__ == '__main__':
    main()

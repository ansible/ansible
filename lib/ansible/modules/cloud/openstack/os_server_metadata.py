#!/usr/bin/python
# coding: utf-8 -*-

# Copyright (c) 2016, Mario Santos <mario.rf.santos@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: os_server_metadata
short_description: Add/Update/Delete Metadata in Compute Instances from OpenStack
extends_documentation_fragment: openstack
version_added: "2.6"
author: "Mario Santos (@ruizink)"
description:
   - Add, Update or Remove metadata in compute instances from OpenStack.
options:
   server:
     description:
        - Name of the instance to update the metadata
     required: true
     aliases: ['name']
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
   availability_zone:
     description:
       - Availability zone in which to create the snapshot.
     required: false
requirements:
    - "python >= 2.7"
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
            group: group1

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

RETURN = '''
server_id:
    description: The compute instance id where the change was made
    returned: success
    type: string
    sample: "324c4e91-3e03-4f62-9a4d-06119a8a8d16"
metadata:
    description: The metadata of compute instance after the change
    returned: success
    type: dict
    sample: {'key1': 'value1', 'key2': 'value2'}
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import (openstack_full_argument_spec,
                                            openstack_module_kwargs,
                                            openstack_cloud_from_module)


def _needs_update(server_metadata=None, metadata=None):
    if server_metadata is None:
        server_metadata = {}
    if metadata is None:
        metadata = {}
    return len(set(metadata.items()) - set(server_metadata.items())) != 0


def _get_keys_to_delete(server_metadata_keys=None, metadata_keys=None):
    if server_metadata_keys is None:
        server_metadata_keys = []
    if metadata_keys is None:
        metadata_keys = []
    return set(server_metadata_keys) & set(metadata_keys)


def main():
    argument_spec = openstack_full_argument_spec(
        server=dict(required=True, aliases=['name']),
        meta=dict(required=True, type='dict'),
        state=dict(default='present', choices=['absent', 'present']),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    state = module.params['state']
    server_param = module.params['server']
    meta_param = module.params['meta']
    changed = False

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        server = cloud.get_server(server_param)
        if not server:
            module.fail_json(
                msg='Could not find server {0}'.format(server_param))

        if state == 'present':
            # check if it needs update
            if _needs_update(server_metadata=server.metadata,
                             metadata=meta_param):
                if not module.check_mode:
                    cloud.set_server_metadata(server_param, meta_param)
                changed = True
        elif state == 'absent':
            # remove from params the keys that do not exist in the server
            keys_to_delete = _get_keys_to_delete(server.metadata.keys(),
                                                 meta_param.keys())
            if len(keys_to_delete) > 0:
                if not module.check_mode:
                    cloud.delete_server_metadata(server_param, keys_to_delete)
                changed = True

        if changed:
            server = cloud.get_server(server_param)

        module.exit_json(
            changed=changed, server_id=server.id, metadata=server.metadata)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=e.message, extra_data=e.extra_data)


if __name__ == '__main__':
    main()

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

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: os_volume_snapshot
short_description: Create/Delete Cinder Volume Snapshots
extends_documentation_fragment: openstack
version_added: "2.6"
author: "Mario Santos (@ruizink)"
description:
   - Create or Delete cinder block storage volume snapshots
options:
   display_name:
     description:
        - Name of the snapshot
     required: true
     aliases: ['name']
   display_description:
     description:
       - String describing the snapshot
     required: false
     default: null
     aliases: ['description']
   volume:
     description:
       - The volume name or id to create/delete the snapshot
     required: True
   force:
     description:
       - Allows or disallows snapshot of a volume to be created when the volume
         is attached to an instance.
     required: false
     default: False
     type: bool
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
     - "openstacksdk"
'''

EXAMPLES = '''
# Creates a snapshot on volume 'test_volume'
- name: create and delete snapshot
  hosts: localhost
  tasks:
  - name: create snapshot
    os_volume_snapshot:
      state: present
      cloud: mordred
      availability_zone: az2
      display_name: test_snapshot
      volume: test_volume
  - name: delete snapshot
    os_volume_snapshot:
      state: absent
      cloud: mordred
      availability_zone: az2
      display_name: test_snapshot
      volume: test_volume
'''

RETURN = '''
snapshot:
    description: The snapshot instance after the change
    returned: success
    type: dict
    sample:
      id: 837aca54-c0ee-47a2-bf9a-35e1b4fdac0c
      name: test_snapshot
      volume_id: ec646a7c-6a35-4857-b38b-808105a24be6
      size: 2
      status: available
      display_name: test_snapshot
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import (openstack_full_argument_spec,
                                            openstack_module_kwargs,
                                            openstack_cloud_from_module)


def _present_volume_snapshot(module, cloud):
    volume = cloud.get_volume(module.params['volume'])
    snapshot = cloud.get_volume_snapshot(module.params['display_name'],
                                         filters={'volume_id': volume.id})
    if not snapshot:
        snapshot = cloud.create_volume_snapshot(volume.id,
                                                force=module.params['force'],
                                                wait=module.params['wait'],
                                                timeout=module.params[
                                                    'timeout'],
                                                name=module.params['display_name'],
                                                description=module.params.get(
                                                    'display_description')
                                                )
        module.exit_json(changed=True, snapshot=snapshot)
    else:
        module.exit_json(changed=False, snapshot=snapshot)


def _absent_volume_snapshot(module, cloud):
    volume = cloud.get_volume(module.params['volume'])
    snapshot = cloud.get_volume_snapshot(module.params['display_name'],
                                         filters={'volume_id': volume.id})
    if not snapshot:
        module.exit_json(changed=False)
    else:
        cloud.delete_volume_snapshot(name_or_id=snapshot.id,
                                     wait=module.params['wait'],
                                     timeout=module.params['timeout'],
                                     )
        module.exit_json(changed=True, snapshot_id=snapshot.id)


def _system_state_change(module, cloud):
    volume = cloud.get_volume(module.params['volume'])
    snapshot = cloud.get_volume_snapshot(module.params['display_name'],
                                         filters={'volume_id': volume.id})
    state = module.params['state']

    if state == 'present':
        return snapshot is None
    if state == 'absent':
        return snapshot is not None


def main():
    argument_spec = openstack_full_argument_spec(
        display_name=dict(required=True, aliases=['name']),
        display_description=dict(default=None, aliases=['description']),
        volume=dict(required=True),
        force=dict(required=False, default=False, type='bool'),
        state=dict(default='present', choices=['absent', 'present']),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    sdk, cloud = openstack_cloud_from_module(module)

    state = module.params['state']

    try:
        if cloud.volume_exists(module.params['volume']):
            if module.check_mode:
                module.exit_json(changed=_system_state_change(module, cloud))
            if state == 'present':
                _present_volume_snapshot(module, cloud)
            if state == 'absent':
                _absent_volume_snapshot(module, cloud)
        else:
            module.fail_json(
                msg="No volume with name or id '{0}' was found.".format(
                    module.params['volume']))
    except (sdk.exceptions.OpenStackCloudException, sdk.exceptions.OpenStackCloudTimeout) as e:
        module.fail_json(msg=e.message)


if __name__ == '__main__':
    main()

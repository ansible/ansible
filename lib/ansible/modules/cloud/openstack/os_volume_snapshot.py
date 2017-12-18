#!/usr/bin/python

# Copyright (C) 2017 Red Hat, Inc.
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_volume_snapshot
short_description: Create/Delete Cinder Volume Snapshot
extends_documentation_fragment: openstack
version_added: "2.5"
author: "Nicolas Hicher"
description:
   - Create or Remove cinder block storage volume snapshot
options:
   name:
     description:
        - Name of volume snapshot
     required: true
   description:
     description:
       - String describing the volume snapshot
     required: false
     default: None
   volume:
     description:
       - Volume to snapshot
     required: false
     default: None
   force:
     description:
       - Force snapshot creation (mandatory for attached volume)
     required: false
     default: false
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
# Creates a new volume snapshot
- name: create a volume
  hosts: localhost
  tasks:
  - name: create snapshot from volume
    os_volume_snapshot:
      state: present
      cloud: default
      name: my_volume_snapshot
      volume: my_volume
  - name: delete snapshot
    os_volume_snapshot:
      state: absent
      cloud: default
      name: my_volume_snapshot
'''

RETURN = '''
snapshot:
    description: Dictionary describing the snapshot.
    returned: On success when I(state) is 'present'.
    type: complex
    contains:
        id:
            description: Unique snapshot ID
            type: string
            sample: "3fa9818f-c216-4843-b7b2-4626ce0c2573"
        name:
            description: Snapshot name
            type: string
            sample: "my_volume_snapshot"
        size:
            description: Snapshot size
            type: int
            sample: 40
        status:
            description: Snapshot status
            type: string
            sample: "available"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec

try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False


def _present_volume_snapshot(module, cloud):
    s_name = cloud.get_volume_snapshot(module.params['name'])
    if s_name:
        module.exit_json(changed=False, id=s_name['id'], snapshot=s_name)

    v_id = cloud.get_volume_id(module.params['volume'])
    if not v_id:
        module.fail_json(msg='volume %s not found' % module.params['volume'])

    volume_snapshot_args = dict(
        name=module.params['name'],
        force=module.params['force'],
        volume_id=v_id,
        description=module.params['description'],
    )

    snapshot = cloud.create_volume_snapshot(
        wait=module.params['wait'], timeout=module.params['timeout'],
        **volume_snapshot_args)
    module.exit_json(changed=True, id=snapshot['id'], snapshot=snapshot)


def _absent_volume_snapshot(module, cloud):
    try:
        cloud.delete_volume_snapshot(
            name_or_id=module.params['name'],
            wait=module.params['wait'],
            timeout=module.params['timeout'])
    except shade.OpenStackCloudTimeout:
        module.exit_json(changed=False)
    module.exit_json(changed=True)


def main():
    argument_spec = openstack_full_argument_spec(
        name=dict(required=True),
        description=dict(default=None),
        force=dict(default=False),
        volume=dict(default=None),
        state=dict(default='present', choices=['absent', 'present']),
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    state = module.params['state']

    if module.check_mode:
        module.exit_json(changed=_system_state_change(module, service))
    try:
        cloud = shade.openstack_cloud(**module.params)
        if state == 'present':
            _present_volume_snapshot(module, cloud)
        if state == 'absent':
            _absent_volume_snapshot(module, cloud)
    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()

#!/usr/bin/python

# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_volume
short_description: Create/Delete Cinder Volumes
extends_documentation_fragment: openstack
version_added: "2.0"
author: "Monty Taylor (@emonty)"
description:
   - Create or Remove cinder block storage volumes
options:
   size:
     description:
        - Size of volume in GB. This parameter is required when the
          I(state) parameter is 'present'.
     required: false
     default: None
   display_name:
     description:
        - Name of volume
     required: true
   display_description:
     description:
       - String describing the volume
     required: false
     default: None
   volume_type:
     description:
       - Volume type for volume
     required: false
     default: None
   image:
     description:
       - Image name or id for boot from volume
     required: false
     default: None
   snapshot_id:
     description:
       - Volume snapshot id to create from
     required: false
     default: None
   volume:
     description:
       - Volume name or id to create from
     required: false
     default: None
     version_added: "2.3"
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
     required: false
   scheduler_hints:
     description:
       - Scheduler hints passed to volume API in form of dict
     required: false
     default: None
     version_added: "2.4"
requirements:
     - "python >= 2.6"
     - "shade"
'''

EXAMPLES = '''
# Creates a new volume
- name: create a volume
  hosts: localhost
  tasks:
  - name: create 40g test volume
    os_volume:
      state: present
      cloud: mordred
      availability_zone: az2
      size: 40
      display_name: test_volume
      scheduler_hints:
        same_host: 243e8d3c-8f47-4a61-93d6-7215c344b0c0
'''

try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

from distutils.version import StrictVersion


def _present_volume(module, cloud):
    if cloud.volume_exists(module.params['display_name']):
        v = cloud.get_volume(module.params['display_name'])
        module.exit_json(changed=False, id=v['id'], volume=v)

    volume_args = dict(
        size=module.params['size'],
        volume_type=module.params['volume_type'],
        display_name=module.params['display_name'],
        display_description=module.params['display_description'],
        snapshot_id=module.params['snapshot_id'],
        availability_zone=module.params['availability_zone'],
    )
    if module.params['image']:
        image_id = cloud.get_image_id(module.params['image'])
        volume_args['imageRef'] = image_id

    if module.params['volume']:
        volume_id = cloud.get_volume_id(module.params['volume'])
        if not volume_id:
            module.fail_json(msg="Failed to find volume '%s'" % module.params['volume'])
        volume_args['source_volid'] = volume_id

    if module.params['scheduler_hints']:
        volume_args['scheduler_hints'] = module.params['scheduler_hints']

    volume = cloud.create_volume(
        wait=module.params['wait'], timeout=module.params['timeout'],
        **volume_args)
    module.exit_json(changed=True, id=volume['id'], volume=volume)


def _absent_volume(module, cloud):
    changed = False
    if cloud.volume_exists(module.params['display_name']):
        try:
            changed = cloud.delete_volume(name_or_id=module.params['display_name'],
                                          wait=module.params['wait'],
                                          timeout=module.params['timeout'])
        except shade.OpenStackCloudTimeout:
            module.exit_json(changed=changed)

    module.exit_json(changed=changed)


def main():
    argument_spec = openstack_full_argument_spec(
        size=dict(default=None),
        volume_type=dict(default=None),
        display_name=dict(required=True, aliases=['name']),
        display_description=dict(default=None, aliases=['description']),
        image=dict(default=None),
        snapshot_id=dict(default=None),
        volume=dict(default=None),
        state=dict(default='present', choices=['absent', 'present']),
        scheduler_hints=dict(default=None, type='dict')
    )
    module_kwargs = openstack_module_kwargs(
        mutually_exclusive=[
            ['image', 'snapshot_id', 'volume'],
        ],
    )
    module = AnsibleModule(argument_spec=argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    if (module.params['scheduler_hints'] and
            StrictVersion(shade.__version__) < StrictVersion('1.22')):
        module.fail_json(msg="To utilize scheduler_hints, the installed version of"
                             "the shade library MUST be >= 1.22")

    state = module.params['state']

    if state == 'present' and not module.params['size']:
        module.fail_json(msg="Size is required when state is 'present'")

    try:
        cloud = shade.openstack_cloud(**module.params)
        if state == 'present':
            _present_volume(module, cloud)
        if state == 'absent':
            _absent_volume(module, cloud)
    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e))

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
if __name__ == '__main__':
    main()

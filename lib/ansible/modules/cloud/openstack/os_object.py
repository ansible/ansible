#!/usr/bin/python

# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2013, Benno Joy <benno@ansible.com>
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
module: os_object
short_description: Create or Delete objects and containers from OpenStack
version_added: "2.0"
author: "Monty Taylor (@emonty)"
extends_documentation_fragment: openstack
description:
   - Create or Delete objects and containers from OpenStack
options:
   container:
     description:
        - The name of the container in which to create the object
     required: true
   name:
     description:
        - Name to be give to the object. If omitted, operations will be on
          the entire container
     required: false
   filename:
     description:
        - Path to local file to be uploaded.
     required: false
   container_access:
     description:
        - desired container access level.
     required: false
     choices: ['private', 'public']
     default: private
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
     required: false
'''

EXAMPLES = '''
- name: "Create a object named 'fstab' in the 'config' container"
  os_object:
    cloud: mordred
    state: present
    name: fstab
    container: config
    filename: /etc/fstab

- name: Delete a container called config and all of its contents
  os_object:
    cloud: rax-iad
    state: absent
    container: config
'''

try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False


def process_object(
        cloud_obj, container, name, filename, container_access, **kwargs):

    changed = False
    container_obj = cloud_obj.get_container(container)
    if kwargs['state'] == 'present':
        if not container_obj:
            container_obj = cloud_obj.create_container(container)
            changed = True
        if cloud_obj.get_container_access(container) != container_access:
            cloud_obj.set_container_access(container, container_access)
            changed = True
        if name:
            if cloud_obj.is_object_stale(container, name, filename):
                cloud_obj.create_object(container, name, filename)
                changed = True
    else:
        if container_obj:
            if name:
                if cloud_obj.get_object_metadata(container, name):
                    cloud_obj.delete_object(container, name)
                changed= True
            else:
                cloud_obj.delete_container(container)
                changed= True
    return changed


def main():
    argument_spec = openstack_full_argument_spec(
        name=dict(required=False, default=None),
        container=dict(required=True),
        filename=dict(required=False, default=None),
        container_access=dict(default='private', choices=['private', 'public']),
        state=dict(default='present', choices=['absent', 'present']),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    try:
        cloud = shade.openstack_cloud(**module.params)

        changed = process_object(cloud, **module.params)

        module.exit_json(changed=changed)
    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e))

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *

if __name__ == "__main__":
    main()

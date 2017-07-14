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

#TODO(mordred): we need to support "location"(v1) and "locations"(v2)

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_image
short_description: Add/Delete images from OpenStack Cloud
extends_documentation_fragment: openstack
version_added: "2.0"
author: "Monty Taylor (@emonty)"
description:
   - Add or Remove images from the OpenStack Image Repository
options:
   name:
     description:
        - Name that has to be given to the image
     required: true
     default: None
   id:
     version_added: "2.4"
     description:
        - The Id of the image
     required: false
     default: None
   disk_format:
     description:
        - The format of the disk that is getting uploaded
     required: false
     default: qcow2
   container_format:
     description:
        - The format of the container
     required: false
     default: bare
   owner:
     description:
        - The owner of the image
     required: false
     default: None
   min_disk:
     description:
        - The minimum disk space (in GB) required to boot this image
     required: false
     default: None
   min_ram:
     description:
        - The minimum ram (in MB) required to boot this image
     required: false
     default: None
   is_public:
     description:
        - Whether the image can be accessed publicly. Note that publicizing an image requires admin role by default.
     required: false
     default: 'yes'
   filename:
     description:
        - The path to the file which has to be uploaded
     required: false
     default: None
   ramdisk:
     description:
        - The name of an existing ramdisk image that will be associated with this image
     required: false
     default: None
   kernel:
     description:
        - The name of an existing kernel image that will be associated with this image
     required: false
     default: None
   properties:
     description:
        - Additional properties to be associated with this image
     required: false
     default: {}
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
     required: false
requirements: ["shade"]
'''

EXAMPLES = '''
# Upload an image from a local file named cirros-0.3.0-x86_64-disk.img
- os_image:
    auth:
      auth_url: http://localhost/auth/v2.0
      username: admin
      password: passme
      project_name: admin
    name: cirros
    container_format: bare
    disk_format: qcow2
    state: present
    filename: cirros-0.3.0-x86_64-disk.img
    kernel: cirros-vmlinuz
    ramdisk: cirros-initrd
    properties:
      cpu_arch: x86_64
      distro: ubuntu
'''

try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False


def main():

    argument_spec = openstack_full_argument_spec(
        name              = dict(required=True),
        id                = dict(default=None),
        disk_format       = dict(default='qcow2', choices=['ami', 'ari', 'aki', 'vhd', 'vmdk', 'raw', 'qcow2', 'vdi', 'iso', 'vhdx', 'ploop']),
        container_format  = dict(default='bare', choices=['ami', 'aki', 'ari', 'bare', 'ovf', 'ova', 'docker']),
        owner             = dict(default=None),
        min_disk          = dict(type='int', default=0),
        min_ram           = dict(type='int', default=0),
        is_public         = dict(type='bool', default=False),
        filename          = dict(default=None),
        ramdisk           = dict(default=None),
        kernel            = dict(default=None),
        properties        = dict(type='dict', default={}),
        state             = dict(default='present', choices=['absent', 'present']),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    try:
        cloud = shade.openstack_cloud(**module.params)

        changed = False
        image = cloud.get_image(name_or_id=module.params['name'])

        if module.params['state'] == 'present':
            if not image:
                image = cloud.create_image(
                    name=module.params['name'],
                    id=module.params['id'],
                    filename=module.params['filename'],
                    disk_format=module.params['disk_format'],
                    container_format=module.params['container_format'],
                    wait=module.params['wait'],
                    timeout=module.params['timeout'],
                    is_public=module.params['is_public'],
                    min_disk=module.params['min_disk'],
                    min_ram=module.params['min_ram']
                )
                changed = True
                if not module.params['wait']:
                    module.exit_json(changed=changed, image=image, id=image.id)

            cloud.update_image_properties(
                image=image,
                kernel=module.params['kernel'],
                ramdisk=module.params['ramdisk'],
                **module.params['properties'])
            image = cloud.get_image(name_or_id=image.id)
            module.exit_json(changed=changed, image=image, id=image.id)

        elif module.params['state'] == 'absent':
            if not image:
                changed = False
            else:
                cloud.delete_image(
                    name_or_id=module.params['name'],
                    wait=module.params['wait'],
                    timeout=module.params['timeout'])
                changed = True
            module.exit_json(changed=changed)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e), extra_data=e.extra_data)

# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *

if __name__ == "__main__":
    main()

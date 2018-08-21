#!/usr/bin/python

# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2013, Benno Joy <benno@ansible.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


# TODO(mordred): we need to support "location"(v1) and "locations"(v2)

ANSIBLE_METADATA = {'metadata_version': '1.1',
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
   id:
     version_added: "2.4"
     description:
        - The Id of the image
   checksum:
     version_added: "2.5"
     description:
        - The checksum of the image
   disk_format:
     description:
        - The format of the disk that is getting uploaded
     default: qcow2
   container_format:
     description:
        - The format of the container
     default: bare
   owner:
     description:
        - The owner of the image
   min_disk:
     description:
        - The minimum disk space (in GB) required to boot this image
   min_ram:
     description:
        - The minimum ram (in MB) required to boot this image
   is_public:
     description:
        - Whether the image can be accessed publicly. Note that publicizing an image requires admin role by default.
     type: bool
     default: 'yes'
   filename:
     description:
        - The path to the file which has to be uploaded
   ramdisk:
     description:
        - The name of an existing ramdisk image that will be associated with this image
   kernel:
     description:
        - The name of an existing kernel image that will be associated with this image
   properties:
     description:
        - Additional properties to be associated with this image
     default: {}
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
   update_policy:
     version_added: "2.8"
     description:
        - What to do if an image with that name already exists.
        - If C(keep_existing), the original file will be kept. Set I(checksum)
          if you want the file to uploaded with the same name. Default is
          C(keep_existing).
        - If C(delete), the existing image will be removed prior to uploading
          the new one.
        - If C(rename), the existing image will be renamed with the extension
          name.YYYY-MM-DD@HH:MM:SS formatted with the creation timestamp.
requirements: ["openstacksdk"]
'''

EXAMPLES = '''
# Upload an image from a local file named cirros-0.3.0-x86_64-disk.img
- os_image:
    auth:
      auth_url: https://identity.example.com
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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module
import time


def does_checksum_match(module, image):
    if not image:
        return False
    local_sum = module.digest_from_file(module.params["filename"], "md5")
    return local_sum == image.checksum


def main():

    argument_spec = openstack_full_argument_spec(
        name=dict(required=True),
        id=dict(default=None),
        checksum=dict(default=None),
        disk_format=dict(default='qcow2', choices=['ami', 'ari', 'aki', 'vhd', 'vmdk', 'raw', 'qcow2', 'vdi', 'iso', 'vhdx', 'ploop']),
        container_format=dict(default='bare', choices=['ami', 'aki', 'ari', 'bare', 'ovf', 'ova', 'docker']),
        owner=dict(default=None),
        min_disk=dict(type='int', default=0),
        min_ram=dict(type='int', default=0),
        is_public=dict(type='bool', default=False),
        filename=dict(default=None),
        ramdisk=dict(default=None),
        kernel=dict(default=None),
        properties=dict(type='dict', default={}),
        state=dict(default='present', choices=['absent', 'present']),
        update_policy=dict(default='keep_existing',
                           choices=['keep_existing', 'delete', 'rename']),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    sdk, cloud = openstack_cloud_from_module(module)

    try:
        if module.params['checksum']:
            image = cloud.get_image(name_or_id=None, filters={'checksum': module.params['checksum']})
        else:
            image = cloud.get_image(name_or_id=module.params['name'])

        update_policy = module.params['update_policy']
        checksum_matches = does_checksum_match(module, image)

        if module.params['state'] == 'present':
            if (image and update_policy == "keep_existing") or checksum_matches:
                module.exit_json(changed=False)
            elif image and update_policy == "delete":
                cloud.delete_image(
                    name_or_id=module.params['name'],
                    wait=True,
                    timeout=module.params['timeout']
                )
            elif image and update_policy == "rename":
                dt = time.strptime(image.created_at, "%Y-%m-%dT%H:%M:%SZ")
                # backups named name.YYYY-MM-DD@HH:MM:SS
                ext = time.strftime("%Y-%m-%d@%H:%M:%S", dt)
                cloud.update_image_properties(
                    image=image,
                    name="{name}.{ext}".format(
                        name=image.name,
                        ext=ext
                    )
                )
            kwargs = {}
            if module.params['id'] is not None:
                kwargs['id'] = module.params['id']
            image = cloud.create_image(
                name=module.params['name'],
                filename=module.params['filename'],
                disk_format=module.params['disk_format'],
                container_format=module.params['container_format'],
                wait=module.params['wait'],
                timeout=module.params['timeout'],
                is_public=module.params['is_public'],
                min_disk=module.params['min_disk'],
                min_ram=module.params['min_ram'],
                **kwargs
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

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e), extra_data=e.extra_data)


if __name__ == "__main__":
    main()

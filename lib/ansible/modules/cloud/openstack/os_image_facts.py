#!/usr/bin/python

# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: os_image_facts
short_description: Retrieve facts about an image within OpenStack.
version_added: "2.0"
author: "Davide Agnello (@dagnello)"
description:
    - Retrieve facts about a image image from OpenStack.
notes:
    - Facts are placed in the C(openstack_image) variable.
requirements:
    - "python >= 2.7"
    - "openstacksdk"
options:
   image:
     description:
        - Name or ID of the image
     required: false
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
     required: false
extends_documentation_fragment: openstack
'''

EXAMPLES = '''
- name: Gather facts about a previously created image named image1
  os_image_facts:
    auth:
      auth_url: https://identity.example.com
      username: user
      password: password
      project_name: someproject
    image: image1

- name: Show openstack facts
  debug:
    var: openstack_image

# Show all available Openstack images
- name: Retrieve all available Openstack images
  os_image_facts:

- name: Show images
  debug:
    var: openstack_image
'''

RETURN = '''
openstack_image:
    description: has all the openstack facts about the image
    returned: always, but can be null
    type: complex
    contains:
        id:
            description: Unique UUID.
            returned: success
            type: str
        name:
            description: Name given to the image.
            returned: success
            type: str
        status:
            description: Image status.
            returned: success
            type: str
        created_at:
            description: Image created at timestamp.
            returned: success
            type: str
        deleted:
            description: Image deleted flag.
            returned: success
            type: bool
        container_format:
            description: Container format of the image.
            returned: success
            type: str
        min_ram:
            description: Min amount of RAM required for this image.
            returned: success
            type: int
        disk_format:
            description: Disk format of the image.
            returned: success
            type: str
        updated_at:
            description: Image updated at timestamp.
            returned: success
            type: str
        properties:
            description: Additional properties associated with the image.
            returned: success
            type: dict
        min_disk:
            description: Min amount of disk space required for this image.
            returned: success
            type: int
        protected:
            description: Image protected flag.
            returned: success
            type: bool
        checksum:
            description: Checksum for the image.
            returned: success
            type: str
        owner:
            description: Owner for the image.
            returned: success
            type: str
        is_public:
            description: Is public flag of the image.
            returned: success
            type: bool
        deleted_at:
            description: Image deleted at timestamp.
            returned: success
            type: str
        size:
            description: Size of the image.
            returned: success
            type: int
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


def main():

    argument_spec = openstack_full_argument_spec(
        image=dict(required=False),
    )
    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec, **module_kwargs)

    sdk, cloud = openstack_cloud_from_module(module)
    try:
        if module.params['image']:
            image = cloud.get_image(module.params['image'])
            module.exit_json(changed=False, ansible_facts=dict(
                openstack_image=image))
        else:
            images = cloud.list_images()
            module.exit_json(changed=False, ansible_facts=dict(
                openstack_image=images))

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

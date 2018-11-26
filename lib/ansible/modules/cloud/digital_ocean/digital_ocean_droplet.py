#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: digital_ocean_droplet
short_description: Create and remove droplets in DigitalOcean.
description:
    - Create and remove droplet in DigitalOcean.
author: "Kevin Breit (@kevinbreit)"
version_added: "2.9"
options:
  name:
    description:
     - The name of the tag. The supported characters for names include
       alphanumeric characters, dashes, and underscores.
    required: true
  resource_id:
    description:
    - The ID of the resource to operate on.
    - The data type of resource_id is changed from integer to string, from version 2.5.
    aliases: ['droplet_id']
  resource_type:
    description:
    - The type of resource to operate on. Currently, only tagging of
      droplets is supported.
    default: droplet
    choices: ['droplet']
  state:
    description:
     - Whether the tag should be present or absent on the resource.
    default: present
    choices: ['present', 'absent']
extends_documentation_fragment: digital_ocean.documentation
notes:
  - Two environment variables can be used, DO_API_KEY and DO_API_TOKEN.
    They both refer to the v2 token.
  - As of Ansible 2.0, Version 2 of the DigitalOcean API is used.

requirements:
  - "python >= 2.6"
'''


EXAMPLES = '''
- name: create a tag
  digital_ocean_tag:
    name: production
    state: present

- name: tag a resource; creating the tag if it does not exist
  digital_ocean_tag:
    name: "{{ item }}"
    resource_id: "73333005"
    state: present
  with_items:
    - staging
    - dbserver

- name: untag a resource
  digital_ocean_tag:
    name: staging
    resource_id: "73333005"
    state: absent

# Deleting a tag also untags all the resources that have previously been
# tagged with it
- name: remove a tag
  digital_ocean_tag:
    name: dbserver
    state: absent
'''


RETURN = '''
data:
    description: a DigitalOcean Tag resource
    returned: success and no resource constraint
    type: dict
    sample: {
        "tag": {
        "name": "awesome",
        "resources": {
          "droplets": {
            "count": 0,
            "last_tagged": null
          }
        }
      }
    }
'''

from traceback import format_exc
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.digital_ocean import DigitalOceanHelper
from ansible.module_utils._text import to_native


def core(module):
    state = module.params['state']
    names = module.params['names']
    name = module.params['name']
    region = module.params['region']
    size = module.params['size']
    image = module.params['image']
    ssh_keys = module.params['ssh_keys']
    backups = module.params['backups']
    ipv6 = module.params['ipv6']
    private_networking = module.params['private_networking']
    user_data = module.params['user_data']
    monitoring = module.params['monitoring']
    volumes = module.params['volumes']
    tags = module.params['tags']
    id = module.params['id']
    action = module.params['action']
    

    rest = DigitalOceanHelper(module)

    if state == 'present':
        if action is not None:
            module.fail_json(msg="Implement actions")
        else: # Assumes droplet isn't created
            payload = {'name': name,
                       'region': region,
                       'size': size,
                       'image': image,
                       'ssh_keys': ssh_keys,
                       }
            if names:
                payload['names'] = names
                del payload['name']
            if tags:
                payload['tags'] = tags
            if volumes:
                payload['volumes'] = volumes
            if monitoring is not None:
                payload['monitoring'] = monitoring
            if user_data is not None:
                payload['user_data'] = user_data
            if private_networking is not None:
                payload['private_networking'] = private_networking
            if ipv6 is not None:
                payload['ipv6'] = ipv6
            if backups is not None:
                payload['backups'] = backups

            response = rest.post("droplets", data=payload)
            if response.status_code != 202:
                module.fail_json(msg="Failed", status_code=response.status_code, response=response.resp_json)
            else:
                module.exit_json(changed=True, droplet=response.json)

def main():
    argument_spec = DigitalOceanHelper.digital_ocean_argument_spec()
    argument_spec.update(
        id=dict(type='int'),
        action=dict(type='str', choices=['reboot',
                                         'power_on',
                                         'power_off',
                                         'power_cycle',
                                         'password-reset',
                                         'restore',
                                         'resize',
                                         'rebuild',
                                         'snapshot']),
        resize_disk=dict(type='str'),
        kernel=dict(type='str'),
        name=dict(type='str'),
        names=dict(type='list'),
        region=dict(type='str'),
        size=dict(type='str'),
        image=dict(type='str'),
        ssh_keys=dict(type='list'),
        backups=dict(type='bool'),
        ipv6=dict(type='bool'),
        private_networking=dict(type='bool'),
        user_data=dict(type='str'),
        monitoring=dict(type='bool'),
        volumes=dict(type='list'),
        tags=dict(type='list'),
        state=dict(choices=['present'], default='present'),
    )

    module = AnsibleModule(argument_spec=argument_spec)

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=format_exc())


if __name__ == '__main__':
    main()

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

    rest = DigitalOceanHelper(module)

    if state == 'present':
        response = rest.get('droplets')
        status_code = response.status_code
        resp_json = response.json
        changed = False
'''        if status_code == 200 and resp_json['droplet']['name'] == name:
            changed = False
        else:
            # Ensure droplet exists
            response = rest.post("droplets", data={'name': name})
            status_code = response.status_code
            resp_json = response.json
            if status_code == 201:
                changed = True
            elif status_code == 422:
                changed = False
            else:
                module.exit_json(changed=False, data=resp_json)

        if resource_id is None:
            # No resource defined, we're done.
            module.exit_json(changed=changed, data=resp_json)
        else:
            # Check if resource is already tagged or not
            found = False
            url = "{0}?tag_name={1}".format(resource_type, name)
            if resource_type == 'droplet':
                url = "droplets?tag_name={0}".format(name)
            response = rest.get(url)
            status_code = response.status_code
            resp_json = response.json
            if status_code == 200:
                for resource in resp_json['droplets']:
                    if not found and resource['id'] == int(resource_id):
                        found = True
                        break
                if not found:
                    # If resource is not tagged, tag a resource
                    url = "tags/{0}/resources".format(name)
                    payload = {
                        'resources': [{
                            'resource_id': resource_id,
                            'resource_type': resource_type}]}
                    response = rest.post(url, data=payload)
                    if response.status_code == 204:
                        module.exit_json(changed=True)
                    else:
                        module.fail_json(msg="error tagging resource '{0}': {1}".format(resource_id, response.json["message"]))
                else:
                    # Already tagged resource
                    module.exit_json(changed=False)
            else:
                # Unable to find resource specified by user
                module.fail_json(msg=resp_json['message'])
'''
    elif state == 'absent':
        if resource_id:
            url = "tags/{0}/resources".format(name)
            payload = {
                'resources': [{
                    'resource_id': resource_id,
                    'resource_type': resource_type}]}
            response = rest.delete(url, data=payload)
        else:
            url = "tags/{0}".format(name)
            response = rest.delete(url)
        if response.status_code == 204:
            module.exit_json(changed=True)
        else:
            module.exit_json(changed=False, data=response.json)


def main():
    argument_spec = DigitalOceanHelper.digital_ocean_argument_spec()
    argument_spec.update(
        name=dict(type='str', required=True),
        region=dict(type='str', required=True),
        size=dict(type='str', required=True),
        image=dict(type='int', required=True),
        ssh_keys=dict(type='list'),
        backups=dict(type='bool'),
        ipv6=dict(type='bool'),
        private_networking=dict(type='bool'),
        user_data=dict(type='str'),
        monitoring=dict(type='bool'),
        volumes=dict(type='list'),
        tags=dict(type='list'),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    module = AnsibleModule(argument_spec=argument_spec)

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=format_exc())


if __name__ == '__main__':
    main()

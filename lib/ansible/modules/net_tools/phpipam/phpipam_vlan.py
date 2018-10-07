#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Carson Anderson <rcanderson23@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
---
module: phpipam_vlan
author: "Carson Anderson (@rcanderson23)"
short_description: Set the state of a vlan
requirements: []
version_added: "2.8"
description:
    - Creates, modifies, or destroys vlan in phpIPAM instance if necessary.
options:
  username:
    description:
      - username that has permission to access phpIPAM API
    required: True
  password:
    description:
      - password for username provided
    required: True
  url:
    description:
      - API url for phpIPAM instance
    required: True
  vlan:
    description:
      - Vlan number.
    required: True
  name:
    description:
      - Vlan display name in phpIPAM.
    required: True
  description:
    description:
      - Optional description displayed next to vlan in phpIPAM.
    required: False
  state:
    description:
      - States whether the vlan should be present or absent
    choices: ["present", "absent"]
    required: False
    default: present
'''

EXAMPLES = '''

- name: Create a nested subnet
  phpipam_vlan:
    username: username
    password: secret
    url: "https://ipam.domain.tld/api/app/"
    name: 'wireless'
    vlan: '22'
    description: "Wireless at Building A"
    state: present

- name: Delete a vlan
  phpipam_vlan:
    username: username
    password: secret
    url: "https://ipam.domain.tld/api/app/"
    name: 'ansible vlan'
    vlan: '22'
    state: absent
'''

RETURN = '''
output:
    description: dictionary containing phpIPAM response
    returned: success
    type: complex
    contains:
        code:
            description: HTTP response code
            returned: success
            type: int
            sample: 201
        success:
            description: True or False depending on if subnet was created or deleted
            returned: success
            type: bool
            sample: True
        time:
            description: Amount of time operation took.
            returned: success
            type: float
            sample: 0.015
        message:
            description: Response message of what happened
            returned: success
            type: string
            sample: "Vlan created"
        id:
            description: ID of vlan created/modified
            returned: success
            type: string
            sample: "10"
'''

from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.phpipam as phpipam


def main():
    module = AnsibleModule(
        argument_spec=dict(
            username=dict(type=str, required=True),
            password=dict(type=str, required=True, no_log=True),
            url=dict(type=str, required=True),
            vlan=dict(type=str, required=True),
            name=dict(type=str, required=True),
            description=dict(type=str, required=False),
            state=dict(default='present', choices=['present', 'absent'])
        ),
        supports_check_mode=False
    )

    result = dict(
        changed=False
    )
    username = module.params['username']
    password = module.params['password']
    url = module.params['url']
    vlan = module.params['vlan']
    name = module.params['name']
    description = module.params['description']
    state = module.params['state']

    session = phpipam.PhpIpamWrapper(username, password, url)
    try:
        session.create_session()
    except AttributeError:
        module.fail_json(msg='Error getting authorization token', **result)

    vlan_url = url + 'vlan/'
    found_vlan = session.get_vlan(vlan)

    optional_args = {'name': name,
                     'description': description}
    if state == 'present' and found_vlan is None:
        # Create vlan if not present

        creation = session.create(session,
                                  vlan_url,
                                  number=vlan,
                                  **optional_args)
        if creation['code'] == 201:
            result['changed'] = True
            result['output'] = creation
            module.exit_json(**result)
        else:
            module.fail_json(msg='vlan unable to be created', **result)
    elif state == 'present':
        # Update vlan information if necessary

        value_changed = False
        payload = {'name': name}
        vlan_id = session.get_vlan_id(vlan)

        for k in optional_args:
            if optional_args[k] != found_vlan[k]:
                value_changed = True
                payload[k] = optional_args[k]
        if value_changed:
            patch_response = session.modify(session,
                                            vlan_url,
                                            id=vlan_id,
                                            **payload)
            result['changed'] = True
            result['output'] = patch_response
            module.exit_json(**result)
        else:
            result['output'] = patch_response
            module.exit_json(**result)
    else:
        # Delete vlan if it exist

        vlan_id = session.get_vlan_id(vlan)
        if vlan_id is None:
            result['output'] = 'Vlan doesn\'t exist'
            module.exit_json(**result)
        else:
            deletion = session.remove(session,
                                      vlan_url,
                                      vlan_id)
            if deletion['code'] == 200:
                result['changed'] = True
                result['output'] = deletion
                module.exit_json(**result)
            else:
                result['output'] = deletion
                module.fail_json(**result)


if __name__ == '__main__':
    main()

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
module: phpipam_subnet
author: "Carson Anderson (@rcanderson23)"
short_description: Set the state of a subnet
requirements: []
version_added: "2.8"
description:
    - Creates, modifies, or destroys subnet in phpIPAM instance if necessary.
options:
  section:
    description:
      - Name of the section that the subnet belongs to.
    required: True
  subnet:
    description:
      - Subnet in CIDR format.
    required: True
  master_subnet:
    description:
      - Master subnet for the subnet to be nested under.
      - When master_subnet is not defined it defaults to the root.
    required: False
  vlan:
    description:
      - Optional vlan for subnet to be assigned
    required: False
  description:
    description:
      - Optional description displayed next to address in phpIPAM.
    required: False
  state:
    description:
      - States whether the subnet should be present or absent
    choices: ["present", "absent"]
    required: False
    default: 'present'
extends_documentation_fragment: phpipam
'''

EXAMPLES = '''

- name: Create a subnet
  phpipam_subnet:
    auth:
      username: user
      password: secret
      url: http://phpipam.domain.tld/api/app/
    section: 'ansible section'
    subnet: "192.168.10.0/24"
    description: "optional description"
    state: present

- name: Create a nested subnet
  phpipam_subnet:
    auth:
      username: user
      password: secret
      url: http://phpipam.domain.tld/api/app/
    section: 'section two'
    subnet: '192.168.10.0/25'
    master_subnet: '192.168.10.0/24'
    description: "section two"
    state: present

- name: Delete a subnet
  phpipam_subnet:
    auth:
      username: user
      password: secret
      url: http://phpipam.domain.tld/api/app/
    section: 'section two'
    subnet: '192.168.10.0/24'
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
            description: True or False depending on if ip was successfully obtained
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
            sample: "Address created"
        id:
            description: ID of section created/modified
            returned: success
            type: string
            sample: "206"
'''
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils import phpipam


def main():
    argument_spec = phpipam.phpipam_argument_spec(
        section=dict(type=str, required=True),
        subnet=dict(type=str, required=True),
        master_subnet=dict(type=str, required=False),
        description=dict(type=str, required=False),
        vlan=dict(type=str, required=False),
        state=dict(default='present', choices=['present', 'absent'])
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    result = dict(
        changed=False
    )
    auth = module.params.pop('auth')
    url = auth['url']
    section = module.params['section']
    subnet = module.params['subnet']
    master_subnet = module.params['master_subnet']
    description = module.params['description']
    vlan = module.params['vlan']
    state = module.params['state']

    session = phpipam.PhpIpamWrapper(auth)
    try:
        session.create_session(auth)
    except AttributeError:
        module.fail_json(msg='Error getting authorization token', **result)

    subnet_url = url + 'subnets/'
    section_id = session.get_section_id(section)
    if section_id is None:
        module.fail_json(msg='section doesn\'t exist', **result)
    found_subnet = session.get_subnet(subnet, section)
    optional_args = {}

    if description:
        optional_args['description'] = description

    if vlan:
        # If vlan is defined, make sure it exists and then set

        vlan_id = session.get_vlan_id(vlan)
        if vlan_id is None:
            module.fail_json(msg='vlan not found', **result)
        else:
            optional_args['vlanId'] = vlan_id

    if master_subnet:
        master_subnet_id = session.get_subnet_id(master_subnet, section)
        if master_subnet_id is None:
            module.fail_json(msg='master_subnet not found', **result)
        else:
            optional_args['masterSubnetId'] = master_subnet_id

    if state == 'present' and found_subnet is None:
        # Create subnet if it doesn't exist

        if module.check_mode:
            result['changed'] = True
            module.exit_json(**result)

        subnet_split = subnet.rsplit('/', 1)
        creation = session.create(session,
                                  subnet_url,
                                  subnet=subnet_split[0],
                                  mask=subnet_split[1],
                                  sectionId=section_id,
                                  **optional_args)
        if creation['code'] == 201:
            result['changed'] = True
            result['output'] = creation
            module.exit_json(**result)
        else:
            result['output'] = creation
            module.fail_json(**result)
    elif state == 'present':
        # Update subnet if necessary

        value_changed = False
        payload = {}
        for k in optional_args:
            if optional_args[k] != found_subnet[k]:
                value_changed = True
                payload[k] = optional_args[k]

        if module.check_mode:
            if value_changed:
                result['changed'] = True
                module.exit_json(**result)
            module.exit_json(**result)

        if value_changed:
            patch_response = session.modify(session,
                                            subnet_url,
                                            id=found_subnet['id'],
                                            sectionId=found_subnet['sectionId'],
                                            **payload)
            result['changed'] = True
            result['output'] = patch_response
            module.exit_json(**result)
        else:
            result['output'] = 'Subnet required no change'
            module.exit_json(**result)
    else:
        # Delete subnet if present
        if module.check_mode:
            if found_subnet:
                result['changed'] = True
                module.exit_json(**result)
            module.exit_json(**result)
        try:
            deletion = session.remove(session, subnet_url, found_subnet['id'])
            if deletion['code'] == 200:
                result['changed'] = True
                result['output'] = deletion
                module.exit_json(**result)
        except TypeError:
            result['output'] = 'Subnet did not exist'
            module.exit_json(**result)


if __name__ == '__main__':
    main()

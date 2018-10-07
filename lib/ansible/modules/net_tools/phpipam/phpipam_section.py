#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Carson Anderson <rcanderson23@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = '''
---
module: phpipam_section
author: "Carson Anderson (@rcanderson23)"
short_description: Set the state of a section
requirements: []
version_added: "2.7"
description:
    - Creates, modifies, or destroys section in phpIPAM instance if necessary.
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
  section:
    description:
      - Section name that the subnet resides in.
    type: string
    required: True
  master_section:
    description:
      - Master section for the section to be nested under.
      - When master_section is not defined it defaults to the root.
    type: string
    required: False
    default: root
  description:
    description:
      - Optional description displayed next to address in phpIPAM.
    type: string
    required: False
  state:
    description:
      - States whether the section should be present or absent
    type: string
    choices: ["present", "absent"]
    required: False
    default: present
'''

EXAMPLES = '''

- name: Create a section
  phpipam_section:
    username: username
    password: secret
    url: "https://ipam.domain.tld/api/app/"
    section: 'ansible section'
    description: "optional description"
    state: present

- name: Create a section nested under 'ansible section'
  phpipam_section:
    username: username
    password: secret
    url: "https://ipam.domain.tld/api/app/"
    section: 'section two'
    master_section: 'ansbile section'
    description: "section two"
    state: present

- name: Delete a section
  phpipam_section:
    username: username
    password: secret
    url: "https://ipam.domain.tld/api/app/"
    section: 'section two'
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
import ansible.module_utils.phpipam as phpipam


def set_master_section(session, master_section):
    if master_section in ('', 'root'):
        return '0'
    else:
        return session.get_section_id(master_section)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            username=dict(type=str, required=True),
            password=dict(type=str, required=True, no_log=True),
            url=dict(type=str, required=True),
            section=dict(type=str, required=True),
            master_section=dict(type=str, required=False, default='root'),
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
    section = module.params['section']
    master_section = module.params['master_section']
    description = module.params['description']
    state = module.params['state']

    session = phpipam.PhpIpamWrapper(username, password, url)
    try:
        session.create_session()
    except AttributeError:
        module.fail_json(msg='Error getting authorization token', **result)

    section_url = url + 'sections/'
    found_section = session.get_section(section)
    master_section_id = set_master_section(session, master_section)
    if master_section_id is None:
        module.fail_json(msg='master_section does not exist', **result)
    else:
        optional_args = {'masterSection': set_master_section(session, master_section),
                         'description': description}
    if state == 'present' and found_section is None:
        # Create the section since it does not exist

        if optional_args['masterSection'] == '0':
            del optional_args['masterSection']
        creation = session.create(session,
                                  section_url,
                                  name=section,
                                  **optional_args)
        if creation['code'] == 201:
            result['changed'] = True
            result['output'] = creation
            module.exit_json(**result)
        elif creation['code'] == 500:
            result['output'] = creation
            module.exit_json(**result)
        else:
            result['output'] = creation
            module.fail_json(msg='Something went wrong', **result)
    elif state == 'present':
        # Potentially modify the section if it doesn't match

        value_changed = False
        payload = {}
        section_id = session.get_section_id(section)

        for k in optional_args:
            if optional_args[k] != found_section[k]:
                value_changed = True
                payload[k] = optional_args[k]
        if value_changed:
            patch_response = session.modify(session,
                                            section_url,
                                            id=section_id,
                                            **payload)
            result['changed'] = True
            result['output'] = patch_response
            module.exit_json(**result)
        else:
            result['output'] = patch_response
            module.exit_json(**result)
    else:
        # Ensure the section does not exist, delete if necessary

        section_info = session.get_section(section)
        try:
            deletion = session.remove(session,
                                      section_url,
                                      section_info['id'])
            if deletion['code'] == 200:
                result['changed'] = True
                result['output'] = deletion
                module.exit_json(**result)
        except KeyError:
            result['ouput'] = 'Section did not exist'
            module.exit_json(**result)
        except TypeError:
            result['output'] = 'Section did not exist'
            module.exit_json(**result)


if __name__ == '__main__':
    main()

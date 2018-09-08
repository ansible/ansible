#!/usr/bin/python
#
# (c) 2017 Apstra Inc, <community@apstra.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: aos_rack_type
author: Damien Garros (@dgarros)
version_added: "2.3"
short_description: Manage AOS Rack Type
deprecated:
    removed_in: "2.9"
    why: This module does not support AOS 2.1 or later
    alternative: See new modules at U(https://www.ansible.com/ansible-apstra).
description:
  - Apstra AOS Rack Type module let you manage your Rack Type easily.
    You can create create and delete Rack Type by Name, ID or by using a JSON File.
    This module is idempotent and support the I(check) mode.
    It's using the AOS REST API.
requirements:
  - "aos-pyez >= 0.6.0"
options:
  session:
    description:
      - An existing AOS session as obtained by M(aos_login) module.
    required: true
  name:
    description:
      - Name of the Rack Type to manage.
        Only one of I(name), I(id) or I(content) can be set.
  id:
    description:
      - AOS Id of the Rack Type to manage (can't be used to create a new Rack Type),
        Only one of I(name), I(id) or I(content) can be set.
  content:
    description:
      - Datastructure of the Rack Type to create. The data can be in YAML / JSON or
        directly a variable. It's the same datastructure that is returned
        on success in I(value).
  state:
    description:
      - Indicate what is the expected state of the Rack Type (present or not).
    default: present
    choices: ['present', 'absent']
'''

EXAMPLES = '''

- name: "Delete a Rack Type by name"
  aos_rack_type:
    session: "{{ aos_session }}"
    name: "my-rack-type"
    state: absent

- name: "Delete a Rack Type by id"
  aos_rack_type:
    session: "{{ aos_session }}"
    id: "45ab26fc-c2ed-4307-b330-0870488fa13e"
    state: absent

# Save a Rack Type to a file

- name: "Access Rack Type 1/3"
  aos_rack_type:
    session: "{{ aos_session }}"
    name: "my-rack-type"
    state: present
  register: rack_type

- name: "Save Rack Type into a JSON file 2/3"
  copy:
    content: "{{ rack_type.value | to_nice_json }}"
    dest: rack_type_saved.json
- name: "Save Rack Type into a YAML file 3/3"
  copy:
    content: "{{ rack_type.value | to_nice_yaml }}"
    dest: rack_type_saved.yaml

- name: "Load Rack Type from a JSON file"
  aos_rack_type:
    session: "{{ aos_session }}"
    content: "{{ lookup('file', 'resources/rack_type_saved.json') }}"
    state: present

- name: "Load Rack Type from a YAML file"
  aos_rack_type:
    session: "{{ aos_session }}"
    content: "{{ lookup('file', 'resources/rack_type_saved.yaml') }}"
    state: present
'''

RETURNS = '''
name:
  description: Name of the Rack Type
  returned: always
  type: str
  sample: AOS-1x25-1

id:
  description: AOS unique ID assigned to the Rack Type
  returned: always
  type: str
  sample: fcc4ac1c-e249-4fe7-b458-2138bfb44c06

value:
  description: Value of the object as returned by the AOS Server
  returned: always
  type: dict
  sample: {'...'}
'''

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.aos.aos import get_aos_session, find_collection_item, do_load_resource, check_aos_version, content_to_dict

#########################################################
# State Processing
#########################################################


def rack_type_absent(module, aos, my_rack_type):

    margs = module.params

    # If the module do not exist, return directly
    if my_rack_type.exists is False:
        module.exit_json(changed=False,
                         name=margs['name'],
                         id=margs['id'],
                         value={})

    # If not in check mode, delete Rack Type
    if not module.check_mode:
        try:
            my_rack_type.delete()
        except Exception:
            module.fail_json(msg="An error occurred, while trying to delete the Rack Type")

    module.exit_json(changed=True,
                     name=my_rack_type.name,
                     id=my_rack_type.id,
                     value={})


def rack_type_present(module, aos, my_rack_type):

    margs = module.params

    if margs['content'] is not None:

        if 'display_name' in module.params['content'].keys():
            do_load_resource(module, aos.RackTypes, module.params['content']['display_name'])
        else:
            module.fail_json(msg="Unable to find display_name in 'content', Mandatory")

    # if rack_type doesn't exist already, create a new one
    if my_rack_type.exists is False and 'content' not in margs.keys():
        module.fail_json(msg="'content' is mandatory for module that don't exist currently")

    module.exit_json(changed=False,
                     name=my_rack_type.name,
                     id=my_rack_type.id,
                     value=my_rack_type.value)

#########################################################
# Main Function
#########################################################


def rack_type(module):

    margs = module.params

    try:
        aos = get_aos_session(module, margs['session'])
    except Exception:
        module.fail_json(msg="Unable to login to the AOS server")

    item_name = False
    item_id = False

    if margs['content'] is not None:

        content = content_to_dict(module, margs['content'])

        if 'display_name' in content.keys():
            item_name = content['display_name']
        else:
            module.fail_json(msg="Unable to extract 'display_name' from 'content'")

    elif margs['name'] is not None:
        item_name = margs['name']

    elif margs['id'] is not None:
        item_id = margs['id']

    # ----------------------------------------------------
    # Find Object if available based on ID or Name
    # ----------------------------------------------------
    my_rack_type = find_collection_item(aos.RackTypes,
                                        item_name=item_name,
                                        item_id=item_id)

    # ----------------------------------------------------
    # Proceed based on State value
    # ----------------------------------------------------
    if margs['state'] == 'absent':

        rack_type_absent(module, aos, my_rack_type)

    elif margs['state'] == 'present':

        rack_type_present(module, aos, my_rack_type)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            session=dict(required=True, type="dict"),
            name=dict(required=False),
            id=dict(required=False),
            content=dict(required=False, type="json"),
            state=dict(required=False,
                       choices=['present', 'absent'],
                       default="present")
        ),
        mutually_exclusive=[('name', 'id', 'content')],
        required_one_of=[('name', 'id', 'content')],
        supports_check_mode=True
    )

    # Check if aos-pyez is present and match the minimum version
    check_aos_version(module, '0.6.0')

    rack_type(module)


if __name__ == "__main__":
    main()

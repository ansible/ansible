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
module: aos_template
author: Damien Garros (@dgarros)
version_added: "2.3"
short_description: Manage AOS Template
deprecated:
    removed_in: "2.9"
    why: This module does not support AOS 2.1 or later
    alternative: See new modules at U(https://www.ansible.com/ansible-apstra).
description:
  - Apstra AOS Template module let you manage your Template easily. You can create
    create and delete Template by Name, ID or by using a JSON File. This module
    is idempotent and support the I(check) mode. It's using the AOS REST API.
requirements:
  - "aos-pyez >= 0.6.0"
options:
  session:
    description:
      - An existing AOS session as obtained by M(aos_login) module.
    required: true
  name:
    description:
      - Name of the Template to manage.
        Only one of I(name), I(id) or I(src) can be set.
  id:
    description:
      - AOS Id of the Template to manage (can't be used to create a new Template),
        Only one of I(name), I(id) or I(src) can be set.
  content:
    description:
      - Datastructure of the Template to create. The data can be in YAML / JSON or
        directly a variable. It's the same datastructure that is returned
        on success in I(value).
  state:
    description:
      - Indicate what is the expected state of the Template (present or not).
    default: present
    choices: ['present', 'absent']
'''

EXAMPLES = '''

- name: "Check if an Template exist by name"
  aos_template:
    session: "{{ aos_session }}"
    name: "my-template"
    state: present

- name: "Check if an Template exist by ID"
  aos_template:
    session: "{{ aos_session }}"
    id: "45ab26fc-c2ed-4307-b330-0870488fa13e"
    state: present

- name: "Delete an Template by name"
  aos_template:
    session: "{{ aos_session }}"
    name: "my-template"
    state: absent

- name: "Delete an Template by id"
  aos_template:
    session: "{{ aos_session }}"
    id: "45ab26fc-c2ed-4307-b330-0870488fa13e"
    state: absent

- name: "Access Template 1/3"
  aos_template:
    session: "{{ aos_session }}"
    name: "my-template"
    state: present
  register: template
- name: "Save Template into a JSON file 2/3"
  copy:
    content: "{{ template.value | to_nice_json }}"
    dest: template_saved.json
- name: "Save Template into a YAML file 2/3"
  copy:
    content: "{{ template.value | to_nice_yaml }}"
    dest: template_saved.yaml

- name: "Load Template from File (Json)"
  aos_template:
    session: "{{ aos_session }}"
    content: "{{ lookup('file', 'resources/template_saved.json') }}"
    state: present

- name: "Load Template from File (yaml)"
  aos_template:
    session: "{{ aos_session }}"
    content: "{{ lookup('file', 'resources/template_saved.yaml') }}"
    state: present
'''

RETURNS = '''
name:
  description: Name of the Template
  returned: always
  type: str
  sample: My-Template

id:
  description: AOS unique ID assigned to the Template
  returned: always
  type: str
  sample: fcc4ac1c-e249-4fe7-b458-2138bfb44c06

value:
  description: Value of the object as returned by the AOS Server
  returned: always
  type: dict
  sample: {'...'}
'''

import time
import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.aos.aos import get_aos_session, find_collection_item, do_load_resource, check_aos_version, content_to_dict

#########################################################
# State Processing
#########################################################


def template_absent(module, aos, my_template):

    margs = module.params

    # If the module do not exist, return directly
    if my_template.exists is False:
        module.exit_json(changed=False,
                         name=margs['name'],
                         id=margs['id'],
                         value={})

    # If not in check mode, delete Template
    if not module.check_mode:
        try:
            # need to way 1sec before delete to workaround a current limitation in AOS
            time.sleep(1)
            my_template.delete()
        except:
            module.fail_json(msg="An error occurred, while trying to delete the Template")

    module.exit_json(changed=True,
                     name=my_template.name,
                     id=my_template.id,
                     value={})


def template_present(module, aos, my_template):

    margs = module.params

    # if content is defined, create object from Content

    if margs['content'] is not None:

        if 'display_name' in module.params['content'].keys():
            do_load_resource(module, aos.DesignTemplates, module.params['content']['display_name'])
        else:
            module.fail_json(msg="Unable to find display_name in 'content', Mandatory")

    # if template doesn't exist already, create a new one
    if my_template.exists is False and 'content' not in margs.keys():
        module.fail_json(msg="'content' is mandatory for module that don't exist currently")

    # if module already exist, just return it
    module.exit_json(changed=False,
                     name=my_template.name,
                     id=my_template.id,
                     value=my_template.value)


#########################################################
# Main Function
#########################################################
def aos_template(module):

    margs = module.params

    try:
        aos = get_aos_session(module, margs['session'])
    except:
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
    try:
        my_template = find_collection_item(aos.DesignTemplates,
                                           item_name=item_name,
                                           item_id=item_id)
    except:
        module.fail_json(msg="Unable to find the IP Pool based on name or ID, something went wrong")

    # ----------------------------------------------------
    # Proceed based on State value
    # ----------------------------------------------------
    if margs['state'] == 'absent':

        template_absent(module, aos, my_template)

    elif margs['state'] == 'present':

        template_present(module, aos, my_template)


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

    aos_template(module)

if __name__ == "__main__":
    main()

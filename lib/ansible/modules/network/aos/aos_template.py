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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: aos_template
author: Damien Garros (@dgarros)
version_added: "2.3"
short_description: Manage AOS Template
description:
  - Apstra AOS Template module let you manage your Template easily. You can create
    create and delete Template by Name, ID or by using a JSON File. This module
    is idempotent and support the I(check) mode. It's using the AOS REST API
requirements:
  - aos-pyez
options:
  session:
    description:
      - An existing AOS session as obtained by aos_login module
    required: true
  name:
    description:
      - Name of the Template to manage.
        Only one of I(name), I(id) or I(src) can be set.
    required: false
  id:
    description:
      - AOS Id of the Template to manage (can't be used to create a new Template),
        Only one of I(name), I(id) or I(src) can be set.
    required: false
  src:
    description:
      - Filepath to JSON file containing the collection item data to upload.
        Only one of I(name), I(id) or I(src) can be set.
    required: false
  state:
    description:
      - Indicate what is the expected state of the Template (present or not)
    default: present
    choices: ['present', 'absent']
    required: false
'''

EXAMPLES = '''

- name: "Check if an Template exist by name"
  aos_template:
    session: "{{ session_ok }}"
    name: "my-template"
    state: present

- name: "Check if an Template exist by ID"
  aos_template:
    session: "{{ session_ok }}"
    id: "45ab26fc-c2ed-4307-b330-0870488fa13e"
    state: present

- name: "Delete an Template by name"
  aos_template:
    session: "{{ session }}"
    name: "my-template"
    state: absent

- name: "Delete an Template by id"
  aos_template:
    session: "{{ session }}"
    id: "45ab26fc-c2ed-4307-b330-0870488fa13e"
    state: absent

# Save an Template to a file

- name: "Access Template 1/2"
  aos_template:
    session: "{{ session_ok }}"
    name: "my-template"
    state: present
  register: template
- name: "Save Template into a file 2/2"
  copy:
    content: "{{ template.value | to_nice_json }}"
    dest: template_saved.json

- name: "Load Template from a file"
  aos_template:
    session: "{{ session_ok }}"
    src: resources/template_saved.json
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

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.aos import get_aos_session, find_collection_item, get_display_name_from_file, do_load_resource, check_aos_version

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
        my_template.delete()

    module.exit_json( changed=True,
                      name=my_template.name,
                      id=my_template.id,
                      value={} )

def template_present(module, aos, my_template):

    margs = module.params

    # if src is defined
    if margs['src'] is not None:
        do_load_resource(module, aos.DesignTemplates, margs['src'])

    # if ip_pool doesn't exist already, create a new one
    if my_template.exists is False and 'src' not in margs.keys():
        module.fail_json(msg="src is mandatory for module that don't exist currently")

    # if module already exist, just return it
    module.exit_json( changed=False,
                      name=my_template.name,
                      id=my_template.id,
                      value=my_template.value )


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

    if margs['src'] is not None:
        item_name = get_display_name_from_file(module, margs['src'])

    elif margs['name'] is not None:
        item_name = margs['name']

    elif margs['id'] is not None:
        item_id = margs['id']

    #----------------------------------------------------
    # Find Object if available based on ID or Name
    #----------------------------------------------------
    my_template = find_collection_item(aos.DesignTemplates,
                        item_name=item_name,
                        item_id=item_id)

    #----------------------------------------------------
    # Proceed based on State value
    #----------------------------------------------------
    if margs['state'] == 'absent':

        template_absent(module, aos, my_template)

    elif margs['state'] == 'present':

        template_present(module, aos, my_template)

def main():
    module = AnsibleModule(
        argument_spec=dict(
            session=dict(required=True, type="dict"),
            name=dict(required=False ),
            id=dict(required=False ),
            src=dict(required=False),
            state=dict( required=False,
                        choices=['present', 'absent'],
                        default="present")
        ),
        mutually_exclusive = [('name', 'id', 'src')],
        required_one_of=[('name', 'id', 'src')],
        supports_check_mode=True
    )

    # Check if aos-pyez is present and match the minimum version
    check_aos_version(module, '0.6.0')

    aos_template(module)

if __name__ == "__main__":
    main()

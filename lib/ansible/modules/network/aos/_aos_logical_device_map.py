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
module: aos_logical_device_map
author: Damien Garros (@dgarros)
version_added: "2.3"
short_description: Manage AOS Logical Device Map
deprecated:
    removed_in: "2.9"
    why: This module does not support AOS 2.1 or later
    alternative: See new modules at U(https://www.ansible.com/ansible-apstra).
description:
  - Apstra AOS Logical Device Map module let you manage your Logical Device Map easily. You can create
    create and delete Logical Device Map by Name, ID or by using a JSON File. This module
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
      - Name of the Logical Device Map to manage.
        Only one of I(name), I(id) or I(content) can be set.
  id:
    description:
      - AOS Id of the Logical Device Map to manage (can't be used to create a new Logical Device Map),
        Only one of I(name), I(id) or I(content) can be set.
  content:
    description:
      - Datastructure of the Logical Device Map to manage. The data can be in YAML / JSON or
        directly a variable. It's the same datastructure that is returned
        on success in I(value). Only one of I(name), I(id) or I(content) can be set.
  state:
    description:
      - Indicate what is the expected state of the Logical Device Map (present or not).
    default: present
    choices: ['present', 'absent']
'''

EXAMPLES = '''

- name: "Create an Logical Device Map with one subnet"
  aos_logical_device_map:
    session: "{{ aos_session }}"
    name: "my-logical-device-map"
    state: present

- name: "Create an Logical Device Map with multiple subnets"
  aos_logical_device_map:
    session: "{{ aos_session }}"
    name: "my-other-logical-device-map"
    state: present

- name: "Check if an Logical Device Map exist with same subnets by ID"
  aos_logical_device_map:
    session: "{{ aos_session }}"
    name: "45ab26fc-c2ed-4307-b330-0870488fa13e"
    state: present

- name: "Delete an Logical Device Map by name"
  aos_logical_device_map:
    session: "{{ aos_session }}"
    name: "my-logical-device-map"
    state: absent

- name: "Delete an Logical Device Map by id"
  aos_logical_device_map:
    session: "{{ aos_session }}"
    id: "45ab26fc-c2ed-4307-b330-0870488fa13e"
    state: absent

# Save an Logical Device Map to a file

- name: "Access Logical Device Map 1/3"
  aos_logical_device_map:
    session: "{{ aos_session }}"
    name: "my-logical-device-map"
    state: present
  register: logical_device_map

- name: "Save Logical Device Map into a file in JSON 2/3"
  copy:
    content: "{{ logical_device_map.value | to_nice_json }}"
    dest: logical_device_map_saved.json

- name: "Save Logical Device Map into a file in YAML 3/3"
  copy:
    content: "{{ logical_device_map.value | to_nice_yaml }}"
    dest: logical_device_map_saved.yaml

- name: "Load Logical Device Map from a JSON file"
  aos_logical_device_map:
    session: "{{ aos_session }}"
    content: "{{ lookup('file', 'resources/logical_device_map_saved.json') }}"
    state: present

- name: "Load Logical Device Map from a YAML file"
  aos_logical_device_map:
    session: "{{ aos_session }}"
    content: "{{ lookup('file', 'resources/logical_device_map_saved.yaml') }}"
    state: present

'''

RETURNS = '''
name:
  description: Name of the Logical Device Map
  returned: always
  type: str
  sample: Server-IpAddrs

id:
  description: AOS unique ID assigned to the Logical Device Map
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
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.aos.aos import get_aos_session, find_collection_item, do_load_resource, check_aos_version, content_to_dict

#########################################################
# State Processing
#########################################################


def logical_device_map_absent(module, aos, my_log_dev_map):

    margs = module.params

    # If the module do not exist, return directly
    if my_log_dev_map.exists is False:
        module.exit_json(changed=False, name=margs['name'], id='', value={})

    # If not in check mode, delete Logical Device Map
    if not module.check_mode:
        try:
            # Need to wait for 1sec before a delete to workaround a current
            # limitation in AOS
            time.sleep(1)
            my_log_dev_map.delete()
        except:
            module.fail_json(msg="An error occurred, while trying to delete the Logical Device Map")

    module.exit_json(changed=True,
                     name=my_log_dev_map.name,
                     id=my_log_dev_map.id,
                     value={})


def logical_device_map_present(module, aos, my_log_dev_map):

    margs = module.params

    # if content is defined, create object from Content
    if margs['content'] is not None:

        if 'display_name' in module.params['content'].keys():
            do_load_resource(module, aos.LogicalDeviceMaps, module.params['content']['display_name'])
        else:
            module.fail_json(msg="Unable to find display_name in 'content', Mandatory")

    # if my_log_dev_map doesn't exist already, create a new one

    if my_log_dev_map.exists is False and 'content' not in margs.keys():
        module.fail_json(msg="'Content' is mandatory for module that don't exist currently")

    module.exit_json(changed=False,
                     name=my_log_dev_map.name,
                     id=my_log_dev_map.id,
                     value=my_log_dev_map.value)

#########################################################
# Main Function
#########################################################


def logical_device_map(module):

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
        my_log_dev_map = find_collection_item(aos.LogicalDeviceMaps,
                                              item_name=item_name,
                                              item_id=item_id)
    except:
        module.fail_json(msg="Unable to find the Logical Device Map based on name or ID, something went wrong")

    # ----------------------------------------------------
    # Proceed based on State value
    # ----------------------------------------------------
    if margs['state'] == 'absent':

        logical_device_map_absent(module, aos, my_log_dev_map)

    elif margs['state'] == 'present':

        logical_device_map_present(module, aos, my_log_dev_map)


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

    logical_device_map(module)

if __name__ == "__main__":
    main()

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
module: aos_external_router
author: Damien Garros (@dgarros)
version_added: "2.3"
short_description: Manage AOS External Router
deprecated:
    removed_in: "2.9"
    why: This module does not support AOS 2.1 or later
    alternative: See new modules at U(https://www.ansible.com/ansible-apstra).
description:
  - Apstra AOS External Router module let you manage your External Router easily. You can create
    create and delete External Router by Name, ID or by using a JSON File. This module
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
      - Name of the External Router to manage.
        Only one of I(name), I(id) or I(content) can be set.
  id:
    description:
      - AOS Id of the External Router to manage (can't be used to create a new External Router),
        Only one of I(name), I(id) or I(content) can be set.
  content:
    description:
      - Datastructure of the External Router to create. The format is defined by the
        I(content_format) parameter. It's the same datastructure that is returned
        on success in I(value).
  state:
    description:
      - Indicate what is the expected state of the External Router (present or not).
    default: present
    choices: ['present', 'absent']
  loopback:
    description:
      - IP address of the Loopback interface of the external_router.
  asn:
    description:
      - ASN id of the external_router.
'''

EXAMPLES = '''

- name: "Create an External Router"
  aos_external_router:
    session: "{{ aos_session }}"
    name: "my-external-router"
    loopback: 10.0.0.1
    asn: 65000
    state: present

- name: "Check if an External Router exist by ID"
  aos_external_router:
    session: "{{ aos_session }}"
    name: "45ab26fc-c2ed-4307-b330-0870488fa13e"
    state: present

- name: "Delete an External Router by name"
  aos_external_router:
    session: "{{ aos_session }}"
    name: "my-external-router"
    state: absent

- name: "Delete an External Router by id"
  aos_external_router:
    session: "{{ aos_session }}"
    id: "45ab26fc-c2ed-4307-b330-0870488fa13e"
    state: absent

# Save an External Router to a file
- name: "Access External Router 1/3"
  aos_external_router:
    session: "{{ aos_session }}"
    name: "my-external-router"
    state: present
  register: external_router

- name: "Save External Router into a file in JSON 2/3"
  copy:
    content: "{{ external_router.value | to_nice_json }}"
    dest: external_router_saved.json

- name: "Save External Router into a file in YAML 3/3"
  copy:
    content: "{{ external_router.value | to_nice_yaml }}"
    dest: external_router_saved.yaml

- name: "Load External Router from a JSON file"
  aos_external_router:
    session: "{{ aos_session }}"
    content: "{{ lookup('file', 'resources/external_router_saved.json') }}"
    state: present

- name: "Load External Router from a YAML file"
  aos_external_router:
    session: "{{ aos_session }}"
    content: "{{ lookup('file', 'resources/external_router_saved.yaml') }}"
    state: present
'''

RETURNS = '''
name:
  description: Name of the External Router
  returned: always
  type: str
  sample: Server-IpAddrs

id:
  description: AOS unique ID assigned to the External Router
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


def create_new_ext_router(module, my_ext_router, name, loopback, asn):

    # Create value
    datum = dict(display_name=name, address=loopback, asn=asn)

    my_ext_router.datum = datum

    # Write to AOS
    return my_ext_router.write()

#########################################################
# State Processing
#########################################################


def ext_router_absent(module, aos, my_ext_router):

    margs = module.params

    # If the module do not exist, return directly
    if my_ext_router.exists is False:
        module.exit_json(changed=False,
                         name=margs['name'],
                         id=margs['id'],
                         value={})

    # If not in check mode, delete External Router
    if not module.check_mode:
        try:
            # Add Sleep before delete to workaround a bug in AOS
            time.sleep(2)
            my_ext_router.delete()
        except Exception:
            module.fail_json(msg="An error occurred, while trying to delete the External Router")

    module.exit_json(changed=True,
                     name=my_ext_router.name,
                     id=my_ext_router.id,
                     value={})


def ext_router_present(module, aos, my_ext_router):

    margs = module.params

    # if content is defined, create object from Content
    if my_ext_router.exists is False and margs['content'] is not None:
        do_load_resource(module, aos.ExternalRouters, module.params['content']['display_name'])

    # if my_ext_router doesn't exist already, create a new one
    if my_ext_router.exists is False and margs['name'] is None:
        module.fail_json(msg="Name is mandatory for module that don't exist currently")

    elif my_ext_router.exists is False:

        if not module.check_mode:
            try:
                my_new_ext_router = create_new_ext_router(module,
                                                          my_ext_router,
                                                          margs['name'],
                                                          margs['loopback'],
                                                          margs['asn'])
                my_ext_router = my_new_ext_router
            except Exception:
                module.fail_json(msg="An error occurred while trying to create a new External Router")

        module.exit_json(changed=True,
                         name=my_ext_router.name,
                         id=my_ext_router.id,
                         value=my_ext_router.value)

    # if external Router already exist, check if loopback and ASN are the same
    # if same just return the object and report change false
    loopback = None
    asn = None

    # Identify the Loopback, parameter 'loopback' has priority over 'content'
    if margs['loopback'] is not None:
        loopback = margs['loopback']
    elif margs['content'] is not None:
        if 'address' in margs['content'].keys():
            loopback = margs['content']['address']

    # Identify the ASN, parameter 'asn' has priority over 'content'
    if margs['asn'] is not None:
        asn = margs['asn']
    elif margs['content'] is not None:
        if 'asn' in margs['content'].keys():
            asn = margs['content']['asn']

    # Compare Loopback and ASN if defined
    if loopback is not None:
        if loopback != my_ext_router.value['address']:
            module.fail_json(msg="my_ext_router already exist but Loopback is different, currently not supported to update a module")

    if asn is not None:
        if int(asn) != int(my_ext_router.value['asn']):
            module.fail_json(msg="my_ext_router already exist but ASN is different, currently not supported to update a module")

    module.exit_json(changed=False,
                     name=my_ext_router.name,
                     id=my_ext_router.id,
                     value=my_ext_router.value)

#########################################################
# Main Function
#########################################################


def ext_router(module):

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
    try:
        my_ext_router = find_collection_item(aos.ExternalRouters,
                                             item_name=item_name,
                                             item_id=item_id)
    except Exception:
        module.fail_json(msg="Unable to find the IP Pool based on name or ID, something went wrong")

    # ----------------------------------------------------
    # Proceed based on State value
    # ----------------------------------------------------
    if margs['state'] == 'absent':

        ext_router_absent(module, aos, my_ext_router)

    elif margs['state'] == 'present':

        ext_router_present(module, aos, my_ext_router)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            session=dict(required=True, type="dict"),
            name=dict(required=False),
            id=dict(required=False),
            content=dict(required=False, type="json"),
            state=dict(required=False,
                       choices=['present', 'absent'],
                       default="present"),
            loopback=dict(required=False),
            asn=dict(required=False)
        ),
        mutually_exclusive=[('name', 'id', 'content')],
        required_one_of=[('name', 'id', 'content')],
        supports_check_mode=True
    )

    # Check if aos-pyez is present and match the minimum version
    check_aos_version(module, '0.6.0')

    ext_router(module)


if __name__ == "__main__":
    main()

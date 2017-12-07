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
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: aos_asn_pool
author: Damien Garros (@dgarros)
version_added: "2.3"
short_description: Manage AOS ASN Pool
description:
  - Apstra AOS ASN Pool module let you manage your ASN Pool easily. You can create
    and delete ASN Pool by Name, ID or by using a JSON File. This module
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
      - Name of the ASN Pool to manage.
        Only one of I(name), I(id) or I(content) can be set.
  id:
    description:
      - AOS Id of the ASN Pool to manage.
        Only one of I(name), I(id) or I(content) can be set.
  content:
    description:
      - Datastructure of the ASN Pool to manage. The data can be in YAML / JSON or
        directly a variable. It's the same datastructure that is returned
        on success in I(value).
  state:
    description:
      - Indicate what is the expected state of the ASN Pool (present or not).
    default: present
    choices: ['present', 'absent']
  ranges:
    description:
      - List of ASNs ranges to add to the ASN Pool. Each range must have 2 values.
'''

EXAMPLES = '''

- name: "Create ASN Pool"
  aos_asn_pool:
    session: "{{ aos_session }}"
    name: "my-asn-pool"
    ranges:
      - [ 100, 200 ]
    state: present
  register: asnpool

- name: "Save ASN Pool into a file in JSON"
  copy:
    content: "{{ asnpool.value | to_nice_json }}"
    dest: resources/asn_pool_saved.json

- name: "Save ASN Pool into a file in YAML"
  copy:
    content: "{{ asnpool.value | to_nice_yaml }}"
    dest: resources/asn_pool_saved.yaml


- name: "Delete ASN Pool"
  aos_asn_pool:
    session: "{{ aos_session }}"
    name: "my-asn-pool"
    state: absent

- name: "Load ASN Pool from File(JSON)"
  aos_asn_pool:
    session: "{{ aos_session }}"
    content: "{{ lookup('file', 'resources/asn_pool_saved.json') }}"
    state: present

- name: "Delete ASN Pool from File(JSON)"
  aos_asn_pool:
    session: "{{ aos_session }}"
    content: "{{ lookup('file', 'resources/asn_pool_saved.json') }}"
    state: absent

- name: "Load ASN Pool from File(Yaml)"
  aos_asn_pool:
    session: "{{ aos_session }}"
    content: "{{ lookup('file', 'resources/asn_pool_saved.yaml') }}"
    state: present
  register: test

- name: "Delete ASN Pool from File(Yaml)"
  aos_asn_pool:
    session: "{{ aos_session }}"
    content: "{{ lookup('file', 'resources/asn_pool_saved.yaml') }}"
    state: absent
'''

RETURNS = '''
name:
  description: Name of the ASN Pool
  returned: always
  type: str
  sample: Private-ASN-pool

id:
  description: AOS unique ID assigned to the ASN Pool
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


def check_ranges_are_valid(module, ranges):

    i = 1
    for range in ranges:
        if not isinstance(range, list):
            module.fail_json(msg="Range (%i) must be a list not %s" % (i, type(range)))
        elif len(range) != 2:
            module.fail_json(msg="Range (%i) must be a list of 2 members, not %i" % (i, len(range)))
        elif not isinstance(range[0], int):
            module.fail_json(msg="1st element of range (%i) must be integer instead of %s " % (i, type(range[0])))
        elif not isinstance(range[1], int):
            module.fail_json(msg="2nd element of range (%i) must be integer instead of %s " % (i, type(range[1])))
        elif range[1] <= range[0]:
            module.fail_json(msg="2nd element of range (%i) must be bigger than 1st " % (i))

        i += 1

    return True


def get_list_of_range(asn_pool):
    ranges = []

    for range in asn_pool.value['ranges']:
        ranges.append([range['first'], range['last']])

    return ranges


def create_new_asn_pool(asn_pool, name, ranges):

    # Create value
    datum = dict(display_name=name, ranges=[])
    for range in ranges:
        datum['ranges'].append(dict(first=range[0], last=range[1]))

    asn_pool.datum = datum

    # Write to AOS
    return asn_pool.write()


def asn_pool_absent(module, aos, my_pool):

    margs = module.params

    # If the module do not exist, return directly
    if my_pool.exists is False:
        module.exit_json(changed=False, name=margs['name'], id='', value={})

    # Check if object is currently in Use or Not
    # If in Use, return an error
    if my_pool.value:
        if my_pool.value['status'] != 'not_in_use':
            module.fail_json(msg="Unable to delete ASN Pool '%s' is currently in use" % my_pool.name)
    else:
        module.fail_json(msg="ASN Pool object has an invalid format, value['status'] must be defined")

    # If not in check mode, delete Ip Pool
    if not module.check_mode:
        try:
            my_pool.delete()
        except:
            module.fail_json(msg="An error occurred, while trying to delete the ASN Pool")

    module.exit_json(changed=True,
                     name=my_pool.name,
                     id=my_pool.id,
                     value={})


def asn_pool_present(module, aos, my_pool):

    margs = module.params

    # if content is defined, create object from Content
    if margs['content'] is not None:

        if 'display_name' in module.params['content'].keys():
            do_load_resource(module, aos.AsnPools, module.params['content']['display_name'])
        else:
            module.fail_json(msg="Unable to find display_name in 'content', Mandatory")

    # if asn_pool doesn't exist already, create a new one
    if my_pool.exists is False and 'name' not in margs.keys():
        module.fail_json(msg="name is mandatory for module that don't exist currently")

    elif my_pool.exists is False:

        if not module.check_mode:
            try:
                my_new_pool = create_new_asn_pool(my_pool, margs['name'], margs['ranges'])
                my_pool = my_new_pool
            except:
                module.fail_json(msg="An error occurred while trying to create a new ASN Pool ")

        module.exit_json(changed=True,
                         name=my_pool.name,
                         id=my_pool.id,
                         value=my_pool.value)

    # Currently only check if the pool exist or not
    #    if exist return change false
    #
    # Later it would be good to check if the list of ASN are same
    # if pool already exist, check if list of ASN is the same
    # if same just return the object and report change false
    # if set(get_list_of_range(my_pool)) == set(margs['ranges']):
    module.exit_json(changed=False,
                     name=my_pool.name,
                     id=my_pool.id,
                     value=my_pool.value)

# ########################################################
# Main Function
# ########################################################


def asn_pool(module):

    margs = module.params

    try:
        aos = get_aos_session(module, margs['session'])
    except:
        module.fail_json(msg="Unable to login to the AOS server")

    item_name = False
    item_id = False

    # Check ID / Name and Content
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

    # If ranges are provided, check if they are valid
    if 'ranges' in margs.keys():
        check_ranges_are_valid(module, margs['ranges'])

    # ----------------------------------------------------
    # Find Object if available based on ID or Name
    # ----------------------------------------------------
    try:
        my_pool = find_collection_item(aos.AsnPools,
                                       item_name=item_name,
                                       item_id=item_id)
    except:
        module.fail_json(msg="Unable to find the IP Pool based on name or ID, something went wrong")

    # ----------------------------------------------------
    # Proceed based on State value
    # ----------------------------------------------------
    if margs['state'] == 'absent':

        asn_pool_absent(module, aos, my_pool)

    elif margs['state'] == 'present':

        asn_pool_present(module, aos, my_pool)


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
            ranges=dict(required=False, type="list", default=[])
        ),
        mutually_exclusive=[('name', 'id', 'content')],
        required_one_of=[('name', 'id', 'content')],
        supports_check_mode=True
    )

    # Check if aos-pyez is present and match the minimum version
    check_aos_version(module, '0.6.0')

    asn_pool(module)

if __name__ == "__main__":
    main()

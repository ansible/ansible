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
module: aos_ip_pool
author: Damien Garros (@dgarros)
version_added: "2.3"
short_description: Manage AOS IP Pool
deprecated:
    removed_in: "2.9"
    why: This module does not support AOS 2.1 or later
    alternative: See new modules at U(https://www.ansible.com/ansible-apstra).
description:
  - Apstra AOS Ip Pool module let you manage your IP Pool easily. You can create
    create and delete IP Pool by Name, ID or by using a JSON File. This module
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
      - Name of the IP Pool to manage.
        Only one of I(name), I(id) or I(content) can be set.
  id:
    description:
      - AOS Id of the IP Pool to manage (can't be used to create a new IP Pool),
        Only one of I(name), I(id) or I(content) can be set.
  content:
    description:
      - Datastructure of the IP Pool to manage. The data can be in YAML / JSON or
        directly a variable. It's the same datastructure that is returned
        on success in I(value).
  state:
    description:
      - Indicate what is the expected state of the IP Pool (present or not).
    default: present
    choices: ['present', 'absent']
  subnets:
    description:
      - List of subnet that needs to be part of the IP Pool.
'''

EXAMPLES = '''

- name: "Create an IP Pool with one subnet"
  aos_ip_pool:
    session: "{{ aos_session }}"
    name: "my-ip-pool"
    subnets: [ 172.10.0.0/16 ]
    state: present

- name: "Create an IP Pool with multiple subnets"
  aos_ip_pool:
    session: "{{ aos_session }}"
    name: "my-other-ip-pool"
    subnets: [ 172.10.0.0/16, 192.168.0.0./24 ]
    state: present

- name: "Check if an IP Pool exist with same subnets by ID"
  aos_ip_pool:
    session: "{{ aos_session }}"
    name: "45ab26fc-c2ed-4307-b330-0870488fa13e"
    subnets: [ 172.10.0.0/16, 192.168.0.0./24 ]
    state: present

- name: "Delete an IP Pool by name"
  aos_ip_pool:
    session: "{{ aos_session }}"
    name: "my-ip-pool"
    state: absent

- name: "Delete an IP pool by id"
  aos_ip_pool:
    session: "{{ aos_session }}"
    id: "45ab26fc-c2ed-4307-b330-0870488fa13e"
    state: absent

# Save an IP Pool to a file

- name: "Access IP Pool 1/3"
  aos_ip_pool:
    session: "{{ aos_session }}"
    name: "my-ip-pool"
    subnets: [ 172.10.0.0/16, 172.12.0.0/16 ]
    state: present
  register: ip_pool

- name: "Save Ip Pool into a file in JSON 2/3"
  copy:
    content: "{{ ip_pool.value | to_nice_json }}"
    dest: ip_pool_saved.json

- name: "Save Ip Pool into a file in YAML 3/3"
  copy:
    content: "{{ ip_pool.value | to_nice_yaml }}"
    dest: ip_pool_saved.yaml

- name: "Load IP Pool from a JSON file"
  aos_ip_pool:
    session: "{{ aos_session }}"
    content: "{{ lookup('file', 'resources/ip_pool_saved.json') }}"
    state: present

- name: "Load IP Pool from a YAML file"
  aos_ip_pool:
    session: "{{ aos_session }}"
    content: "{{ lookup('file', 'resources/ip_pool_saved.yaml') }}"
    state: present

- name: "Load IP Pool from a Variable"
  aos_ip_pool:
    session: "{{ aos_session }}"
    content:
      display_name: my-ip-pool
      id: 4276738d-6f86-4034-9656-4bff94a34ea7
      subnets:
        - network: 172.10.0.0/16
        - network: 172.12.0.0/16
    state: present
'''

RETURNS = '''
name:
  description: Name of the IP Pool
  returned: always
  type: str
  sample: Server-IpAddrs

id:
  description: AOS unique ID assigned to the IP Pool
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


def get_list_of_subnets(ip_pool):
    subnets = []

    for subnet in ip_pool.value['subnets']:
        subnets.append(subnet['network'])

    return subnets


def create_new_ip_pool(ip_pool, name, subnets):

    # Create value
    datum = dict(display_name=name, subnets=[])
    for subnet in subnets:
        datum['subnets'].append(dict(network=subnet))

    ip_pool.datum = datum

    # Write to AOS
    return ip_pool.write()

#########################################################
# State Processing
#########################################################


def ip_pool_absent(module, aos, my_pool):

    margs = module.params

    # If the module do not exist, return directly
    if my_pool.exists is False:
        module.exit_json(changed=False, name=margs['name'], id='', value={})

    # Check if object is currently in Use or Not
    # If in Use, return an error
    if my_pool.value:
        if my_pool.value['status'] != 'not_in_use':
            module.fail_json(msg="unable to delete this ip Pool, currently in use")
    else:
        module.fail_json(msg="Ip Pool object has an invalid format, value['status'] must be defined")

    # If not in check mode, delete Ip Pool
    if not module.check_mode:
        try:
            my_pool.delete()
        except:
            module.fail_json(msg="An error occurred, while trying to delete the IP Pool")

    module.exit_json(changed=True,
                     name=my_pool.name,
                     id=my_pool.id,
                     value={})


def ip_pool_present(module, aos, my_pool):

    margs = module.params

    # if content is defined, create object from Content
    try:
        if margs['content'] is not None:

            if 'display_name' in module.params['content'].keys():
                do_load_resource(module, aos.IpPools, module.params['content']['display_name'])
            else:
                module.fail_json(msg="Unable to find display_name in 'content', Mandatory")

    except:
        module.fail_json(msg="Unable to load resource from content, something went wrong")

    # if ip_pool doesn't exist already, create a new one

    if my_pool.exists is False and 'name' not in margs.keys():
        module.fail_json(msg="Name is mandatory for module that don't exist currently")

    elif my_pool.exists is False:

        if not module.check_mode:
            try:
                my_new_pool = create_new_ip_pool(my_pool, margs['name'], margs['subnets'])
                my_pool = my_new_pool
            except:
                module.fail_json(msg="An error occurred while trying to create a new IP Pool ")

        module.exit_json(changed=True,
                         name=my_pool.name,
                         id=my_pool.id,
                         value=my_pool.value)

    # if pool already exist, check if list of network is the same
    # if same just return the object and report change false
    if set(get_list_of_subnets(my_pool)) == set(margs['subnets']):
        module.exit_json(changed=False,
                         name=my_pool.name,
                         id=my_pool.id,
                         value=my_pool.value)
    else:
        module.fail_json(msg="ip_pool already exist but value is different, currently not supported to update a module")

#########################################################
# Main Function
#########################################################


def ip_pool(module):

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
        my_pool = find_collection_item(aos.IpPools,
                                       item_name=item_name,
                                       item_id=item_id)
    except:
        module.fail_json(msg="Unable to find the IP Pool based on name or ID, something went wrong")

    # ----------------------------------------------------
    # Proceed based on State value
    # ----------------------------------------------------
    if margs['state'] == 'absent':

        ip_pool_absent(module, aos, my_pool)

    elif margs['state'] == 'present':

        ip_pool_present(module, aos, my_pool)


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
            subnets=dict(required=False, type="list")
        ),
        mutually_exclusive=[('name', 'id', 'content')],
        required_one_of=[('name', 'id', 'content')],
        supports_check_mode=True
    )

    # Check if aos-pyez is present and match the minimum version
    check_aos_version(module, '0.6.0')

    ip_pool(module)

if __name__ == "__main__":
    main()

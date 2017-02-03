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
module: aos_ip_pool
author: damien@apstra.com (@dgarros)
version_added: "2.3"
short_description: Manage AOS IP Pool
description:
  - Used to add an IP Pool to AOS-server from playbook
  - Used to add an IP Pool to AOS-server from a JSON file
  - Used to delete an IP Pool
  - Used to gather an IP Pool
requirements:
  - aos-pyez
options:
  session:
    description:
      - An existing AOS session as obtained by aos_login module
    required: true
  name:
    description:
      - Name of the IP Pool to manage
    required: false
  id:
    description:
      - AOS Id of the IP Pool to manage (can't be used to create a new IP Pool),
        it's an alternative to C(name) and can't be use with C(name)
    required: false
  state:
    description:
      - Indicate
    default: present
    choices: ['present', 'absent']
    required: false
  subnets:
    description:
      - Filepath to JSON file containing the collection item data
    default: []
    required: false
  src:
    description:
      - Filepath to JSON file containing the collection item data
    required: false
'''

EXAMPLES = '''
# add an IP address pool to AOS-server

- aos_ip_pool:
    session: "{{ aos_session }}"
    name:
    state: present
    src: resources/ip-pools/dc1_switches.json

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
from ansible.module_utils.aos import *

def get_list_of_subnets(ip_pool):
    subnets = []

    for subnet in ip_pool.value['subnets']:
        subnets.append(subnet['network'])

    return subnets

def create_new_ip_pool(ip_pool, name, subnets=[]):

    # Create value
    datum = dict(display_name=name, subnets=[])
    for subnet in subnets:
        datum['subnets'].append(dict(network=subnet))

    ip_pool.datum = datum

    ## Write to AOS
    return ip_pool.write()

#########################################################
# Main Function
#########################################################
def ip_pool(module):

    margs = module.params

    # TODO add Exception handling for login error
    aos = get_aos_session(margs['session'])

    item_name = False
    item_id = False

    if 'name' in margs.keys():
        item_name = margs['name']

    if 'id' in margs.keys():
        item_id = margs['id']

    #----------------------------------------------------
    # Find Object if available based on ID or Name
    #----------------------------------------------------
    my_pool = find_collection_item(aos.IpPools,
                        item_name=item_name,
                        item_id=item_id)

    #----------------------------------------------------
    # State == Absent
    #----------------------------------------------------
    if margs['state'] == 'absent':

        # If the module do not exist, return directly
        if my_pool.exists == False:
            module.exit_json(changed=False, name=margs['name'], id='', value={})

        ## Check if object is currently in Use or Not
        # If in Use, return an error
        in_use = False
        if my_pool.value:
            if my_pool.value['status'] != 'not_in_use':
                in_use = True
                module.fail_json(msg="unable to delete this ip Pool, currently in use")
        else:
            module.fail_json(msg="Ip Pool object has an invalid format, value['status'] must be defined")

        # If not in check mode, delete Ip Pool
        if not module.check_mode:
            my_pool.delete()

        module.exit_json( changed=True,
                          name=my_pool.name,
                          id=my_pool.id,
                          value={} )

    #----------------------------------------------------
    # State == Present
    #----------------------------------------------------
    elif margs['state'] == 'present':

        # if ip_pool doesn't exist already, create a new one
        if my_pool.exists == False and 'name' not in margs.keys():
            module.fail_json(msg="name is mandatory for module that don't exist currently")

        elif my_pool.exists == False:

            if not module.check_mode:
                my_new_pool = create_new_ip_pool(my_pool, margs['name'], margs['subnets'])
                my_pool = my_new_pool

            module.exit_json( changed=True,
                              name=my_pool.name,
                              id=my_pool.id,
                              value=my_pool.value )

        # if pool already exist, check if list of network is the same
        # if same just return the object and report change false
        if set(get_list_of_subnets(my_pool)) == set(margs['subnets']):
            module.exit_json( changed=False,
                              name=my_pool.name,
                              id=my_pool.id,
                              value=my_pool.value )
        else:
            module.fail_json(msg="ip_pool already exist but value is different, currently not supported to update a module")

def main():
    module = AnsibleModule(
        argument_spec=dict(
            session=dict(required=True, type="dict"),
            name=dict(required=False ),
            id=dict(required=False ),
            state=dict( required=False,
                        choices=['present', 'absent'],
                        default="present"),
            subnets=dict(required=False, type="list")
        ),
        mutually_exclusive = [('name', 'id')],
        supports_check_mode=True
    )

    ip_pool(module)

if __name__ == "__main__":
    main()

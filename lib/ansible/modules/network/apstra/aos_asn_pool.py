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
module: aos_asn_pool
author: damien@apstra.com (@dgarros)
version_added: "2.3"
short_description: Manage AOS ASN Pool
description:
  - Used to add an ASN Pool to AOS-server from playbook
  - Used to add an ASN Pool to AOS-server from a JSON file
  - Used to delete an ASN Pool
  - Used to gather an ASN Pool
requirements:
  - aos-pyez
options:
  session:
    description:
      - An existing AOS session as obtained by aos_login module
    required: true
  name:
    description:
      - Name of the ASN Pool to manage
    required: false
  id:
    description:
      - AOS Id of the ASN Pool to manage (can't be used to create a new ASN Pool),
        it's an alternative to C(name) and can't be use with C(name)
    required: false
  state:
    description:
      - Indicate 
    default: present
    choices: ['present', 'absent']
    required: false
  ranges:
    description:
      - List of ASNs ranges to add to the ASN Pool
    default: []
    required: false
  src:
    description:
      - Filepath to JSON file containing the collection item data
    required: false
'''

EXAMPLES = '''
# add an ASN pool to AOS-server


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
from ansible.module_utils.aos import *


def check_ranges_are_valid(module, ranges):

    i = 1
    for range in ranges:
        if not isinstance(range, list) :
            module.fail_json(msg="Range (%i) must be a list not %s" % (i, type(range)))
        elif len(range) != 2:
            module.fail_json(msg="Range (%i) must be a list of 2 members, not %i" % (i, len(range)))
        elif not isinstance( range[0], int ):
            module.fail_json(msg="1st element of range (%i) must be integer instead of %s " % (i,type(range[0])))
        elif not isinstance( range[1], int ):
            module.fail_json(msg="2nd element of range (%i) must be integer instead of %s " % (i,type(range[1])))
        elif range[1] <= range[0]:
            module.fail_json(msg="2nd element of range (%i) must be bigger than 1st " % (i))

        i += 1

    return True

def get_list_of_range(asn_pool):
    ranges = []

    for range in asn_pool.value['ranges']:
        ranges.append([ range['first'], range['last']])

    return ranges

def create_new_asn_pool(asn_pool, name, ranges=[]):

    # Create value
    datum = dict(display_name=name, ranges=[])
    for range in ranges:
        datum['ranges'].append(dict(first=range[0],last=range[1]))

    asn_pool.datum = datum

    ## Write to AOS
    return asn_pool.write()

#########################################################
# Main Function
#########################################################
def asn_pool(module):

    margs = module.params

    aos = get_aos_session(margs['session'])

    item_name = False
    item_id = False

    if 'name' in margs.keys():
        item_name = margs['name']

    if 'id' in margs.keys():
        item_id = margs['id']

    if 'ranges' in margs.keys():
        check_ranges_are_valid(module, margs['ranges'])

    #----------------------------------------------------
    # Find Object if available based on ID or Name
    #----------------------------------------------------
    my_pool = find_collection_item(aos.AsnPools,
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
                module.fail_json(msg="Unable to delete this Asn Pool is currently in use")
        else:
            module.fail_json(msg="Asn Pool object has an invalid format, value['status'] must be defined")

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

        # if asn_pool doesn't exist already, create a new one
        if my_pool.exists == False and 'name' not in margs.keys():
            module.fail_json(msg="name is mandatory for module that don't exist currently")

        elif my_pool.exists == False:

            if not module.check_mode:
                my_new_pool = create_new_asn_pool(my_pool, margs['name'], margs['ranges'])
                my_pool = my_new_pool

            module.exit_json( changed=True,
                              name=my_pool.name,
                              id=my_pool.id,
                              value=my_pool.value )

        # Currently only check if the pool exist or not
        #    if exist return change false
        # Later it would be good to check if the list of ASN are same
        # if pool already exist, check if list of ASN is the same
        # if same just return the object and report change false
        # if set(get_list_of_range(my_pool)) == set(margs['ranges']):
        module.exit_json( changed=False,
                          name=my_pool.name,
                          id=my_pool.id,
                          value=my_pool.value )
        # else:
        #     module.fail_json(msg="ASN Pool already exist but value is different, currently not supported to update a module")

def main():
    module = AnsibleModule(
        argument_spec=dict(
            session=dict(required=True, type="dict"),
            name=dict(required=False ),
            id=dict(required=False ),
            state=dict( required=False,
                        choices=['present', 'absent'],
                        default="present"),
            ranges=dict(required=False, type="list", default=[])
        ),
        mutually_exclusive = [('name', 'id')],
        supports_check_mode=True
    )

    asn_pool(module)

if __name__ == "__main__":
    main()

#!/usr/bin/python
#
# Copyright (c) 2017 Alibaba Group Holding Limited. He Guimin <heguimin36@163.com.com>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see http://www.gnu.org/licenses/.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'curated'}

DOCUMENTATION = """
---
module: alicloud_route_entry
version_added: "2.4"
short_description: Manage route entry for Alicloud virtual private cloud,
description:
    - Manage route entry for Alicloud virtual private cloud.
      Create or Delete route entry and Query route entries in one route table.
options:
  status:
    description:
      -  Whether or not to create, delete or query route entry.
    choices: ['present', 'absent', 'list']
    required: false
    default: present
    aliases: [ 'state' ]
  router_id:
    description:
      - The ID of virtual router to which route entry belongs.
    required: true
    default: null
  destination_cidrblock:
    description:
      - The destination CIDR or Ip address of route entry. Such as:192.168.0.0/24 or 192.168.0.1.
        There is not the same destination cidr_block in the same route table. It is required when creating route entry.
    required: false
    default: null
    aliases: ['dest_cidrblock', 'cidr_block']
  nexthop_id:
    description:
      - The next hop ID of route entry. It is required when creating a route entry.
    required: false
    default: null
    aliases: ['hop_id']
  nexthop_type:
    description:
      - The next hop type of route entry.
    required: false
    default: 'Instance'
    choices: ['Instance', 'Tunnel', 'HaVip', 'RouterInterface']
    aliases: ['hop_type']
notes:
  - The max items of route entry no more than 48 in the same route table.
  - The destination_cidrblock can't have the same cidr block as vswitch and can't belong to its in the same vpc.
  - The destination_cidrblock can't be 100.64.0.0/10 and can't belong to it.
  - When status is 'list', the parameters 'route_table_id', 'destination_cidrblock' and 'nexthop_id' are optional.
author:
  - "He Guimin (@xiaozhu36)"
"""

EXAMPLES = """

# basic provisioning example to create custom route
- name: create route entry
  hosts: localhost
  connection: local
  vars:
    alicloud_region: cn-hongkong
    state: present
    cidr_block: '192.168.4.0/24'
    nexthop_id: 'xxxxxxxxxx'
    router_id: 'XXXXXXXX'
  tasks:
    - name: create route entry
      alicloud_route_entry:
        alicloud_region: '{{ alicloud_region }}'
        state: '{{ state }}'
        destination_cidrblock: '{{ cidr_block }}'
        nexthop_id: '{{ nexthop_id }}'
        router_id: 'XXXXXXXX'
      register: result
    - debug: var=result

# basic provisioning example to delete custom route
- name: delete route entry
  hosts: localhost
  connection: local
  vars:
    alicloud_region: cn-hongkong
    destination_cidrblock: "192.168.4.0/24"
    next_hop_id: "xxxxxxxxxx"
    router_id: 'XXXXXXXX'
    state: present
  tasks:
    - name: delete route
      alicloud_route_entry:
        alicloud_region: '{{ alicloud_region }}'
        destination_cidrblock: '{{ cidr_block }}'
        nexthop_id: '{{ nexthop_id }}'
        router_id: 'XXXXXXXX'
        state: '{{ state }}'
      register: result
    - debug: var=result

# basic provisioning example to querying route entries
- name: get route entry list
  hosts: localhost
  connection: local
  vars:
    alicloud_region: cn-hongkong
    router_id: xxxxxxxxxx
    state: list
  tasks:
    - name: get vrouter list
      alicloud_route_entry:
        alicloud_region: '{{ alicloud_region }}'
        router_id: '{{ router_id }}'
        state: '{{ state }}'
      register: result
    - debug: var=result

"""

RETURN = '''

destination_cidrblock:
    description: the destination CIDR block of route entry
    returned: on present and absent
    type: string
    sample: "10.0.14.0/24"

route_entry:
    description: Details about the ecs route entry that was created.
    returned: on present
    type: dict
    sample: {
        "destination_cidrblock": "10.0.14.0/24",
        "nexthop_id": "i-2zejbnp5zv525per4g84",
        "nexthop_type": "Instance",
        "route_table_id": "vtb-2zeeokge820zn0kqawmi9",
        "status": "Available",
        "type": "Custom"
    }

destination_cidrblocks:
    description: the list destination CIDR blocks of route entries in one route table
    returned: on list
    type: list
    sample: ["10.0.14.0/24", "10.0.13.0/24", "100.64.0.0/10"]

"route_entries":
    description: Details about the ecs route entries that were retrieved in one route table.
    returned: on list
    type: list
    sample: [
        {
            "destination_cidrblock": "10.0.14.0/24",
            "nexthop_id": "i-2zejbnp5zv525per4g84",
            "nexthop_type": "Instance",
            "route_table_id": "vtb-2zeeokge820zn0kqawmi9",
            "status": "Available",
            "type": "Custom"
        },
        {
            "destination_cidrblock": "10.0.13.0/24",
            "nexthop_id": "",
            "nexthop_type": "local",
            "route_table_id": "vtb-2zeeokge820zn0kqawmi9",
            "status": "Available",
            "type": "System"
        }
    ]
route_table_id:
    description: the ID of route table to which route entry belongs
    returned: on present and absent
    type: string
    sample: "vtb-2zemlj5nscgoicjnxes7h"
total:
    description: The number of all route entries after retrieving route entry.
    returned: on list
    type: int
    sample: 3
'''

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.alicloud_ecs import ecs_argument_spec, vpc_connect
from footmark.exception import VPCResponseError

HAS_FOOTMARK = False

try:
    from footmark.exception import ECSResponseError
    HAS_FOOTMARK = True
except ImportError:
    HAS_FOOTMARK = False


def get_route_entry_basic(entry):
    """
    Format vpc result and returns it as a dictionary
    """
    return {'route_table_id': entry.route_table_id, 'destination_cidrblock': entry.destination_cidrblock}


def get_route_entry_detail(entry):
    """
    Format vpc result and returns it as a dictionary
    """
    return {'route_table_id': entry.route_table_id, 'destination_cidrblock': entry.destination_cidrblock, 'type': entry.type,
            "nexthop_type": entry.nexthop_type, 'nexthop_id': entry.nexthop_id, 'status': entry.status}


def create_route_entry(module, vpc, route_table_id):
    """
    Create VSwitch
    :param module: Ansible module object
    :param vpc: Authenticated vpc connection object
    :return: Return details of created VSwitch
    """
    destination_cidrblock = module.params['destination_cidrblock']
    nexthop_type = module.params['nexthop_type']
    nexthop_id = module.params['nexthop_id']

    if not nexthop_id:
        module.fail_json(msg='nexthop_id is required for creating a route entry.')

    if not destination_cidrblock:
        module.fail_json(msg='destination_cidrblock is required for creating a route entry.')

    try:
        route_entry = vpc.create_route_entry(route_table_id=route_table_id, destination_cidrblock=destination_cidrblock,
                                             nexthop_type=nexthop_type, nexthop_id=nexthop_id)
        return True, route_entry
    except VPCResponseError as e:
        module.fail_json(msg='Unable to create route entry, error: {0}'.format(e))

    return False, None


def main():
    argument_spec = ecs_argument_spec()
    argument_spec.update(dict(
        status=dict(default='present', aliases=['state'], choices=['present', 'absent', 'list']),
        destination_cidrblock=dict(type='str', aliases=['dest_cidrblock', 'cidr_block']),
        nexthop_type=dict(default='Instance', aliases=['hop_type'], choices=['Instance', 'Tunnel', 'HaVip', 'RouterInterface']),
        nexthop_id=dict(aliases=['hop_id']),
        router_id=dict(type='str', required=True),
    ))

    module = AnsibleModule(argument_spec=argument_spec)
    vpc = vpc_connect(module)

    # Get values of variable
    status = module.params['status']
    destination_cidrblock = module.params['destination_cidrblock']
    router_id = module.params['router_id']
    nexthop_id = module.params['nexthop_id']
    route_table_id = None

    changed = False
    route_entries = []
    route_entries_basic = []
    route_entry = None

    try:
        page = 1
        pagesize = 50
        while True:
            entries = vpc.get_all_route_entries(router_id=router_id, router_type='VRouter', pagenumber=page, pagesize=pagesize)
            if entries and len(entries) > 0:
                for entry in entries:
                    route_table_id = entry.route_table_id
                    route_entries.append(entry)
                    route_entries_basic.append(get_route_entry_basic(entry))

                    if destination_cidrblock and entry.destination_cidrblock == destination_cidrblock:
                        route_entry = entry

            if not entries or len(entries) < pagesize:
                break
            page += 1

    except VPCResponseError as e:
        module.fail_json(msg='Unable to retrieve route entries, error: {0}'.format(e))

    if status == 'present':
        if route_entry:
            module.fail_json(changed=changed, msg="The specified route entry {0} has existed in route table {1}."
                             .format(destination_cidrblock, route_table_id))
        changed, route_entry = create_route_entry(module, vpc, route_table_id)
        module.exit_json(changed=changed, route_table_id=route_table_id, route_entry=get_route_entry_detail(route_entry),
                         destination_cidrblock=route_entry.destination_cidrblock)

    elif status == 'absent':
        if route_entry:
            try:
                changed = vpc.delete_route_entry(route_table_id, destination_cidrblock=destination_cidrblock, nexthop_id=nexthop_id)
            except VPCResponseError as e:
                module.fail_json(msg='Unable to delete route entry, error: {0}'.format(e))
            module.exit_json(changed=changed, route_table_id=route_table_id, destination_cidrblock=destination_cidrblock)

        module.exit_json(changed=changed, msg="Please specify a route entry by using 'destination_cidrblock',"
                                              "and expected vpcs: {0}".format(route_entries_basic))

    elif status == 'list':
        if route_entry:
            module.exit_json(changed=False, route_table_id=route_table_id, route_entries=[route_entry],
                             destination_cidrblocks=[route_entry.destination_cidrblock], total=1)

        destination_cidrblocks = []
        route_entries_detail = []
        for entry in route_entries:
            destination_cidrblocks.append(entry.destination_cidrblock)
            route_entries_detail.append(get_route_entry_detail(entry))
        module.exit_json(changed=False, route_table_id=route_table_id, route_entries=route_entries_detail,
                         destination_cidrblocks=destination_cidrblocks, total=len(route_entries))

    else:
        module.fail_json(msg='The expected state: {0}, {1} and {2}, but got {3}.'.format("present", "absent", "list", status))


if __name__ == '__main__':
    main()

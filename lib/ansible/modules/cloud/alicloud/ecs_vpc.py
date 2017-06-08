#!/usr/bin/python
#
# Copyright 2017 Alibaba Group Holding Limited.
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

ANSIBLE_METADATA = {'status': ['stableinterface'], 
                    'supported_by': 'core',
                    'version': '1.0'}
DOCUMENTATION = """
---
module: ecs_vpc
short_description: Create VPC,
common options:
  alicloud_access_key:
    description:
      - Aliyun Cloud access key. If not set then the value of the `ALICLOUD_ACCESS_KEY`, `ACS_ACCESS_KEY_ID`, 
        `ACS_ACCESS_KEY` or `ECS_ACCESS_KEY` environment variable is used.
    required: false
    default: null
    aliases: ['acs_access_key', 'ecs_access_key','access_key']
  alicloud_secret_key:
    description:
      - Aliyun Cloud secret key. If not set then the value of the `ALICLOUD_SECRET_KEY`, `ACS_SECRET_ACCESS_KEY`,
        `ACS_SECRET_KEY`, or `ECS_SECRET_KEY` environment variable is used.
    required: false
    default: null
    aliases: ['acs_secret_access_key', 'ecs_secret_key','secret_key']
  status:
    description:
      -  status for create VPC,
    choices: ['present', 'absent', 'getinfo_vroute','describe_vswitch']
    required: false
    default: present
    aliases: [ 'state' ]


function create vpc in VPC
    description: create VPC
    status: present
    options:
      cidr_block:
        description:
          - The CIDR block representing the VPC, e.g. 10.0.0.0/8. Value options: 10.0.0.0/8, 172.16.0.0/12,
           192.168.0.0/16.
        required: false
        default: 172.16.0.0/16
      vpc_name:
        description:
          - The VPC name. The default value is blank. [2, 128] English or Chinese characters, must begin with an
           uppercase/lowercase letter or Chinese character. Can contain numbers, "_" and "-". The disk description will
            appear on the console. Cannot begin with http:// or https://
        required: false
        default: null
        aliases: [ 'name' ]
      description:
        description:
          - The description. The default value is blank. [2, 256] English or Chinese characters. Cannot begin with
          http:// or https://
        required: false
        default: null
      user_cidr:
        description:
          - User custom cidr in the VPC.
        required: false
        default: null
      vswitches:
        description:
          - List of hash/dictionary of route tables to add in VPC
          - '[{"key":"value", "key":"value"}]', keys allowed:
            - cidr_block (required:true, description: It must be equal to or belong to the VPC CIDR. The subnet mask
            must be between 16 and 29. E.g., 192.168.1.0/24)
            - zone_id (required:true, description: zone_id is the desired availability zone of the subnet.)
            - vswitch_name (required:false; default: The name should be 2-128 characters. It should start with a letter
            in either the upper or lower case, or a Chinese character. It can contain digits, "_" or "-")
            - description (required:false; default: The description can be empty, or contain 2-256 characters. Cannot
             start with http:// or https://)
        required: false
        default: null
      wait:
        description: Wait for the VPC instance to be 'running' before returning.
        Choices: [yes, no, true, false]
        required: false
        default: no
      wait_timeout:
        description: how long before wait gives up, in seconds
        required: false
        default: 300


function delete vpc in VPC
    description: delete VPC
    status: absent
    options:
      vpc_id:
        description:
          - The unique ID of a VPC to delete.
        required: True
        default: null


function create vswitches in VPC
    description: create vswitches
    status: present
    options:
      vpc_id:
        description:
          - The unique ID of a VPC to delete.
        required: True
        default: null
      vswitches:
        description:
          - List of hash/dictionary of route tables to add in VPC
          - '[{"key":"value", "key":"value"}]', keys allowed:
            - cidr_block (required:true, description: It must be equal to or belong to the VPC CIDR. The subnet mask
            must be between 16 and 29. E.g., 192.168.1.0/24)
            - zone_id (required:true, description: zone_id is the desired availability zone of the subnet.)
            - vswitch_name (required:false; default: The name should be 2-128 characters. It should start with a letter
            in either the upper or lower case, or a Chinese character. It can contain digits, "_" or "-")
            - description (required:false; default: The description can be empty, or contain 2-256 characters. Cannot
             start with http:// or https://)
        required: True
        default: null
        aliases: [ 'subnets' ]


function delete vswitches in VPC
    description: delete vswitches
    status: present
    options:
      vpc_id:
        description:
          - The unique ID of a VPC to delete.
        required: True
        default: null
      purge_vswitches:
        description:
          - The List of unique ID of a VSwicth to delete from VPC
        required: True
        default: null


function create custom route in VPC
    description: create custom route
    status: present
    options:
      vpc_id:
        description:
          - The unique ID of a VPC to delete.
        required: True
        default: null
      route_entries:
        description:
          - A dictionary array of route entries to add in VPC
          - '[{"key":"value", "key":"value"}]', keys allowed:
            - destination_cidrblock (required: True; aliases: dest; description: It must be a legal CIDR or IP address,
            such as: 192.168.0.0/24 or 192.168.0.1)
            - next_hop_type (required:false, description: The next hop type. Available value options: Instance | Tunnel.
             The default value is Instance)
            - next_hop_id (required:true; default: The route entry's next hop)
        required: True
        default: null


function delete custom route in VPC
    description: delete custom route
    status: present
    options:
      vpc_id:
        description:
          - The unique ID of a VPC to delete.
        required: True
        default: null
      purge_routes:
        description:
          - A dictionary array of route tables to add in VPC
          - '[{"key":"value", "key":"value"}]', keys allowed:
            - destination_cidrblock (required: True; aliases: dest; description: It must be a legal CIDR or IP address,
            such as: 192.168.0.0/24 or 192.168.0.1)
            - route_table_id (required:True, description: The RouteEntry's RouteTableId)
            - next_hop_id (required:True; default: The route entry's next hop)
        required: false
        default: null

function querying vroute in VPC
    description: querying vroute
    status: getinfo_vroute
    options:
      vrouter_id:
        description:
          - The ID of the VRouter to be queried
        required: false
        default: null
      pagenumber:
        description:
          - Page number of the instance status list. The start value is 1. The default value is 1
        required: fasle
        default: null
      pagesize:
        description:
          - The number of lines per page set for paging query. The maximum value is 50 and default value is 10
        required: false
        default: null

function querying vswitch in VPC
    description: querying vswitch
    status: getinfo_vswitch
    options:
      vpc_id:
        description:
          - The unique ID of a VPC to delete.
        required: True
        default: null
      vswitch_id:
        description:
          - The ID of the VSwitch to be queried
        required: false
        default: null
        aliases: ['subnet']
      alicloud_zone:
        description:
          - The number of lines per page set for paging query. The maximum value is 50 and default value is 10
        required: false
        default: null
        aliases: ['zone_id', 'zone']
      pagenumber:
        description:
          - Page number of the instance status list. The start value is 1. The default value is 1
        required: fasle
        default: null
      pagesize:
        description:
          - The number of lines per page set for paging query. The maximum value is 50 and default value is 10
        required: false
        default: null

"""

EXAMPLES = """
#
# provisioning to create vpc in VPC
#

# basic provisioning example to create vpc in VPC
- name: create vpc
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-hongkong
    status: present
    cidr_block: 192.168.0.0/16
    vpc_name: Demo_VPC
    description: Demo VPC
    vswitches:
      - zone_id: 'cn-hongkong-b'
        description: 'dummy'
        cidr_block: '172.16.0.0/24'
  tasks:
    - name: create vpc
      ecs_vpc:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        status: '{{ status }}'
        cidr_block: '{{ cidr_block }}'
        vpc_name: '{{ vpc_name }}'
        description: '{{ description }}'
        vswitches: '{{ vswitches }}'
      register: result
    - debug: var=result

# basic provisioning example to delete vpc
- name: delete vpc
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-hongkong
  tasks:
    - name: delete vpc
      ecs_vpc:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        state: absent
        vpc_id: xxxxxxxxxx
      register: result
    - debug: var=result

# basic provisioning example to create vswitch
- name: create vswitch
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-hongkong
    vpc_id: xxxxxxxxxx
    vswitches:
      - zone_id: cn-hongkong-b
        cidr_block: '172.16.0.0/24'
        name: 'Demo_VSwitch'
        description: 'akashhttp://'
    state: present
  tasks:
    - name: create vswitch
      ecs_vpc:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        vswitches: '{{ vswitches }}'
        vpc_id: '{{ vpc_id }}'
        state: '{{ state }}'
      register: result
    - debug: var=result

# basic provisioning example to delete vswitch
- name: delete vswitch
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-hongkong
    vpc_id: xxxxxxxxxx
    purge_vswitches:
     - xxxxxxxxxx
    state: present
  tasks:
    - name: delete vswitch
      ecs_vpc:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        vpc_id: '{{ vpc_id }}'
        purge_vswitches: '{{ purge_vswitches }}'
        state: '{{ state }}'
      register: result
    - debug: var=result

# basic provisioning example to create custom route
- name: create vpc
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-hongkong
    state: present
    vpc_id: xxxxxxxxxx
    route_entries:
      - destination_cidrblock: '192.168.4.0/24'
        next_hop_id: 'xxxxxxxxxx'
  tasks:
    - name: create vpc
      ecs_vpc:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        state: '{{ state }}'
        route_entries: '{{ route_entries }}'
        vpc_id: '{{ vpc_id }}'
      register: result
    - debug: var=result

# basic provisioning example to delete custom route
- name: delete route
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-hongkong
    vpc_id: vpc-j6cjkmappmgb4fywpbj0u
    purge_routes:
         destination_cidrblock: "192.168.4.0/24"
         next_hop_id: "xxxxxxxxxx"
    state: present
  tasks:
    - name: delete route
      ecs_vpc:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        purge_routes: '{{ purge_routes }}'
        state: '{{ state }}'
        vpc_id: '{{ vpc_id }}'
      register: result
    - debug: var=result

# basic provisioning example to querying vroute
- name: get vrouter list
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-hongkong
    vrouter_id: xxxxxxxxxx
    pagenumber: 1
    pagesize: 10
    state: getinfo_vroute
  tasks:
    - name: get vrouter list
      ecs_vpc:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        vrouter_id: '{{ vrouter_id }}'
        state: '{{ state }}'
        pagenumber: '{{ pagenumber }}'
        pagesize: '{{ pagesize }}'
      register: result
    - debug: var=result

# basic provisioning example to querying vswitch
- name: querying vswitch status
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: ap-southeast-1
    status: getinfo_vswitch
    alicloud_zone: ap-southeast-1a
    vpc_id: xxxxxxxxxx
    vswitch_id: xxxxxxxxxx
    page_size: 10
    page_number: 1
  tasks:
    - name: querying instance status
      ecs_vpc:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        status: '{{ status }}'
        alicloud_zone: '{{ alicloud_zone }}'
        vpc_id: '{{ vpc_id }}'
        vswitch_id: '{{ vswitch_id }}'
        page_size: '{{ page_size }}'
        page_number: '{{ page_number }}'
      register: result
    - debug: var=result

"""

from footmark.exception import VPCResponseError


def create_vpc(module, vpc, cidr_block, user_cidr, vpc_name, description, vswitches):
    """
    Create Virtual Private Cloud
    module: Ansible module object
    vpc: Authenticated vpc connection object
    cidr_block: The cidr block representing the VPC, e.g. 10.0.0.0/8
    user_cidr: User custom cidr in the VPC
    vpc_name: A VPC name
    description: Description about VPC
    vswitches: List of Dictionary of Parameters for creating subnet(vswitch)
    return: Returns details of created VPC
    """
    changed = False
    if str(description).startswith('http://') or str(description).startswith('https://'):
        module.fail_json(msg='description can not start with http:// or https://')
    if str(vpc_name).startswith('http://') or str(vpc_name).startswith('https://'):
        module.fail_json(msg='vpc_name can not start with http:// or https://')
    if vswitches:
        for vswitch in vswitches:
            vswitch_description = vswitch.pop('description', None)
            if vswitch_description:
                if str(vswitch_description).startswith('http://') or \
                        str(vswitch_description).startswith('https://'):
                    module.fail_json(msg='description can not start with http:// or https://')

    try:
        changed, result = vpc.create_vpc(cidr_block=cidr_block, user_cidr=user_cidr, vpc_name=vpc_name,
                                         description=description, vswitches=vswitches)

        if 'error' in (''.join(str(result))).lower():
            module.fail_json(changed=changed, msg=result)

    except VPCResponseError as e:
        module.fail_json(msg='Unable to create vpc, error: {0}'.format(e))

    return changed, result


def delete_vpc(module, vpc, vpc_id):
    """
    Delete VPC
    :param module: Ansible module object
    :param vpc: Authenticated vpc connection object
    :param vpc_id: ID of Vpc
    :return: Returns status of operation with RequestId
    """
    changed = False
    try:
        changed, result = vpc.delete_vpc(vpc_id=vpc_id)

        if 'error' in (''.join(str(result))).lower():
            module.fail_json(changed=changed, msg=result)

    except VPCResponseError as ex:
        module.fail_json(msg='Unable to delete vpc, error: {0}'.format(ex))

    return changed, result


def get_vpc_dict(vpc):
    """
    Retrieves vpc information from an instance
    and returns it as a dictionary
    """

    return ({
        'id': vpc['VpcId'],
        'cidr_block': vpc['CidrBlock'],
        'region': vpc['RegionId'],
        'status': vpc['Status'],
        'purge_vswitches': vpc['purge_vswitches'],
        'vrouter_id': vpc['VRouterId'],
        'name': vpc['VpcName']
    })


def create_vswitch(module, vpc, vpc_id, vswitches):
    """
    Create VSwitch
    :param module: Ansible module object
    :param vpc: Authenticated vpc connection object
    :param vpc_id: ID of Vpc
    :param vswitches:
         - zone_id: Zone Id is specific zone inside region that we worked
         - cidr_block: The network address allocated to the new VSwitch
         - vswitch_name: The VSwitch name. The default value is blank. [2, 128] English or Chinese characters,
         must begin with an uppercase/lowercase letter or Chinese character. Can contain numbers, "_" and "-".
         This value will appear on the console.It cannot begin with http:// or https://.
         - description: The VSwitch description. The default value is blank. [2, 256] English or Chinese characters.
         Cannot begin with http:// or https://.
    :return: VSwitchId The system allocated VSwitchID
    """            
    if not vpc_id:
        module.fail_json(msg='vpc_id is required for creating a vswitch')

    if vswitches:
        for vswitch in vswitches:
            vswitch_description = vswitch.pop('description', None)
            if vswitch_description:
                if str(vswitch_description).startswith('http://') or \
                        str(vswitch_description).startswith('https://'):
                    module.fail_json(msg='description can not start with http:// or https://')
    else:
        module.fail_json(msg='vswitches is required for creating a vswitch')
    changed = False
    try:
        changed, result, VSwitchId = vpc.create_vswitch(vpc_id=vpc_id, vswitches=vswitches)

        if 'error' in (''.join(str(result))).lower():
            module.fail_json(changed=changed, msg=result)

    except VPCResponseError as e:
        module.fail_json(msg='Unable to Create Vswitch, error: {0}'.format(e))
    return changed, result, VSwitchId


def delete_vswitch(module, vpc, vpc_id, purge_vswitches):
    """
    Delete VSwitch
    :param module: Ansible module object
    :param vpc: Authenticated vpc connection object
    :param vpc_id: ID of Vpc
    :param purge_vswitches: The ID of the VSwitch to be deleted
    :return: Returns status of operation with RequestId
    """
    if not purge_vswitches:
        module.fail_json(msg='purge_vswitches is required for delete vswitch')
    if not vpc_id:
        module.fail_json(msg='vpc_id is required for delete vswitch')
    changed = False
    try:
        result = []
        if len(purge_vswitches) < 1:
            module.fail_json(msg='VSwitchIds is required for delete vswitch')

        changed, result = vpc.delete_vswitch(vpc_id=vpc_id, purge_vswitches=purge_vswitches)
        count = 0
        index_res = 0
        for res_items in result:
            if res_items['flag']:
                count += 1
            result[index_res].pop('flag', None)
            index_res += 1

        if count <> len(purge_vswitches):
            module.fail_json(msg=result)

        if 'error:' in (''.join(str(result))).lower():
            module.fail_json(msg=result)

    except VPCResponseError as e:
        module.fail_json(msg='Unable to delete vswitch, error: {0}'.format(e))

    return changed, result


def create_route_entry(module, vpc, route_entries, vpc_id):
    """
    Create Route Entry in VPC
    :param module: Ansible module object
    :param vpc: authenticated vpc connection object
    :param vpc_id: ID of vpc
    :param route_entries:
     - route_table_id: ID of VPC route table
     - dest: It must be a legal CIDR or IP address, such as: 192.168.0.0/24 or 192.168.0.1
     - next_hop_type: The next hop type. Available value options: Instance or Tunnel
     - next_hop_id: The route entry's next hop
    :return: Returns details of RouteEntry
    """
    if not route_entries:
        module.fail_json(msg='route_entries is required for CreateRouteEntry')
    if not vpc_id:
        module.fail_json(msg='vpc_id is required for CreateRouteEntry')
    changed = False
    try:
        changed, result = vpc.create_route_entry(route_tables=route_entries, vpc_id=vpc_id)
        if 'error' in (''.join(str(result))).lower():
            module.fail_json(changed=changed, msg=result)

    except VPCResponseError as e:
        module.fail_json(msg='Unable to create custom route entry, error: {0}'.format(e))

    return changed, result


def get_vrouter_list(module, vpc, vrouter_id, pagenumber=None, pagesize=None):
    """
    Query the Vrouters for the region
    :param module: Ansible module object
    :param vpc: Authenticated vpc connection object
    :param vrouter_id: List of VRouter_Id to be fetched
    :param pagenumber: Page number of the instance status list. The start value is 1. The default value is 1
    :param pagesize: Sets the number of lines per page for queries per page. The maximum value is 50.
    The default value is 10
    :return: List of VRouters in json format
    """
    changed = False
    result = []

    try:
        changed, result = vpc.get_all_vrouters(vrouter_id=vrouter_id, pagenumber=pagenumber, pagesize=pagesize)
        if 'error' in (''.join(str(result))).lower():
            module.fail_json(msg=result)

    except VPCResponseError as e:
        module.fail_json(msg='Unable to fetch vrouter list, error: {0}'.format(e))
    return changed, result


def process_vrouter(vrouter):
    """
    Used to process output received from get_vrouter_list
    :return:
    """
    lst = []
    for item in vrouter:
        v_router_list = {
            'vrouter_id': item.v_router_id,
            'vrouter_name': item.v_router_name,
            'description': item.description,
            'vpc_id': item.vpc_id,
            'region': item.region,
            'creation_time': item.creation_time,
            'route_table_id': item.route_table_id
        }
        lst.append(v_router_list)

    return lst


def get_vswitch_status(module, vpc, vpc_id, zone_id=None, vswitch_id=None, pagenumber=None, pagesize=None):
    """
    List VSwitches of VPC with their status
    module: Ansible module object
    vpc: authenticated vpc connection object
    vpc_id: ID of Vpc from which VSwitch belongs
    zone_id: ID of the Zone
    vswitch_id: The ID of the VSwitch to be queried
    pagenumber: Page number of the instance status list. The start value is 1. The default value is 1
    pagesize: The number of lines per page set for paging query. The maximum value is 50 and default value is 10
    :return: Returns list of VSwiches in VPC with their status
    """
    if not vpc_id:
        module.fail_json(msg='VpcId is required for querying vswitch')

    changed = False
    try:
        changed, result = vpc.get_vswitch_status(vpc_id=vpc_id, zone_id=zone_id, vswitch_id=vswitch_id,
                                                 pagenumber=pagenumber, pagesize=pagesize)
        if 'error' in (''.join(str(result))).lower():
            module.fail_json(changed=changed, msg=result)

    except VPCResponseError as e:
        module.fail_json(msg='Unable to querying vswitch list, error: {0}'.format(e))

    return changed, result


def delete_custom_route(module, vpc, purge_routes, vpc_id):
    """
    Deletes the specified RouteEntry for the vpc
    :param module: Ansible module object
    :param vpc: authenticated vpc connection object
    :param vpc_id: ID of vpc
    :param purge_routes:
        - route_table_id: Id of the route table
        - destination_cidr_block: The RouteEntry's target network segment
        - next_hop_id: The route entry's next hop
    :return: Return status of operation
    """
    if not purge_routes:
        module.fail_json(msg='purge_routes is required for deleting route entry')
    if not vpc_id:
        module.fail_json(msg='vpc_id is required for delete route entry')
    changed = False
    try:
        changed, result = vpc.delete_custom_route(purge_routes=purge_routes, vpc_id=vpc_id)

        if 'error' in (''.join(str(result))).lower():
            module.fail_json(changed=changed, msg=result)
    except VPCResponseError as e:
        module.fail_json(msg='Unable to delete custom route entry, error: {0}'.format(e))
    return changed, result


def manage_present_state(module, vpc):
    """
    Manage present state conditions
    :param module: Ansible module object
    :param vpc: authenticated vpc connection object
    :return: Returns status of operation with RequestId
    """
    cidr_block = module.params['cidr_block']
    user_cidr = module.params['user_cidr']
    vpc_name = module.params['vpc_name']
    description = module.params['description']
    route_entries = module.params['route_entries']
    purge_vswitches = module.params['purge_vswitches']
    purge_routes = module.params['purge_routes']
    vswitches = module.params['vswitches']
    vpc_id = module.params['vpc_id']
    
    if route_entries is not None:
        (changed, result) = create_route_entry(module=module, vpc=vpc, route_entries=route_entries, vpc_id=vpc_id)
        module.exit_json(changed=changed, result=result)

    elif vpc_id and purge_routes is not None:
        (changed, result) = delete_custom_route(module=module, vpc=vpc, purge_routes=purge_routes, vpc_id=vpc_id)
        module.exit_json(changed=changed, result=result)

    elif cidr_block and vpc_id is None:
        (changed, result) = create_vpc(module=module, vpc=vpc, cidr_block=cidr_block,
                                       user_cidr=user_cidr, vpc_name=vpc_name,
                                       description=description, vswitches=vswitches)
        module.exit_json(changed=changed, result=result)
    elif vpc_id and vswitches:

        (changed, result, VSwitchId) = create_vswitch(module=module, vpc=vpc, vpc_id=vpc_id, vswitches=vswitches)
        module.exit_json(changed=changed, VSwitchId=VSwitchId)
    
    elif vpc_id and purge_vswitches:
        (changed, result) = delete_vswitch(module=module, vpc=vpc, vpc_id=vpc_id, purge_vswitches=purge_vswitches)
        module.exit_json(changed=changed, result=result)

    else:
        module.fail_json(msg=[
                {'To create route entry': 'route_entries parameters are required.'},
                {' To delete custom route entry': 'vpc_id and purge_routes parameters are required.'},
                {' To create vswitch': 'vpc_id and vswitches parameters are required.'},
                {' To delete vswitch': 'vpc_id and purge_vswitches parameters are required.'}])
        

def manage_absent_state(module, vpc):
    """
    Manage absent state conditions
    :param module: Ansible module object
    :param vpc: authenticated vpc connection object
    :return: Returns status of operation with RequestId
    """
    vpc_id = module.params['vpc_id']
    if vpc_id is None:
        module.fail_json(msg='Vpc Id is required to delete the targeted VPC')

    vpc_found, vpc_result = vpc.get_vpcs(vpc_id=vpc_id)

    if vpc_found:
        changed, result = delete_vpc(module, vpc, vpc_id)
        vpc_result[0]['Status'] = 'terminated'
        module.exit_json(changed=changed, vpc=vpc_result[0], msg=result)
    else:
        module.fail_json(msg=vpc_result)


def main():
    argument_spec = ecs_argument_spec()
    argument_spec.update(dict(
        status=dict(default='present', aliases=['state'], choices=['present', 'absent', 'getinfo_vroute',
                                                                   'getinfo_vswitch']),
        cidr_block=dict(default='172.16.0.0/16', aliases=['cidr'], type="str"),
        user_cidr=dict(),
        vpc_name=dict(),
        description=dict(),
        subnet=dict(type='list'),
        route_entries=dict(type='list'),
        alicloud_zone=dict(aliases=['zone_id', 'zone', 'az']),
        vpc_id=dict(),
        vpc_ids=dict(type='list'),
        cidr=dict(),
        vswitch_name=dict(aliases=['name']),
        route_table_id=dict(),
        dest=dict(),
        next_hop_id=dict(),
        next_hop_type=dict(),
        vrouter_id=dict(type='str'),
        vswitch_id=dict(aliases=['subnet']),
        pagenumber=dict(type="int"),
        destination_cidr_block=dict(),
        pagesize=dict(type="int"),
        purge_vswitches=dict(type='list'),
        purge_routes=dict(type='dict'),
        vswitches=dict(type='list', aliases=['subnets']),
        wait=dict(type='bool', default=False),
        wait_timeout=dict(type='int', default='300')

    ))

    module = AnsibleModule(argument_spec=argument_spec)
    vpc = vpc_connect(module)
    region, acs_connect_kwargs = get_acs_connection_info(module)

    # Get values of variable
    status = module.params['status']

    if status == 'present':
        manage_present_state(module, vpc)

    elif status == 'absent':
        manage_absent_state(module, vpc)

    elif status == 'getinfo_vroute':
        vrouter_id = module.params['vrouter_id']
        pagenumber = module.params['pagenumber']
        pagesize = module.params['pagesize']

        (changed, result) = get_vrouter_list(module=module, vpc=vpc, vrouter_id=vrouter_id, pagenumber=pagenumber,
                                             pagesize=pagesize)
        module.exit_json(changed=changed, result=result)

    elif status == 'getinfo_vswitch':
        zone_id = module.params['alicloud_zone']
        vpc_id = module.params['vpc_id']
        vswitch_id = module.params['vswitch_id']
        pagenumber = module.params['pagenumber']
        pagesize = module.params['pagesize']

        (changed, result) = get_vswitch_status(module=module, vpc=vpc, vpc_id=vpc_id, zone_id=zone_id,
                                               vswitch_id=vswitch_id, pagenumber=pagenumber, pagesize=pagesize)
        module.exit_json(changed=changed, result=result)


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.alicloud_ecs import *

# import ECSConnection
main()

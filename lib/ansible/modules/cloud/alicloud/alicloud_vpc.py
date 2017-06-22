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
module: alicloud_vpc
version_added: "2.4"
short_description: Create, Query or Delete Vpc. Query Vswitch.
description:
    - Create, Query or Delete Vpc, and Query vswitch which in it.
options:
  status:
    description:
      -  Whether or not to create, delete or query VPC.
    choices: ['present', 'absent', 'fetch']
    required: false
    default: present
    aliases: [ 'state' ]
  vpc_name:
    description:
      - The name of VPC, which is a string of 2 to 128 Chinese or English characters. It must begin with an
        uppercase/lowercase letter or a Chinese character and can contain numerals, "_", or "-".
        It cannot begin with http:// or https://.
    required: false
    default: null
    aliases: [ 'name' ]
  description:
    description:
      - The description of VPC, which is a string of 2 to 256 characters. It cannot begin with http:// or https://.
    required: false
    default: null
  cidr_block:
    description:
      - The CIDR block representing the vpc. The value can be subnet block of its choices.
    required: false
    default: '172.16.0.0/12'
    choices: ['10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16']
    aliases: [ 'cidr' ]
  user_cidr:
    description:
      - User custom cidr in the VPC. Multiple cidr should be separated by comma, and no more than three.
    required: false
    default: null
  vpc_id:
    description:
      - The ID of a VPC. It required when managing an existing VPC. Such as deleting vpc and querying vpc attribute.
    required: false
    default: null
  is_default:
    description:
      - When retrieving vpc, it can mark the VPC is created by system.
    required: false
    default: null
    type: bool
  pagenumber:
    description:
      - Page number of the instance status list. The start value is 1.
    required: false
    default: 1
  pagesize:
    description:
      - The number of lines per page set for paging query. The maximum value is 50.
    required: false
    default: 10
author:
  - "He Guimin (@xiaozhu36)"

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
    alicloud_region: cn-hongkong
    status: present
    cidr_block: 192.168.0.0/16
    vpc_name: Demo_VPC
    description: Demo VPC
  tasks:
    - name: create vpc
      alicloud_vpc:
        alicloud_region: '{{ alicloud_region }}'
        status: '{{ status }}'
        cidr_block: '{{ cidr_block }}'
        vpc_name: '{{ vpc_name }}'
        description: '{{ description }}'
      register: result
    - debug: var=result

# basic provisioning example to delete vpc
- name: delete vpc
  hosts: localhost
  connection: local
  vars:
    alicloud_region: cn-hongkong
  tasks:
    - name: delete vpc
      alicloud_vpc:
        alicloud_region: '{{ alicloud_region }}'
        state: absent
        vpc_id: xxxxxxxxxx
      register: result
    - debug: var=result

"""

RETURN = '''
vpc_id:
    description: the id of vpc
    returned: on present and absent
    type: string
    sample: "vpc-2zevlzpjz2dmkj0lgxa9j"
vpc_ids:
    description: the list ids of vpcs
    returned: on fetch
    type: list
    sample: ["vpc-2zevlzpjz2dmkj0lgxa9j", "vpc-3rvlzpjz2dmkj0lgxaxe"]
vpc:
    description: Details about the ecs vpc that was created.
    returned: on present
    type: dict
    sample: {
       "cidr_block": "10.0.0.0/8",
       "creation_time": "2017-06-20T08:07:05Z",
       "description": "travis-ansible-vpc",
       "id": "vpc-2zeqndzfcsfavl93wrwsf",
       "is_default": false,
       "name": "travis-ansible-vpc",
       "region": "cn-beijing",
       "status": "Available",
       "user_cidrs": {
           "user_cidr": []
       },
       "vrouter_id": "vrt-2ze89k29g4zn7afavd6tc",
       "vswitch_ids": {
           "vswitch_id": []
       }
    }
vpcs:
    description: Details about the ecs vpcs that were created.
    returned: on fetch
    type: list
    sample: [
        {
           "cidr_block": "10.0.0.0/8",
           "creation_time": "2017-06-20T08:07:05Z",
           "description": "travis-ansible-vpc",
           "id": "vpc-2zeqndzfcsfavl93wrwsf",
           "is_default": false,
           "name": "travis-ansible-vpc",
           "region": "cn-beijing",
           "status": "Available",
           "user_cidrs": {
               "user_cidr": []
           },
           "vrouter_id": "vrt-2ze89k29g4zn7afavd6tc",
           "vswitch_ids": {
               "vswitch_id": []
           }
        },
        {
           "cidr_block": "10.0.0.0/8",
           "creation_time": "2017-06-20T08:07:05Z",
           "description": "travis-ansible-vpc",
           "id": "vpc-2zeqndzfcsfavl93wrwsf",
           "is_default": false,
           "name": "travis-ansible-vpc",
           "region": "cn-beijing",
           "status": "Available",
           "user_cidrs": {
               "user_cidr": []
           },
           "vrouter_id": "vrt-2ze89k29g4zn7afavd6tc",
           "vswitch_ids": {
               "vswitch_id": []
           }
        }
    ]
total_count:
    description: The number of all vpcs after fetching ecs vpc.
    returned: on fetch
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


def get_vpc_dict(vpc):
    """
    Format vpc result and returns it as a dictionary
    """

    return ({'id': vpc.id, 'cidr_block': vpc.cidr_block, 'region': vpc.region_id, 'status': vpc.status,
             'vswitch_ids': vpc.vswitch_ids, 'vrouter_id': vpc.vrouter_id, 'name': vpc.name, 'description': vpc.description,
             'creation_time': vpc.creation_time, 'is_default': vpc.is_default, 'user_cidrs': vpc.user_cidrs})


def create_vpc(module, vpc):
    """
    Create Virtual Private Cloud
    module: Ansible module object
    vpc: Authenticated vpc connection object
    return: Return details of created VPC
    """
    cidr_block = module.params['cidr_block']
    user_cidr = module.params['user_cidr']
    vpc_name = module.params['vpc_name']
    description = module.params['description']

    if str(description).startswith('http://') or str(description).startswith('https://'):
        module.fail_json(msg='description can not start with http:// or https://')
    if str(vpc_name).startswith('http://') or str(vpc_name).startswith('https://'):
        module.fail_json(msg='vpc_name can not start with http:// or https://')

    changed = False
    try:
        changed, vpc = vpc.create_vpc(cidr_block=cidr_block, user_cidr=user_cidr, vpc_name=vpc_name, description=description)

        return changed, get_vpc_dict(vpc)
    except VPCResponseError as e:
        module.fail_json(msg='Unable to create vpc, error: {0}'.format(e))

    return changed, None


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
        changed = vpc.delete_vpc(vpc_id=vpc_id)

    except VPCResponseError as ex:
        module.fail_json(msg='Unable to delete vpc: {0}, error: {1}'.format(vpc_id, ex))

    return changed


def retrieve_vpcs(module, vpc):
    """
    Retrieve VPC
    :param module: Ansible module object
    :param vpc: Authenticated vpc connection object
    :return: Returns a list of VPC
    """
    vpc_id = module.params['vpc_id']
    is_default = module.params['is_default']
    pagenumber = module.params['pagenumber']
    pagesize = module.params['pagesize']

    vpcs = []
    try:
        results = vpc.get_all_vpcs(vpc_id=vpc_id, is_default=is_default, pagenumber=pagenumber, pagesize=pagesize)
        for vpc in results:
            vpcs.append(get_vpc_dict(vpc))

    except VPCResponseError as e:
        module.fail_json(msg='Unable to retrieve vpc, error: {0}'.format(e))

    return vpcs


def main():
    argument_spec = ecs_argument_spec()
    argument_spec.update(dict(
        status=dict(default='present', aliases=['state'], choices=['present', 'absent', 'fetch']),
        cidr_block=dict(default='172.16.0.0/16', aliases=['cidr']),
        user_cidr=dict(),
        vpc_name=dict(aliases=['name']),
        description=dict(),
        vpc_id=dict(),
        pagenumber=dict(type='int', default='1'),
        pagesize=dict(type='int', default='10'),
        is_default=dict(type='bool'),
    ))

    module = AnsibleModule(argument_spec=argument_spec)
    vpc = vpc_connect(module)

    # Get values of variable
    status = module.params['status']

    if status == 'present':
        changed, vpc = create_vpc(module, vpc)
        module.exit_json(changed=changed, vpc_id=vpc['id'], vpc=vpc)

    elif status == 'absent':
        vpc_id = module.params['vpc_id']
        changed = delete_vpc(module, vpc, vpc_id)
        module.exit_json(changed=changed, vpc_id=vpc_id)

    elif status == 'fetch':
        vpcs = retrieve_vpcs(module=module, vpc=vpc)
        vpc_ids = []
        for vpc in vpcs:
            vpc_ids.append(vpc['id'])
        module.exit_json(changed=False, vpcs=vpcs, vpc_ids=vpc_ids, total_count=len(vpcs))

    else:
        module.fail_json(msg='The expected state: {0}, {1} and {2}, but got {3}.'.format("present", "absent", "fetch", status))


if __name__ == '__main__':
    main()

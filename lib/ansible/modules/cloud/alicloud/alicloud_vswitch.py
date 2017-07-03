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
module: alicloud_vswitch
version_added: "2.4"
short_description: Create, Query or Delete Vswitch.
description:
    - Create, Query or Delete vswitch which in the vpc.
options:
  status:
    description:
      -  Whether or not to create, delete or query vswitch.
    choices: ['present', 'absent', 'list']
    required: false
    default: present
    aliases: [ 'state' ]
  alicloud_zone:
    description:
      - Aliyun availability zone ID which to launch the vswitch or list vswitches.
        It is required when creating a vswitch.
    required: false
    default: null
    aliases: [ 'acs_zone', 'ecs_zone', 'zone_id', 'zone' ]
  vpc_id:
    description:
      - The ID of a VPC to which that Vswitch belongs. It is required when creating a vswitch.
    required: false
    default: null
  cidr_block:
    description:
      - The CIDR block representing the Vswitch e.g. 10.0.0.0/8. The value must be sub cidr_block of Vpc.
        It is required when creating a vswitch.
    required: false
    default: null
  vswitch_name:
    description:
      - The name of vswitch, which is a string of 2 to 128 Chinese or English characters. It must begin with an
        uppercase/lowercase letter or a Chinese character and can contain numerals, "_", or "-".
        It cannot begin with http:// or https://.
    required: false
    default: null
    aliases: [ 'name', 'subnet_name' ]
  description:
    description:
      - The description of vswitch, which is a string of 2 to 256 characters. It cannot begin with http:// or https://.
    required: false
    default: null
  vswitch_id:
    description:
      - VSwitch ID. It is used to manage the existing VSwitch. Such as modifying VSwitch's attribute or deleting VSwitch.
    required: false
    default: null
    aliases: [ 'subnet_id' ]
  is_default:
    description:
      - When retrieving VSwitch, it can mark the VSwitch is created by system.
    required: false
    default: null
    type: bool
author:
  - "He Guimin (@xiaozhu36)"

"""

EXAMPLES = """

# basic provisioning example to create vswitch
- name: create vswitch
  hosts: localhost
  connection: local
  vars:
    alicloud_region: cn-hongkong
    vpc_id: xxxxxxxxxx
    alicloud_zone: cn-hongkong-b
    cidr_block: '172.16.0.0/24'
    name: 'Demo_VSwitch'
    description: 'akashhttp://'
    state: present
  tasks:
    - name: create vswitch
      alicloud_vswitch:
        alicloud_region: '{{ alicloud_region }}'
        cidr_block: '{{ cidr_blok }}'
        name: '{{ name }}'
        description: '{{ description }}'
        vpc_id: '{{ vpc_id }}'
        state: '{{ state }}'
      register: result
    - debug: var=result

# basic provisioning example to delete vswitch
- name: delete vswitch
  hosts: localhost
  connection: local
  vars:
    alicloud_region: cn-hongkong
    vpc_id: xxxxxxxxxx
    vswitch_id: xxxxxxxxxx
    state: absent
  tasks:
    - name: delete vswitch
      alicloud_vswitch:
        alicloud_region: '{{ alicloud_region }}'
        vpc_id: '{{ vpc_id }}'
        vswitch_id: '{{ vswitch_id }}'
        state: '{{ state }}'
      register: result
    - debug: var=result

"""

RETURN = '''
vpc_id:
    description: the id of vpc to which vswitch belongs
    returned: on present
    type: string
    sample: "vpc-2zevlzpjz2dmkj0lgxa9j"
vpc_ids:
    description: the list ids of vpcs to which vswitches belongs
    returned: on list
    type: list
    sample: ["vpc-2zevlzpjz2dmkj0lgxa9j", "vpc-2dseevlzpjz2dmkj0lgxj"]
vswitch_id:
    description: the id of vswitch
    returned: on present and absent
    type: string
    sample: "vsw-2ze330uee6e0zono3orri"
vswitch_ids:
    description: the list ids of vswitches
    returned: on list
    type: list
    sample: [
            "vsw-2ze330uee6e0zono3orri",
            "vsw-2ze450uee6ezgweo3orer",
        ]
vswitch:
    description: Details about the ecs vswitch that was created.
    returned: on present
    type: dict
    sample: {
        "available_ip_count": 252,
        "cidr_block": "10.0.13.0/24",
        "creation_time": "2017-06-22T01:30:36Z",
        "description": "",
        "id": "vsw-2ze330uee6e0zono3orri",
        "is_default": false,
        "name": "",
        "status": "Available",
        "vpc_id": "vpc-2ze2d626c1u36gtzghyng",
        "zone_id": "cn-beijing-a"
    }
vswitches:
    description: Details about the ecs vswitches that were created or retrieved.
    returned: on list
    type: list
    sample: [
        {
            "available_ip_count": 252,
            "cidr_block": "10.0.13.0/24",
            "creation_time": "2017-06-22T01:30:36Z",
            "description": "",
            "id": "vsw-2ze330uee6e0zono3orri",
            "is_default": false,
            "name": "",
            "status": "Available",
            "vpc_id": "vpc-2ze2d626c1u36gtzghyng",
            "zone_id": "cn-beijing-a"
        },
        {
            "available_ip_count": 252,
            "cidr_block": "10.0.13.0/24",
            "creation_time": "2017-06-22T01:30:36Z",
            "description": "",
            "id": "vsw-2ze330uee6e0zono3orri",
            "is_default": false,
            "name": "",
            "status": "Available",
            "vpc_id": "vpc-2ze2d626c1u36gtzghyng",
            "zone_id": "cn-beijing-a"
        }
    ]
total:
    description: The number of all vswitches after listing ecs vswitch.
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


def get_vswitch_basic(vswitch):
    """
    Format vpc result and returns it as a dictionary
    """

    return {'id': vswitch.id, 'cidr_block': vswitch.cidr_block, 'vpc_id': vswitch.vpc_id, 'name': vswitch.name}


def get_vswitch_detail(vswitch):
    """
    Format vpc result and returns it as a dictionary
    """

    return {'id': vswitch.id, 'cidr_block': vswitch.cidr_block, 'available_ip_count': vswitch.available_ip_address_count,
            'creation_time': vswitch.creation_time, 'vpc_id': vswitch.vpc_id, 'zone_id': vswitch.zone_id,
            'status': vswitch.status, 'name': vswitch.name, 'description': vswitch.description, 'is_default': vswitch.is_default}


def create_vswitch(module, vpc):
    """
    Create VSwitch
    :param module: Ansible module object
    :param vpc: Authenticated vpc connection object
    :return: Return details of created VSwitch
    """
    zone_id = module.params['alicloud_zone']
    vpc_id = module.params['vpc_id']
    cidr_block = module.params['cidr_block']
    vsw_name = module.params['vswitch_name']
    description = module.params['description']

    if not vpc_id:
        module.fail_json(msg='vpc_id is required for creating a vswitch')

    if not zone_id:
        module.fail_json(msg='alicloud_zone is required for creating a vswitch')

    if not cidr_block:
        module.fail_json(msg='cidr_block is required for creating a vswitch')

    if str(description).startswith('http://') or str(description).startswith('https://'):
        module.fail_json(msg='description can not start with http:// or https://')

    if str(vsw_name).startswith('http://') or str(vsw_name).startswith('https://'):
        module.fail_json(msg='vswitch_name can not start with http:// or https://')

    changed = False
    try:
        changed, vswitch = vpc.create_vswitch(zone_id=zone_id, vpc_id=vpc_id, cidr_block=cidr_block,
                                              vswitch_name=None, description=None)
        return changed, vswitch
    except VPCResponseError as e:
        module.fail_json(msg='Unable to create Vswitch, error: {0}'.format(e))

    return changed, None


def main():
    argument_spec = ecs_argument_spec()
    argument_spec.update(dict(
        status=dict(default='present', aliases=['state'], choices=['present', 'absent', 'list']),
        cidr_block=dict(aliases=['cidr']),
        description=dict(),
        alicloud_zone=dict(aliases=['acs_zone', 'ecs_zone', 'zone_id', 'zone']),
        vpc_id=dict(),
        vswitch_name=dict(aliases=['name', 'subnet_name']),
        vswitch_id=dict(aliases=['subnet_id']),
        is_default=dict(type='bool'),
    ))

    module = AnsibleModule(argument_spec=argument_spec)
    vpc = vpc_connect(module)

    # Get values of variable
    status = module.params['status']
    vpc_id = module.params['vpc_id']
    vswitch_id = module.params['vswitch_id']
    vswitch_name = module.params['vswitch_name']
    cidr_block = module.params['cidr_block']
    zone_id = module.params['alicloud_zone']
    is_default = module.params['is_default']
    description = module.params['description']

    changed = False
    vswitch = None
    vswitches = []
    vswitches_basic = []
    vswitches_by_opts = []

    try:
        page = 1
        pagesize = 50
        while True:
            vswitch_list = vpc.get_all_vswitches(vpc_id=vpc_id, zone_id=zone_id, is_default=is_default, pagenumber=page, pagesize=pagesize)
            if vswitch_list is not None and len(vswitch_list) > 0:
                for curVsw in vswitch_list:
                    vswitches.append(curVsw)
                    vswitches_basic.append(get_vswitch_basic(curVsw))

                    if curVsw.id == vswitch_id:
                        vswitch = curVsw
                    elif cidr_block and curVsw.cidr_block == cidr_block:
                        vswitch = curVsw

                    if vswitch_name and description:
                        if curVsw.name == vswitch_name and curVsw.description == description:
                            vswitches_by_opts.append(curVsw)
                    elif vswitch_name and curVsw.name == vswitch_name:
                        vswitches_by_opts.append(curVsw)
                    elif description and curVsw.description == description:
                        vswitches_by_opts.append(curVsw)

            if vswitch_list is None or len(vswitch_list) < pagesize:
                break
            page += 1

    except VPCResponseError as e:
        module.fail_json(msg='Unable to retrieve vswitch, error: {0}'.format(e))

    if not vswitch and len(vswitches_by_opts) == 1:
        vswitch = vswitches_by_opts[0]

    if len(vswitches_by_opts) > 1:
        vswitches = vswitches_by_opts

    if status == 'present':
        if not vswitch:
            changed, vswitch = create_vswitch(module, vpc)
        elif vswitch_name or description:
            try:
                vswitch = vswitch.update(name=vswitch_name, description=description)
                changed = True
            except VPCResponseError as e:
                module.fail_json(msg='Unable to modify vswitch attribute, error: {0}'.format(e))

        module.exit_json(changed=changed, vpc_id=vswitch.vpc_id, vswitch=get_vswitch_detail(vswitch), vswitch_id=vswitch.id)

    elif status == 'absent':
        if vswitch:
            try:
                changed = vswitch.delete()
                module.exit_json(changed=changed, vswitch_id=vswitch.id)
            except VPCResponseError as ex:
                module.fail_json(msg='Unable to delete vswitch: {0}, error: {1}'.format(vswitch.id, ex))

        module.exit_json(changed=changed, msg="Please specify a vswitch by using 'vswitch_id', 'vswitch_name' or "
                                              "'cidr_block', and expected vpcs: %s" % vswitches_basic)

    elif status == 'list':
        vswitch_ids = []
        vpc_ids = []
        vswitches_detail = []
        if vswitch:
            module.exit_json(changed=False, vpc_ids=[vswitch.vpc_id], vswitches=[get_vswitch_detail(vswitch)], vswitch_ids=[vswitch.id], total=1)

        for vsw in vswitches:
            vswitch_ids.append(vsw.id)
            vpc_ids.append(vsw.vpc_id)
            vswitches_detail.append(get_vswitch_detail(vsw))
        module.exit_json(changed=False, vpc_id=vpc_ids, vswitches=vswitches_detail, vswitch_ids=vswitch_ids, total=len(vswitches))

    else:
        module.fail_json(msg='The expected state: {0}, {1} and {2}, but got {3}.'.format("present", "absent", "list", status))


if __name__ == '__main__':
    main()

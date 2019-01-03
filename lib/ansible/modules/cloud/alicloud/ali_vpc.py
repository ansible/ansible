#!/usr/bin/python
# Copyright (c) 2017 Alibaba Group Holding Limited. He Guimin <heguimin36@163.com.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
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

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: ali_vpc
version_added: "2.8"
short_description: Configure Alibaba Cloud virtual private cloud(VPC)
description:
    - Create, Delete Alicloud virtual private cloud(VPC).
      It supports updating VPC description.
options:
  state:
    description:
      -  Whether or not to create, delete VPC.
    choices: ['present', 'absent']
    default: 'present'
  name:
    description:
      - The name to give your VPC, which is a string of 2 to 128 Chinese or English characters. It must begin with an
        uppercase/lowercase letter or a Chinese character and can contain numerals, "_" or "-".
        It cannot begin with http:// or https://.
        This is used in combination with C(cidr_block) to determine if a VPC already exists.
    aliases: [ 'vpc_name' ]
    required: True
  description:
    description:
      - The description of VPC, which is a string of 2 to 256 characters. It cannot begin with http:// or https://.
  cidr_block:
    description:
      - The primary CIDR of the VPC. This is used in conjunction with the C(name) to ensure idempotence.
    aliases: [ 'cidr' ]
    required: True
  user_cidrs:
    description:
      - List of user custom cidr in the VPC. It no more than three.
  multi_ok:
    description:
      - By default the module will not create another VPC if there is another VPC with the same name and CIDR block.
        Specify this as true if you want duplicate VPCs created.
    default: False
    type: bool
  recent:
    description:
      - By default the module will not choose the recent one if there is another VPC with the same I(name) and
       I(cidr_block). Specify this as true if you want to target the recent VPC.
        There will be conflict when I(multi_ok=True) and I(recent=True).
    default: False
    type: bool
notes:
  - There will be launch a virtual router along with creating a vpc successfully.
  - There is only one virtual router in one vpc and one route table in one virtual router.
requirements:
    - "python >= 2.6"
    - "footmark >= 1.7.0"
extends_documentation_fragment:
    - alicloud
author:
  - "He Guimin (@xiaozhu36)"
"""

EXAMPLES = """
# Note: These examples do not set authentication details, see the Alibaba Cloud Guide for details.
- name: create a new vpc
  ali_vpc:
    cidr_block: '192.168.0.0/16'
    name: 'Demo_VPC'
    description: 'Demo VPC'

- name: choose the latest VPC as target when there are several vpcs with same name and cidr block
  ali_vpc:
    cidr_block: '192.168.0.0/16'
    name: 'Demo_VPC'
    recent: True

- name: delete a vpc
  ali_vpc:
    state: absent
    cidr_block: '192.168.0.0/16'
    name: 'Demo_VPC'
"""

RETURN = '''
vpc:
    description: info about the VPC that was created or deleted
    returned: always
    type: complex
    contains:
        cidr_block:
            description: The CIDR of the VPC
            returned: always
            type: string
            sample: 10.0.0.0/8
        creation_time:
            description: The time the VPC was created.
            returned: always
            type: string
            sample: 2018-06-24T15:14:45Z
        description:
            description: The VPC description.
            returned: always
            type: string
            sample: "my ansible vpc"
        id:
            description: alias of 'vpc_id'.
            returned: always
            type: string
            sample: vpc-c2e00da5
        is_default:
            description: indicates whether this is the default VPC
            returned: always
            type: bool
            sample: false
        state:
            description: state of the VPC
            returned: always
            type: string
            sample: available
        tags:
            description: tags attached to the VPC, includes name
            returned: always
            type: complex
            sample:
        user_cidrs:
            description: The custom CIDR of the VPC
            returned: always
            type: list
            sample: []
        vpc_id:
            description: VPC resource id
            returned: always
            type: string
            sample: vpc-c2e00da5
        vpc_name:
            description: Name of the VPC
            returned: always
            type: string
            sample: my-vpc
        vrouter_id:
            description: The ID of virtual router which in the VPC
            returned: always
            type: string
            sample: available
        vswitch_ids:
            description: List IDs of virtual switch which in the VPC
            returned: always
            type: list
            sample: [vsw-123cce3, vsw-34cet4v]
'''

import time
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.alicloud_ecs import ecs_argument_spec, vpc_connect

HAS_FOOTMARK = False

try:
    from footmark.exception import VPCResponseError
    HAS_FOOTMARK = True
except ImportError:
    HAS_FOOTMARK = False


def vpc_exists(module, vpc, name, cidr_block, multi, recent):
    """Returns None or a vpc object depending on the existence of a VPC. When supplied
    with a CIDR and Name, it will check them to determine if it is a match
    otherwise it will assume the VPC does not exist and thus return None.
    """
    if multi:
        return None
    matching_vpcs = []
    try:
        for v in vpc.describe_vpcs():
            if v.cidr_block == cidr_block and v.vpc_name == name:
                matching_vpcs.append(v)
    except Exception as e:
        module.fail_json(msg="Failed to describe VPCs: {0}".format(e))

    if len(matching_vpcs) == 1:
        return matching_vpcs[0]
    elif len(matching_vpcs) > 1:
        if recent:
            return matching_vpcs[-1]
        module.fail_json(msg='Currently there are {0} VPCs that have the same name and '
                             'CIDR block you specified. If you would like to create '
                             'the VPC anyway please pass True to the multi_ok param. '
                             'Or, please pass True to the recent param to choose the recent one.'.format(len(matching_vpcs)))
    return None


def main():
    argument_spec = ecs_argument_spec()
    argument_spec.update(dict(
        state=dict(default='present', choices=['present', 'absent']),
        cidr_block=dict(required=True, aliases=['cidr']),
        user_cidrs=dict(type='list'),
        name=dict(required=True, aliases=['vpc_name']),
        multi_ok=dict(type='bool', default=False),
        description=dict(),
        recent=dict(type='bool', default=False),
    ))

    module = AnsibleModule(argument_spec=argument_spec)

    if HAS_FOOTMARK is False:
        module.fail_json(msg='footmark required for the module ali_vpc.')

    vpc_conn = vpc_connect(module)

    # Get values of variable
    state = module.params['state']
    vpc_name = module.params['name']
    description = module.params['description']

    if str(description).startswith('http://') or str(description).startswith('https://'):
        module.fail_json(msg='description can not start with http:// or https://')
    if str(vpc_name).startswith('http://') or str(vpc_name).startswith('https://'):
        module.fail_json(msg='vpc_name can not start with http:// or https://')

    changed = False

    # Check if VPC exists
    vpc = vpc_exists(module, vpc_conn, vpc_name, module.params['cidr_block'], module.params['multi_ok'], module.params['recent'])

    if state == 'absent':
        if not vpc:
            module.exit_json(changed=changed, vpc={})

        try:
            module.exit_json(changed=vpc.delete(), vpc={})
        except VPCResponseError as ex:
            module.fail_json(msg='Unable to delete vpc {0}, error: {1}'.format(vpc.id, ex))

    if not vpc:
        params = module.params
        params['client_token'] = "Ansible-Alicloud-%s-%s" % (hash(str(module.params)), str(time.time()))
        params['vpc_name'] = vpc_name
        try:
            vpc = vpc_conn.create_vpc(**params)
            module.exit_json(changed=True, vpc=vpc.get().read())
        except VPCResponseError as e:
            module.fail_json(msg='Unable to create vpc, error: {0}'.format(e))

    if not description:
        description = vpc.description

    try:
        if vpc.modify(vpc_name, description):
            changed = True
        module.exit_json(changed=changed, vpc=vpc.get().read())
    except VPCResponseError as e:
        module.fail_json(msg='Unable to modify vpc {0}, error: {1}'.format(vpc.id, e))


if __name__ == '__main__':
    main()

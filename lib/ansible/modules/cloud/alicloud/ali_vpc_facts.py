#!/usr/bin/python
# Copyright (c) 2017 Alibaba Group Holding Limited. He Guimin <heguimin36@163.com.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
#  This file is part of Ansible
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

DOCUMENTATION = '''
---
module: ali_vpc_facts
version_added: "2.8"
short_description: Gather facts on vpcs of Alibaba Cloud.
description:
     - This module fetches data from the Open API in Alicloud.
       The module must be called from within the vpc itself.

options:
  vpc_ids:
    description:
      - A list of VPC IDs that exist in your account.
    aliases: ["ids"]
  name_prefix:
    description:
      - Use a VPC name prefix to filter VPCs.
  cidr_prefix:
    description:
      - Use a VPC cidr block prefix to filter VPCs.
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. The filter keys can be
        all of request parameters. See U(https://www.alibabacloud.com/help/doc-detail/35739.htm) for parameter details.
        Filter keys can be same as request parameter name or be lower case and use underscore ("_") or dash ("-") to
        connect different words in one parameter. 'VpcId' will be appended to I(vpc_ids) automatically.
author:
    - "He Guimin (@xiaozhu36)"
requirements:
    - "python >= 2.6"
    - "footmark >= 1.7.0"
extends_documentation_fragment:
    - alicloud
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the Alibaba Cloud Guide for details.

# Gather facts about all VPCs
- ali_vpc_facts:

# Gather facts about a particular VPC using VPC ID
- ali_vpc_facts:
    vpc_ids:
      - vpc-aaabbb
      - vpc-123fwec

# Gather facts about any VPC with 'is_default' and name_prefix
- ali_vpc_facts:
    name_prefix: "my-vpc"
    filters:
      is_default: False

# Gather facts about any VPC with cidr_prefix
- ali_vpc_facts:
    cidr_prefix: "172.16"
'''

RETURN = '''
ids:
    description: List all vpc's id after operating vpc.
    returned: when success
    type: list
    sample: [ "vpc-2zegusms7jwd94lq7ix8o", "vpc-2ze5hrb3y5ksx5oa3a0xa" ]
vpcs:
    description: Returns an array of complex objects as described below.
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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.alicloud_ecs import ecs_argument_spec, vpc_connect

HAS_FOOTMARK = False

try:
    from footmark.exception import VPCResponseError
    HAS_FOOTMARK = True
except ImportError:
    HAS_FOOTMARK = False


def main():
    argument_spec = ecs_argument_spec()
    argument_spec.update(dict(
        vpc_ids=dict(type='list', aliases=['ids']),
        name_prefix=dict(),
        cidr_prefix=dict(),
        filters=dict(type='dict')
    )
    )
    module = AnsibleModule(argument_spec=argument_spec)

    if HAS_FOOTMARK is False:
        module.fail_json(msg="Package 'footmark' required for this module.")

    filters = module.params['filters']
    if not filters:
        filters = {}

    vpc_ids = module.params['vpc_ids']
    if not vpc_ids:
        vpc_ids = []
    for key, value in filters.items():
        if key in ["VpcId", "vpc_id", "vpc-id"] and value not in vpc_ids:
            vpc_ids.append(value)

    name_prefix = module.params['name_prefix']
    cidr_prefix = module.params['cidr_prefix']

    try:
        vpcs = []
        ids = []
        while True:
            if vpc_ids:
                filters['vpc_id'] = vpc_ids[0]
                vpc_ids.pop(0)
            for vpc in vpc_connect(module).describe_vpcs(**filters):
                if name_prefix and not str(vpc.vpc_name).startswith(name_prefix):
                    continue
                if cidr_prefix and not str(vpc.cidr_block).startswith(cidr_prefix):
                    continue
                vpcs.append(vpc.read())
                ids.append(vpc.id)
            if not vpc_ids:
                break

        module.exit_json(changed=False, ids=ids, vpcs=vpcs)
    except Exception as e:
        module.fail_json(msg=str("Unable to get vpcs, error:{0}".format(e)))


if __name__ == '__main__':
    main()

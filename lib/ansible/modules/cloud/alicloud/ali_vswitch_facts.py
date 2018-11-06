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
module: ali_vswitch_facts
version_added: "2.8"
short_description: Gather facts on vswitchs of Alibaba Cloud.
description:
     - This module fetches data from the Open API in Alicloud.
       The module must be called from within the vswitch itself.

options:
  vswitch_ids:
    description:
      - A list of vswitch IDs to gather facts for.
    aliases: ['subnet_ids', 'ids']
  name_prefix:
    description:
      - Use a VSwitch name prefix to filter vswitches.
  cidr_prefix:
    description:
      - Use a VSwitch cidr block prefix to filter vswitches.
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. The filter keys can be
        all of request parameters. See U(https://www.alibabacloud.com/help/doc-detail/35748.htm) for parameter details.
        Filter keys can be same as request parameter name or be lower case and use underscores ("_") or dashes ("-") to
        connect different words in one parameter. 'VSwitchId' will be appended to I(vswitch_ids) automatically.
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

# Gather facts about all VPC vswitches
- ali_vswitch_facts:

# Gather facts about a particular VPC subnet using ID
- ali_vswitch_facts:
    vswitch_ids:
      - vsw-00112233

# Gather facts about any VPC subnet within VPC with ID vpc-abcdef00
- ali_vswitch_facts:
    filters:
      vpc-id: vpc-abcdef00

# Gather facts about a set of VPC subnets, cidrA, cidrB and cidrC within a VPC
- ali_vswitch_facts:
    cidr_prefix: "10.0."
    filters:
      vpc-id: vpc-abcdef00
'''

RETURN = '''
ids:
    description: List ids of being fetched vswtich.
    returned: when success
    type: list
    sample: [ "vsw-2zegusms7jwd94lq7ix8o", "vsw-2ze5hrb3y5ksx5oa3a0xa" ]
vswitches:
    description: Returns an array of complex objects as described below.
    returned: success
    type: complex
    contains:
        id:
            description: alias of vswitch_id
            returned: always
            type: string
            sample: vsw-b883b2c4
        cidr_block:
            description: The IPv4 CIDR of the VSwitch
            returned: always
            type: string
            sample: "10.0.0.0/16"
        availability_zone:
            description: Availability zone of the VSwitch
            returned: always
            type: string
            sample: cn-beijing-a
        state:
            description: state of the Subnet
            returned: always
            type: string
            sample: available
        is_default:
            description: indicates whether this is the default VSwitch
            returned: always
            type: bool
            sample: false
        tags:
            description: tags attached to the Subnet, includes name
            returned: always
            type: dict
            sample: {"Name": "My Subnet", "env": "staging"}
        vpc_id:
            description: the id of the VPC where this VSwitch exists
            returned: always
            type: string
            sample: vpc-67236184
        available_ip_address_count:
            description: number of available IPv4 addresses
            returned: always
            type: string
            sample: 250
        vswitch_id:
            description: VSwitch resource id
            returned: always
            type: string
            sample: vsw-b883b2c4
        subnet_id:
            description: alias of vswitch_id
            returned: always
            type: string
            sample: vsw-b883b2c4
        vswitch_name:
            description: VSwitch resource name
            returned: always
            type: string
            sample: my-vsw
        creation_time:
            description: The time the VSwitch was created.
            returned: always
            type: string
            sample: 2018-06-24T15:14:45Z
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
        name_prefix=dict(),
        cidr_prefix=dict(),
        vswitch_ids=dict(type='list', aliases=['ids', 'subnet_ids']),
        filters=dict(type='dict')
    )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if HAS_FOOTMARK is False:
        module.fail_json(msg="Package 'footmark' required for this module.")

    filters = module.params['filters']
    if not filters:
        filters = {}

    vswitch_ids = module.params['vswitch_ids']
    if not vswitch_ids:
        vswitch_ids = []
    for key, value in filters.items():
        if key in ["VSwitchId", "vswitch_id", "vswitch-id"] and value not in vswitch_ids:
            vswitch_ids.append(value)

    name_prefix = module.params['name_prefix']
    cidr_prefix = module.params['cidr_prefix']

    try:
        vswitches = []
        ids = []
        while True:
            if vswitch_ids:
                filters['vswitch_id'] = vswitch_ids[0]
                vswitch_ids.pop(0)
            for vsw in vpc_connect(module).describe_vswitches(**filters):
                if name_prefix and not str(vsw.vswitch_name).startswith(name_prefix):
                    continue
                if cidr_prefix and not str(vsw.cidr_block).startswith(cidr_prefix):
                    continue
                vswitches.append(vsw.read())
                ids.append(vsw.id)
            if not vswitch_ids:
                break

        module.exit_json(changed=False, ids=ids, vswitches=vswitches)
    except Exception as e:
        module.fail_json(msg=str("Unable to get vswitches, error:{0}".format(e)))


if __name__ == '__main__':
    main()

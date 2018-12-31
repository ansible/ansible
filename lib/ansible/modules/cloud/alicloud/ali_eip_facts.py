#!/usr/bin/python
# Copyright (c) 2017 Alibaba Group Holding Limited. He Guimin <heguimin36@163.com>
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
module: ali_eip_facts
version_added: "2.8"
short_description: Gather facts about Elastic IP addresses in Alibaba Cloud
description:
    - Gather facts about Elastic IP addresses in Alibaba Cloud
options:
  eip_ids:
    description:
      - A list of EIP IDs that exist in your account.
    aliases: ['ids']
  name_prefix:
    description:
      - Use a name prefix to filter EIPs.
  ip_address_prefix:
    description:
      - Use a ip address prefix to filter EIPs.
    aliases: ['ip_prefix']
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. The filter keys can be
        all of request parameters. See U(https://www.alibabacloud.com/help/doc-detail/36018.htm) for parameter details.
        Filter keys can be same as request parameter name or be lower case and use underscore ("_") or dashes ("-") to
        connect different words in one parameter. 'AllocationId' will be appended to I(eip_ids) automatically.
author:
    - "He Guimin (@xiaozhu36)"
requirements:
    - "python >= 2.6"
    - "footmark >= 1.9.0"
extends_documentation_fragment:
    - alicloud
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the Alibaba Cloud Guide for details.

# Gather facts about all EIPs
- ali_eip_facts:

# Gather facts about a particular EIP
- ali_eip_facts:
    eip_ids:
      - eip-xxxxxxx
      - eip-yyyyyyy
    filters:
      status: Available

# Gather facts about a particular EIP
- ali_eip_facts:
    filters:
      associated_instance_type: EcsInstance

# Gather facts based on ip_address_prefix
- ali_eip_facts:
    ip_address_prefix: 72.16
'''

RETURN = '''
eips:
    description: List of matching elastic ip addresses
    returned: always
    type: complex
    contains:
        allocation_id:
            description: The EIP id
            returned: always
            type: string
            sample: "eip-2zee1nu68juox4"
        allocation_time:
            description: The time the EIP was created
            returned: always
            type: string
            sample: "2018-12-31T12:12:52Z"
        bandwidth:
            description: Maximum bandwidth from the internet network
            returned: always
            type: int
            sample: 5
        charge_type:
            description: The eip charge type.
            returned: always
            type: string
            sample: "PostPaid"
        description:
            description: interface description
            returned: always
            type: string
            sample: "My new EIP"
        id:
            description: Allocated EIP id (alias for allocation_id)
            returned: always
            type: string
            sample: "eip-2zee1nu68juox4"
        instance_id:
            description: Associated instance id
            returned: always
            type: string
            sample: "i-123456"
        instance_region_id:
            description: The region id in which the associated instance
            returned: always
            type: string
            sample: "cn-beijing"
        instance_type:
            description: Associated instance type
            returned: always
            type: string
            sample: "EcsInstance"
        internet_charge_type:
            description: The EIP charge type.
            returned: always
            type: string
            sample: "PayByTraffic"
        ip_address:
            description: The IP address of the EIP
            returned: always
            type: string
            sample: "39.96.169.143"
        name:
            description: The EIP name
            returned: always
            type: string
            sample: "from-ansible"
        status:
            description: The EIP status
            returned: always
            type: string
            sample: "inuse"
        tags:
            description: Any tags assigned to the EIP.
            returned: always
            type: dict
            sample: {}
ids:
    description: List of elastic ip address IDs
    returned: always
    type: list
    sample: [eip-12345er, eip-3245fs]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.alicloud_ecs import ecs_argument_spec, vpc_connect

HAS_FOOTMARK = False

try:
    from footmark.exception import ECSResponseError
    HAS_FOOTMARK = True
except ImportError:
    HAS_FOOTMARK = False


def main():
    argument_spec = ecs_argument_spec()
    argument_spec.update(
        dict(
            eip_ids=dict(type='list', aliases=['ids']),
            name_prefix=dict(),
            ip_address_prefix=dict(type='str', aliases=['ip_prefix']),
            filters=dict(type='dict'),
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if HAS_FOOTMARK is False:
        module.fail_json(msg='footmark required for the module ali_eip_facts')

    eips = []
    ids = []
    eip_ids = module.params["eip_ids"]
    if not eip_ids:
        eip_ids = []
    filters = module.params["filters"]
    if not filters:
        filters = {}
    new_filters = {}
    for key, value in filters.items():
        if str(key).lower().replace("-").replace("_") == "allocationid" and value not in eip_ids:
                eip_ids.append(value)
                continue
        new_filters[key] = value

    name_prefix = module.params["name_prefix"]
    address_prefix = module.params["ip_address_prefix"]

    try:
        for eip in vpc_connect(module).describe_eip_addresses(**new_filters):
            if name_prefix and not str(eip.name).startswith(name_prefix):
                continue
            if address_prefix and not str(eip.IpAddress).startswith(address_prefix):
                continue
            if eip_ids and eip.allocation_id not in eip_ids:
                continue
            eips.append(eip.read())
            ids.append(eip.id)

        module.exit_json(changed=False, ids=ids, eips=eips)
    except Exception as e:
        module.fail_json(msg=str("Unable to get eips, error:{0}".format(e)))


if __name__ == '__main__':
    main()

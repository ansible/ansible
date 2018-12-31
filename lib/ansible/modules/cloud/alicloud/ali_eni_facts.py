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
module: ali_eni_facts
short_description: Gather facts about ENI interfaces in Alibaba Cloud
description:
    - Gather facts about ENI interfaces in Alibaba Cloud
version_added: "2.8.0"
options:
  eni_ids:
    description:
      - A list of ENI IDs that exist in your account.
    aliases: ['ids']
  name_prefix:
    description:
      - Use a name prefix to filter network interfaces.
  tags:
    description:
      - A hash/dictionaries of network interface tags. C({"key":"value"})
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. The filter keys can be
        all of request parameters. See U(https://www.alibabacloud.com/help/doc-detail/58512.htm) for parameter details.
        Filter keys can be same as request parameter name or be lower case and use underscore ("_") or dashes ("-") to
        connect different words in one parameter. 'Tag.n.Key' and 'Tag.n.Value' should be a dict and using 'tags' instead.
        'NetworkInterfaceId.N' will be appended to I(eni_ids) automatically.
author:
    - "He Guimin (@xiaozhu36)"
requirements:
    - "python >= 2.6"
    - "footmark >= 1.8.0"
extends_documentation_fragment:
    - alicloud
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the Alibaba Cloud Guide for details.

# Gather facts about all ENIs
- ali_eni_facts:

# Gather facts about a particular ENI
- ali_eni_facts:
    eni_ids:
      - eni-xxxxxxx
      - eni-yyyyyyy
    filters:
      type: Secondary

# Gather facts about a particular ENI
- ali_eni_facts:
    filters:
      network_interface_name: my-test-eni
      type: Secondary

# Gather facts based on vpc and name_prefix
- ali_eni_facts:
    name_prefix: foo
    filters:
      vswitch_id: vpc-dsfh2ef2
'''

RETURN = '''
interfaces:
    description: List of matching elastic network interfaces
    returned: always
    type: complex
    contains:
        associated_public_ip:
            description: The public IP address associated with the ENI.
            type: string
            sample: 42.1.10.1
        zone_id:
            description: The availability zone of the ENI is in.
            returned: always
            type: string
            sample: cn-beijing-a
        name:
            description: interface name
            type: string
            sample: my-eni
        creation_time:
            description: The time the eni was created.
            returned: always
            type: string
            sample: "2018-06-25T04:08Z"
        description:
            description: interface description
            type: string
            sample: My new network interface
        security_groups:
            description: list of security group ids
            type: list
            sample: [ "sg-f8a8a9da", "sg-xxxxxx" ]
        network_interface_id:
            description: network interface id
            type: string
            sample: "eni-123456"
        id:
            description: network interface id (alias for network_interface_id)
            type: string
            sample: "eni-123456"
        instance_id:
            description: Attached instance id
            type: string
            sample: "i-123456"
        mac_address:
            description: interface's physical address
            type: string
            sample: "00:00:5E:00:53:23"
        private_ip_address:
            description: primary ip address of this interface
            type: string
            sample: 10.20.30.40
        private_ip_addresses:
            description: list of all private ip addresses associated to this interface
            type: list of dictionaries
            sample: [ { "primary_address": true, "private_ip_address": "10.20.30.40" } ]
        state:
            description: network interface status
            type: string
            sample: "pending"
        vswitch_id:
            description: which vswitch the interface is bound
            type: string
            sample: vsw-b33i43f3
        vpc_id:
            description: which vpc this network interface is bound
            type: string
            sample: vpc-cj3ht4ogn
        type:
            description: type of the ENI
            type: string
            sample: Secondary
        tags:
            description: Any tags assigned to the ENI.
            returned: always
            type: dict
            sample: {}
ids:
    description: List of elastic network interface IDs
    returned: always
    type: list
    sample: [eni-12345er, eni-3245fs]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.alicloud_ecs import ecs_argument_spec, ecs_connect

HAS_FOOTMARK = False

try:
    from footmark.exception import ECSResponseError
    HAS_FOOTMARK = True
except ImportError:
    HAS_FOOTMARK = False


def main():
    argument_spec = ecs_argument_spec()
    argument_spec.update(dict(
        eni_ids=dict(type='list', aliases=['ids']),
        name_prefix=dict(),
        tags=dict(type='dict'),
        filters=dict(type='dict'),
    )
    )
    module = AnsibleModule(argument_spec=argument_spec)

    if HAS_FOOTMARK is False:
        module.fail_json(msg='footmark required for the module ali_eni_facts')

    interfaces = []
    ids = []
    filters = module.params["filters"]
    if not filters:
        filters = {}
    eni_ids = module.params["eni_ids"]
    if not eni_ids:
        eni_ids = []
    for key, value in filters.items():
        if str(key).startswith("NetworkInterfaceId") or \
                str(key).startswith("network_interface_id") or \
                str(key).startswith("network-interface-id"):
            if value not in eni_ids:
                eni_ids.append(value)
    if eni_ids:
        filters['network_interface_ids'] = eni_ids

    name_prefix = module.params["name_prefix"]
    if module.params['tags']:
        filters['tags'] = module.params['tags']

    try:
        for eni in ecs_connect(module).describe_network_interfaces(**filters):
            if name_prefix and not str(eni.name).startswith(name_prefix):
                continue
            interfaces.append(eni.read())
            ids.append(eni.id)

        module.exit_json(changed=False, ids=ids, interfaces=interfaces)
    except Exception as e:
        module.fail_json(msg=str("Unable to get network interfaces, error:{0}".format(e)))


if __name__ == '__main__':
    main()

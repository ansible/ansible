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
module: ali_slb_lb_facts
version_added: "2.8"
short_description: Gather facts on server load balancer of Alibaba Cloud.
description:
     - This module fetches data from the Open API in Alicloud.
       The module must be called from within the SLB itself.

options:
  load_balancer_ids:
    description:
      - A list of load balancer IDs to gather facts for.
    aliases: ['ids']
  name_prefix:
    description:
      - Use a load balancer name prefix to filter load balancers.
  filters:
    description:
      - A dict of filters to apply. Each dict item consists of a filter key and a filter value. The filter keys can be
        all of request parameters. See U(https://www.alibabacloud.com/help/doc-detail/27582.htm) for parameter details.
        Filter keys can be same as request parameter name or be lower case and use underscores ("_") or dashes ("-") to
        connect different words in one parameter. 'LoadBalancerId' will be appended to I(load_balancer_ids) automatically.
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
- name: Retrieving slbs using ids
  ali_slb_lb_facts:
    ids: 'lb-sn33f3'

- name: Filter slb using name_regex
  ali_slb_lb_facts:
    name_prefix: 'ansible-slb'

- name: Retrieving all slbs
  ali_slb_lb_facts:
'''

RETURN = '''
ids:
    description: List ids of being fetched slb.
    returned: when success
    type: list
    sample: ["lb-dj1oi1h5l74hg22gsnugf", "lb-dj1t1xwn0y9zcr90e52i2"]
names:
    description: List names of being fetched slb.
    returned: when success
    type: list
    sample: ["ansible-foo", "ansible-bar"]
load_balancers:
    description:
      - info about the server load balancer that was created or deleted.
    returned: on present
    type: complex
    contains:
        address:
            description: The IP address of the loal balancer
            returned: always
            type: string
            sample: "47.94.26.126"
        address_ipversion:
            description: The IP address version. IPV4 or IPV6.
            returned: always
            type: string
            sample: "ipv4"
        address_type:
            description: The load balancer internet type
            returned: always
            type: string
            sample: "internet"
        backend_servers:
            description: The load balancer's backend servers
            returned: always
            type: complex
            contains:
                server_id:
                    description: The backend server id
                    returned: always
                    type: string
                    sample: "i-vqunci342"
                weight:
                    description: The backend server weight
                    returned: always
                    type: int
                    sample: 100
                description:
                    description: The backend server description
                    returned: always
                    type: string
                    sample: ""
                type:
                    description: The backend server type, ecs or eni
                    returned: always
                    type: string
                    sample: "ecs"
        bandwidth:
            description: The load balancer internet bandwidth
            returned: always
            type: int
            sample: 5
        create_time:
            description: The time of the load balancer was created
            returned: always
            type: string
            sample: "2019-01-02T02:37:41Z"
        end_time:
            description: The time of the load balancer will be released
            returned: always
            type: string
            sample: "2999-09-08T16:00:00Z"
        id:
            description: The ID of the load balancer was created. Same as load_balancer_id.
            returned: always
            type: string
            sample: "lb-2zea9ohgtf"
        internet_charge_type:
            description: The load balancer internet charge type
            returned: always
            type: string
            sample: "PayByTraffic"
        listeners:
            description: The listeners of the load balancer.
            returned: always
            type: complex
            contains:
                listener_port:
                    description: The front-end port of the listener that is used to receive incoming traffic and
                     distribute the traffic to the backend servers.
                    returned: always
                    type: int
                    sample: 22
                listener_protocol:
                    description: The frontend protocol used by the SLB instance.
                    returned: always
                    type: string
                    sample: tcp
                listener_forward:
                    description: Whether to enable listener forwarding.
                    returned: always
                    type: string
                    sample: ""
                forward_port:
                    description: The destination listening port. It must be an existing HTTPS listening port.
                    returned: always
                    type: int
                    sample: 20
        load_balancer_id:
            description: The ID of the load balancer was created.
            returned: always
            type: string
            sample: "lb-2zea9ohgtf"
        load_balancer_name:
            description: The name of the load balancer was created.
            returned: always
            type: string
            sample: "ansible-ali_slb_lb"
        load_balancer_status:
            description: The load balancer current status.
            returned: always
            type: string
            sample: "active"
        master_zone_id:
            description: The ID of the primary zone.
            returned: always
            type: string
            sample: "cn-beijing-a"
        name:
            description: The name of the load balancer was created.
            returned: always
            type: string
            sample: "ansible-ali_slb_lb"
        network_type:
            description: The network type of the load balancer was created.
            returned: always
            type: string
            sample: "classic"
        pay_type:
            description: The load balancer instance charge type.
            returned: always
            type: string
            sample: "PostPaid"
        resource_group_id:
            description: The resource group of the load balancer belongs.
            returned: always
            type: string
            sample: "rg-acfmwvvtg5owavy"
        slave_zone_id:
            description: The ID of the backup zone
            returned: always
            type: string
            sample: "cn-beijing-d"
        tags:
            description: The load balancer tags
            returned: always
            type: complex
            sample: {}
        vpc_id:
            description: The vpc of the load balancer belongs.
            returned: always
            type: string
            sample: "vpc-fn3nc3"
        vswitch_id:
            description: The vswitch of the load balancer belongs.
            returned: always
            type: string
            sample: "vsw-c3nc3r"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.alicloud_ecs import ecs_argument_spec, slb_connect

HAS_FOOTMARK = False

try:
    from footmark.exception import SLBResponseError

    HAS_FOOTMARK = True
except ImportError:
    HAS_FOOTMARK = False


def main():
    argument_spec = ecs_argument_spec()
    argument_spec.update(dict(
        load_balancer_ids=dict(type='list', aliases=['ids']),
        name_prefix=dict(type='str'),
        filters=dict(type='dict')
    ))

    module = AnsibleModule(argument_spec=argument_spec)

    if HAS_FOOTMARK is False:
        module.fail_json(msg="Package 'footmark' required for this module.")

    lb_ids = module.params['load_balancer_ids']
    if not lb_ids:
        lb_ids = []
    name_prefix = module.params['name_prefix']
    filters = module.params['filters']
    if not filters:
        filters = {}
    for key, value in filters.items():
        if key in ["LoadBalancerId", "load-balancer-id", "load_balancer_id"] and value not in lb_ids:
            lb_ids.append(value)
    lbs = []
    ids = []
    names = []

    try:
        slb = slb_connect(module)
        if len(lb_ids) > 0:
            for index in range(0, len(lb_ids), 10):
                ids_tmp = lb_ids[index:index + 10]
                if not ids_tmp:
                    break
                filters['load_balancer_id'] = ",".join(ids_tmp)

                for lb in slb.describe_load_balancers(**filters):
                    if name_prefix and not str(lb.load_balancer_name).startswith(name_prefix):
                        continue
                    lbs.append(lb.read())
                    ids.append(lb.load_balancer_id)
                    names.append(lb.load_balancer_name)
        else:
            for lb in slb.describe_load_balancers(**filters):
                if name_prefix and not str(lb.load_balancer_name).startswith(name_prefix):
                    continue
                lbs.append(lb.read())
                ids.append(lb.load_balancer_id)
                names.append(lb.load_balancer_name)

        module.exit_json(changed=False, load_balancers=lbs, ids=ids, names=names)
    except Exception as e:
        module.fail_json(msg="Unable to describe server load balancers, and got an error: {0}.".format(e))


if __name__ == "__main__":
    main()

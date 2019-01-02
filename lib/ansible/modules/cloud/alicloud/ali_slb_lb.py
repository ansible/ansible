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

DOCUMENTATION = '''
---
module: ali_slb_lb
version_added: "2.8"
short_description: Create, Delete, Enable or Disable Server Load Balancer.
description:
  - Create, Delete, Start or Stop Server Load Balancer.
  - Modify Load Balancer internet charge type and bandwidth
options:
  state:
    description:
      - The state of the instance after operating.
    default: 'present'
    choices: [ 'present', 'absent', 'running', 'stopped']
  load_balancer_name:
    description:
      - The name of the server load balancer, which is a string of 1 to 80 characters.
        It can contain numerals, "_", "/", "." or "-".
      - This is used to ensure idempotence.
    aliases: [ 'name', 'lb_name' ]
    required: True
  is_internet:
    description:
      - Load balancer network type whether is internet.
    type: bool
    default: False
  vswitch_id:
    description:
      - The ID of the VSwitch to which the SLB instance belongs.
    aliases: ['subnet_id']
  internet_charge_type:
    description:
      - The charge type of internet. It will be ignored when C(is_internet=False)
    default: 'PayByTraffic'
    choices: ['PayByBandwidth', 'PayByTraffic']
  master_zone_id:
    description:
      - The ID of the primary zone. By default, the SLB cluster in the primary zone is used to distribute traffic.
  slave_zone_id:
    description:
        - The ID of the backup zone. The backup zone takes over the traffic distribution only when the SLB cluster in the primary zone fails.
  bandwidth:
    description:
      - Bandwidth peak of the public network instance charged per fixed bandwidth. It allow 1~5000 in Mbps.
      - It will be ignored when C(internet_charge_type=PayByTraffic)
    default: 1
  load_balancer_spec:
    description:
      - The specification of the Server Load Balancer instance. If no value is specified, a shared-performance instance is created.
      - There are some region limitations for load_balancer_spec. See U(https://www.alibabacloud.com/help/doc-detail/27577.htm) for details
    choices: ['slb.s1.small', 'slb.s2.small', 'slb.s2.medium', 'slb.s3.small', 'slb.s3.medium', 'slb.s3.large']
    aliases: [ 'spec', 'lb_spec' ]
  multi_ok:
    description:
      - By default the module will not create another Load Balancer if there is another Load Balancer
        with the same I(name). Specify this as true if you want duplicate Load Balancers created.
    default: False
    type: bool
notes:
  - The change in internet charge type will take effect from the early morning of the next day.
    It can not be changed twice in one day, otherwise, a error "Operation.NotAllowed" will appear.
requirements:
    - "python >= 2.6"
    - "footmark >= 1.9.0"
extends_documentation_fragment:
    - alicloud
author:
  - "He Guimin (@xiaozhu36)"
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the Alibaba Cloud Guide for details.
- name: create a server load balancer
  ali_slb_lb:
    name: 'from-ansible'
    is_internet: True
    internet_charge_type: 'PayByTraffic'
    spec: 'slb.s1.small'
    state: present

- name: stop a server load balancer
  ali_slb_lb:
    name: 'from-ansible'
    state: stopped

- name: start a server load balancer
  ali_slb_lb:
    name: 'from-ansible'
    state: running

- name: modify server load balancer internet charge type and bandwidth
  ali_slb_lb:
    name: 'from-ansible'
    internet_charge_type: 'PayByBandwidth'
    bandwidth: 5
'''
RETURN = '''
load_balancer:
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

import time
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
        internet_charge_type=dict(type='str', choices=['PayByBandwidth', 'PayByTraffic'], default='PayByTraffic'),
        state=dict(type='str', choices=['present', 'absent', 'running', 'stopped'], default='present'),
        load_balancer_name=dict(type='str', required=True, aliases=['name', 'lb_name']),
        is_internet=dict(type='bool', default=False),
        bandwidth=dict(type='int', default=1),
        vswitch_id=dict(type='str', aliases=['subnet_id']),
        master_zone_id=dict(),
        slave_zone_id=dict(),
        load_balancer_spec=dict(type='str', aliases=['spec', 'lb_spec'],
                                choices=['slb.s1.small', 'slb.s2.small', 'slb.s2.medium', 'slb.s3.small', 'slb.s3.medium', 'slb.s3.large']),
        multi_ok=dict(type='bool', default=False)
    ))

    module = AnsibleModule(argument_spec=argument_spec)

    if HAS_FOOTMARK is False:
        module.fail_json(msg='footmark required for the module ali_slb_lb.')

    slb = slb_connect(module)
    state = module.params['state']
    name = module.params['load_balancer_name']
    is_internet = module.params['is_internet']
    internet_charge_type = str(module.params['internet_charge_type']).lower()

    changed = False
    matching = None

    if not module.params['multi_ok']:
        try:
            matching_slbs = slb.describe_load_balancers(load_balancer_name=name)
            if len(matching_slbs) == 1:
                matching = matching_slbs[0]
            elif len(matching_slbs) > 1:
                module.fail_json(msg='Currently there are {0} Load Balancers that have the same name {1}. '
                                     'If you would like to create anyway '
                                     'please pass True to the multi_ok param.'.format(len(matching_slbs), name))
        except Exception as e:
            module.fail_json(msg="Failed to describe Load Balancers: {0}".format(e))

    if state == "absent":
        if matching:
            try:
                changed = matching.delete()
            except Exception as e:
                module.fail_json(msg="Failed to delete Load Balancers: {0}".format(e))
        module.exit_json(changed=changed, load_balancer={})

    if state == "present":
        if not matching:
            params = module.params
            params['internet_charge_type'] = internet_charge_type
            params['client_token'] = "Ansible-Alicloud-%s-%s" % (hash(str(module.params)), str(time.time()))
            address_type = "intranet"
            if is_internet:
                address_type = "internet"
            params['address_type'] = address_type
            try:
                matching = slb.create_load_balancer(**params)
                changed = True
            except Exception as e:
                module.fail_json(msg="Failed to create Load Balancer: {0}".format(e))

    if not matching:
        module.fail_json(msg="The specified load balancer {0} is not exist. Please check your name and try again.".format(name))

    if not internet_charge_type:
        internet_charge_type = str(matching.internet_charge_type).lower()

    bandwidth = module.params['bandwidth']
    if not bandwidth:
        bandwidth = matching.bandwidth
    try:
        if matching.modify_spec(internet_charge_type=internet_charge_type, bandwidth=bandwidth):
            changed = True
        matching = matching.get()
    except Exception as e:
        module.fail_json(msg="Failed to modify Load Balancer spec: {0}".format(e))

    status = "active"
    if state == "stopped":
        status = "inactive"

    try:
        if matching.set_status(status):
            changed = True
    except Exception as e:
        module.fail_json(msg="Failed to modify Load Balancer status: {0}".format(e))

    module.exit_json(changed=changed, load_balancer=matching.get().read())


if __name__ == "__main__":
    main()

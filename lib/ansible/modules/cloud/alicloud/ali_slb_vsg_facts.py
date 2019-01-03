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
module: ali_slb_vsg_facts
version_added: "2.8"
short_description: Gather facts on virtual server group of Alibaba Cloud SLB.
description:
     - This module fetches virtual server groups data from the Open API in Alibaba Cloud.
options:
  load_balancer_id:
    description:
      - ID of server load balancer.
    required: true
    aliases: ["lb_id"]
  vserver_group_ids:
    description:
      - A list of SLB vserver group ids.
    required: false
    aliases: ["group_ids", "ids"]
  name_prefix:
    description:
      - Use a vritual server group name prefix to filter vserver groups.
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
- name: Retrieving vsgs using slb id
  ali_slb_vsg_facts:
    lb_id: '{{item}}'
  with_items: '{{slbs.ids}}'

- name: Filter vsg using name_regex
  ali_slb_vsg_facts:
    name_prefix: 'ansible-foo'
    lb_id: 'lb-cn3cn34'
'''

RETURN = '''
ids:
    description: List ids of being fetched virtual server group.
    returned: when success
    type: list
    sample: ["rsp-2zehblhcv", "rsp-f22c4lhcv"]
names:
    description: List name of being fetched virtual server group.
    returned: when success
    type: list
    sample: ["ansible-1", "ansible-2"]
vserver_groups:
    description:
      - info about the virtual server group that was created or deleted.
    returned: on present
    type: complex
    contains:
        address:
            description: The IP address of the loal balancer
            returned: always
            type: string
            sample: "47.94.26.126"

        backend_servers:
            description: The load balancer's backend servers
            returned: always
            type: complex
            contains:
                port:
                    description: The backend server port
                    returned: always
                    type: int
                    sample: 22
                server_id:
                    description: The backend server id
                    returned: always
                    type: string
                    sample: "i-vqunci342"
                type:
                    description: The backend server type, ecs or eni
                    returned: always
                    type: string
                    sample: "ecs"
                weight:
                    description: The backend server weight
                    returned: always
                    type: int
                    sample: 100
        id:
            description: The ID of the virtual server group was created. Same as vserver_group_id.
            returned: always
            type: string
            sample: "rsp-2zehblhcv"
        vserver_group_id:
            description: The ID of the virtual server group was created.
            returned: always
            type: string
            sample: "rsp-2zehblhcv"
        vserver_group_name:
            description: The name of the virtual server group was created.
            returned: always
            type: string
            sample: "ansible-ali_slb_vsg"
        name:
            description: The name of the virtual server group was created.
            returned: always
            type: string
            sample: "ansible-ali_slb_vsg"
        tags:
            description: The load balancer tags
            returned: always
            type: complex
            sample: {}
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
        load_balancer_id=dict(type='str', aliases=['lb_id'], required=True),
        vserver_group_ids=dict(type='list', aliases=['group_ids', 'ids']),
        name_prefix=dict(type='str')
    ))
    module = AnsibleModule(argument_spec=argument_spec)

    if HAS_FOOTMARK is False:
        module.fail_json(msg="Package 'footmark' required for this module.")

    vsg_ids = module.params['vserver_group_ids']
    name_prefix = module.params['name_prefix']

    ids = []
    vsgs = []
    names = []

    try:
        slb = slb_connect(module)
        groups = slb.describe_vserver_groups(**{'load_balancer_id': module.params['load_balancer_id']})

        if groups:
            for group in groups:
                if vsg_ids and group.id not in vsg_ids:
                    continue
                if name_prefix and not str(group.name).startswith(name_prefix):
                    continue
                vsgs.append(group.read())
                ids.append(group.id)
                names.append(group.name)

        module.exit_json(changed=False, vserver_groups=vsgs, ids=ids, names=names)
    except Exception as e:
        module.fail_json(msg=str("Unable to describe slb vserver groups, error:{0}".format(e)))


if __name__ == '__main__':
    main()

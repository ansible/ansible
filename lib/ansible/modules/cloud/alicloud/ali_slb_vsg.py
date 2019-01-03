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
module: ali_slb_vsg
version_added: "2.8"
short_description: Create, Delete VServerGroup and Modify its name or backend servers.
description:
  - Create and delete a VServer group
  - Add or remove backend servers or network interfaces to/from the VServer group
options:
    state:
      description:
        - Create and delete a VServer group.
      default: 'present'
      choices: ['present', 'absent']
    load_balancer_id:
      description:
        - The Server Load Balancer instance ID.
          This is used in combination with C(name) to determine if a VServer group already exists.
      required: True
      aliases: ['lb_id']
    vserver_group_name:
      description:
        - Virtual server group name.
          This is used in conjunction with the C(load_balancer_id) to ensure idempotence.
      required: True
      aliases: [ 'group_name', 'name' ]
    backend_servers:
      description:
        - List of  that need to be added or.
        - List of hash/dictionaries backend servers or network interfaces to add in this group (see example).
          If none are supplied, no backend servers will be enabled. Each server has several keys and refer to
          https://www.alibabacloud.com/help/doc-detail/35215.htm. Each key should be format as under_score.
          Currently the valid keys including "server_id", "port", "weight" and "type".
    purge_backend_servers:
      description:
        - Purge existing backend servers or ENIs on VServer group that are not found in backend_servers.
        - If True, existing servers or ENIs will be purged from the resource to match exactly what is defined by
          I(backend_servers). If the I(backend_servers) is not set then servers will not be modified.
        - If True, it means you have to specify all the desired backend servers or ENIs on each task affecting a VServer group.
      default: False
      type: bool
    multi_ok:
      description:
        - By default the module will not create another Load Balancer if there is another Load Balancer
          with the same I(name). Specify this as true if you want duplicate Load Balancers created.
      default: False
      type: bool
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
- name: Create VServer Group in SLB
  ali_slb_vsg:
    load_balancer_id: 'lb-cnqnc234'
    name: 'ansible-vsg'

- name: Add backend servers to vserver group
  ali_slb_vsg:
    load_balancer_id: 'lb-cnqnc234'
    name: 'ansible-vsg'
    backend_servers:
      - instance_id: 'i-f2n3cn34c'
        port: 8080
        weight: 100
        type: ecs
      - instance_id: 'eni-n34cjf4vd'
        port: 8081
        weight: 100
        type: eni

- name: Purge backend servers from vserver group
  ali_slb_vsg:
    load_balancer_id: 'lb-cnqnc234'
    name: 'ansible-vsg'
    backend_servers:
      - instance_id: 'eni-f2n3cn34c'
        port: 8080
        weight: 100
        type: eni
      - instance_id: 'eni-n34cjf4vd'
        port: 8081
        weight: 100
        type: eni
    purge_backend_servers: True

- name: Delete VServer Group in SLB
  ali_slb_vsg:
    load_balancer_id: 'lb-cnqnc234'
    name: 'ansible-vsg'
    state: absent
'''

RETURN = '''
vserver_group:
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


VALID_SERVER_PARAMS = ["server_id", "port", "weight", "type"]


def check_backend_servers(module, servers):
    for s in servers:
        for key in s.keys():
            if key not in VALID_SERVER_PARAMS:
                module.fail_json(msg='Invalid backend server key {0}. Valid keys: {1}.'.format(key, VALID_SERVER_PARAMS))


def format_backend_servers(servers):
    backend_servers = []
    if servers:
        for s in servers:
            server = {}
            for key, value in s.items():
                split = []
                for k in str(key).split("_"):
                    split.append(str.upper(k[0]) + k[1:])
                server["".join(split)] = value
            backend_servers.append(server)
    return backend_servers


def filter_backend_servers(existing, inputting):
    old = []
    new = []
    removed = []
    existingList = []
    inputtingList = []
    oldList = []
    for s in existing:
        existingList.append(s['server_id'])

    for s in inputting:
        inputtingList.append(s['server_id'])

    for s in inputting:
        if s['server_id'] in existingList:
            old.append(s)
            oldList.append([s['server_id']])
            continue
        new.append(s)

    for s in existing:
        key = s['server_id']
        if key in inputtingList:
            if key not in oldList:
                old.append(s)
            continue
        removed.append(s)

    return old, new, removed


def main():
    argument_spec = ecs_argument_spec()
    argument_spec.update(dict(
        state=dict(type='str', default='present', choices=['present', 'absent']),
        load_balancer_id=dict(type='str', required=True, aliases=['lb_id']),
        vserver_group_name=dict(type='str', required=True, aliases=['group_name', 'name']),
        backend_servers=dict(type='list'),
        purge_backend_servers=dict(type='bool', default=False),
        multi_ok=dict(type='bool', default=False)
    ))

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=([
                               ('state', 'present', ['backend_servers'])
                           ])
                           )

    if HAS_FOOTMARK is False:
        module.fail_json(msg='footmark required for the module ali_slb_vsg.')

    slb = slb_connect(module)
    state = module.params['state']
    lb_id = module.params['load_balancer_id']
    vsg_name = module.params['vserver_group_name']

    changed = False
    matching = None

    if not module.params['multi_ok']:
        try:
            matching_vsgs = []
            for group in slb.describe_vserver_groups(**{'load_balancer_id': lb_id}):
                if group.name != vsg_name:
                    continue
                matching_vsgs.append(group)
            if len(matching_vsgs) == 1:
                matching = matching_vsgs[0]
            elif len(matching_vsgs) > 1:
                module.fail_json(msg='Currently there are {0} virtual server groups that have the same name {1}. '
                                     'If you would like to create anyway '
                                     'please pass True to the multi_ok param.'.format(len(matching_vsgs), vsg_name))
        except Exception as e:
            module.fail_json(msg=str("Unable to describe vserver group attribute, error:{0}".format(e)))

    if state == 'absent':
        if matching:
            try:
                changed = matching.delete()
            except Exception as e:
                module.fail_json(msg=str("Unable to delete vserver group, error: {0}".format(e)))
        module.exit_json(changed=changed, vserver_group={})

    backend_servers = module.params['backend_servers']
    check_backend_servers(module, backend_servers)

    if not matching:
        try:
            params = module.params
            params['backend_servers'] = format_backend_servers(backend_servers[:20])
            matching = slb.create_vserver_group(**params)
            changed = True
        except Exception as e:
            module.fail_json(msg=str("Unable to create vserver group error:{0}".format(e)))

    if backend_servers:
        old, new, removed = filter_backend_servers(matching.backend_servers['backend_server'], backend_servers)
        if old:
            try:
                if matching.modify(backend_servers=old):
                    changed = True
            except Exception as e:
                module.fail_json(msg='Modify backend servers failed: {0}'.format(e))

        if new:
            try:
                if matching.add(backend_servers=new):
                    changed = True
            except Exception as e:
                module.fail_json(msg='Add backend servers failed: {0}'.format(e))

        if module.params['purge_backend_servers'] and removed:
            try:
                if matching.remove(backend_servers=removed):
                    changed = True
            except Exception as e:
                module.fail_json(msg='Remove backend servers failed: {0}'.format(e))
    module.exit_json(changed=changed, vserver_group=matching.get().read())


if __name__ == '__main__':
    main()

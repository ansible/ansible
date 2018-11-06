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
module: ali_eni
short_description: Create and optionally attach an Elastic Network Interface (ENI) to an instance
description:
    - Create and optionally attach an Elastic Network Interface (ENI) to an instance. If an ENI ID or private ip with
      vswitch id is provided, the existing ENI (if any) will be modified.
version_added: "2.8.0"
options:
  state:
    description:
      - Create or delete ENI.
    default: 'present'
    choices: [ 'present', 'absent' ]
  eni_id:
    description:
      - The ID of the ENI (to modify); if null and state is present, a new eni will be created.
    aliases: ['id']
  instance_id:
    description:
      - Instance ID that you wish to attach ENI to.
  private_ip_address:
    description:
      - Private IP address. If null and state is present, a vacant IP address will be allocated.
    aliases: [ 'private_ip' ]
  vswitch_id:
    description:
      - ID of subnet in which to create the ENI.
    aliases: [ 'subnet_id' ]
  name:
    description:
      - Optional name of the ENI. It is a string of [2, 128] Chinese or English characters. It must begin with a letter
        and can contain numbers, underscores ("_"), colons (":"), or hyphens ("-"). It cannot begin with http:// or https://.
  description:
    description:
      - Optional description of the ENI.
  security_groups:
    description:
      - List of security group ids associated with the interface.
  attached:
    description:
      - Specifies if network interface should be attached or detached from instance. If ommited, attachment status
        won't change
    type: bool
  tags:
    description:
      - A hash/dictionaries of network interface tags. C({"key":"value"})
  purge_tags:
    description:
      - Delete existing tags on the network interface that are not specified in the task.
        If True, it means you have to specify all the desired tags on each task affecting a network interface.
    default: False
    type: bool
author:
    - "He Guimin (@xiaozhu36)"
requirements:
    - "python >= 2.6"
    - "footmark >= 1.8.0"
extends_documentation_fragment:
    - alicloud
notes:
    - This module identifies and ENI based on either the eni_id or a combination of private_ip_address and vswitch_id.
      Any of these options will let you specify a particular ENI.
    - Only name, description and security_groups can be updated.
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the Alibaba Cloud Guide for details.
# Create an ENI.
- ali_eni:
    private_ip_address: 172.31.0.20
    vswitch_id: vsw-xxxxxxxx
    security_groups:
      - sg-xxxxxx1
      - sg-xxxxxx2
    state: present
# Create an ENI and attach it to an instance
- ali_eni:
    instance_id: i-xxxxxxx
    private_ip_address: 172.31.0.20
    vswitch_id: vsw-xxxxxxxx
    security_groups:
      - sg-xxxxxx1
      - sg-xxxxxx2
    attached: True
# Update an ENI
- ali_eni:
    eni_id: eni-xxxxxxx
    name: my-eni
    description: "My new description"
# Update an ENI identifying it by private_ip_address and subnet_id
- ali_eni:
    vswitch_id: vsw-xxxxxxx
    private_ip_address: 172.16.1.1
    description: "My new description"
    security_groups:
      - sg-xxxxxx3
      - sg-xxxxxx4
# Detach an ENI from an instance
- ali_eni:
    eni_id: eni-xxxxxxx
    instance_id: i-xxxxxx
    attached: False
    state: present
# Delete an interface
# First create the interface
- ali_eni:
    vswitch_id: vsw-xxxxxxxx
    security_groups:
      - sg-xxxxxx1
      - sg-xxxxxx2
    state: present
  register: eni
- ali_eni:
    eni_id: "{{ eni.interface.id }}"
    state: absent
'''

RETURN = '''
interface:
    description: info about the elastic network interfaces that was created or deleted.
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
            sample: [{ "primary_address": true, "private_ip_address": "10.20.30.40" }]
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
'''

import time
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.alicloud_ecs import ecs_argument_spec, ecs_connect

HAS_FOOTMARK = False

try:
    from footmark.exception import ECSResponseError
    HAS_FOOTMARK = True
except ImportError:
    HAS_FOOTMARK = False


def uniquely_find_eni(connection, module):

    eni_id = module.params.get("eni_id")
    private_ip_address = module.params.get('private_ip_address')
    vswitch_id = module.params.get('vswitch_id')

    try:
        if not eni_id and not private_ip_address and not vswitch_id:
            return None

        params = {'network_interface_ids': [eni_id],
                  'primary_ip_address': private_ip_address,
                  'vswitch_id': vswitch_id
                  }
        enis = connection.describe_network_interfaces(**params)
        if enis and len(enis) == 1:
            return enis[0]
        return None

    except Exception as e:
        module.fail_json(msg=e.message)


def main():
    argument_spec = ecs_argument_spec()
    argument_spec.update(
        dict(
            eni_id=dict(type='str', aliases=['id']),
            instance_id=dict(type='str'),
            private_ip_address=dict(type='str', aliases=['private_ip']),
            vswitch_id=dict(type='str', aliases=['subnet_id']),
            description=dict(type='str'),
            name=dict(type='str'),
            security_groups=dict(type='list'),
            state=dict(default='present', choices=['present', 'absent']),
            attached=dict(default=None, type='bool'),
            tags=dict(type='dict'),
            purge_tags=dict(type='bool', default=False)
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=([
                               ('attached', True, ['instance_id'])
                           ])
                           )

    if not HAS_FOOTMARK:
        module.fail_json(msg='footmark required for this module')

    ecs = ecs_connect(module)
    state = module.params.get("state")

    eni = uniquely_find_eni(ecs, module)

    changed = False
    if state == 'absent':
        if not eni:
            module.exit_json(changed=changed, interface={})
        try:
            changed = eni.delete()
            module.exit_json(changed=changed, interface={})
        except Exception as e:
            module.fail_json(msg="{0}".format(e))

    # when state is present
    group_ids = module.params.get("security_groups")
    name = module.params.get("name")
    description = module.params.get("description")
    if not eni:
        if not group_ids:
            module.fail_json(msg="'security_groups' is required when creating a new ENI")
        vswitch_id = module.params.get("vswitch_id")
        if not vswitch_id:
            module.fail_json(msg="'vswitch_id' is required when creating a new ENI")
        try:
            params = module.params
            params['security_group_id'] = group_ids[0]
            params['primary_ip_address'] = module.params.get("private_ip_address")
            params['network_interface_name'] = module.params.get("name")
            params['client_token'] = "Ansible-Alicloud-{0}-{1}".format(hash(str(module.params)), str(time.time()))
            eni = ecs.create_network_interface(**params)
            changed = True
        except Exception as e:
            module.fail_json(msg="{0}".format(e))

    if not group_ids:
        group_ids = eni.security_group_ids["security_group_id"]
    if not name:
        name = eni.name
    if not description:
        description = eni.description
    try:
        if eni.modify(group_ids, name, description):
            changed = True
    except Exception as e:
        module.fail_json(msg="{0}".format(e))

    tags = module.params['tags']
    if module.params['purge_tags']:
        removed = {}
        if not tags:
            removed = eni.tags
        else:
            for key, value in eni.tags.items():
                if key not in tags.keys():
                    removed[key] = value
        try:
            if eni.remove_tags(removed):
                changed = True
        except Exception as e:
            module.fail_json(msg="{0}".format(e))

    if tags:
        try:
            if eni.add_tags(tags):
                changed = True
        except Exception as e:
            module.fail_json(msg="{0}".format(e))

    attached = module.params.get("attached")
    instance_id = module.params.get("instance_id")
    try:
        if attached is True:
            if not eni.instance_id:
                if eni.attach(instance_id):
                    changed = True
            elif eni.instance_id != instance_id and eni.detach(eni.instance_id) and eni.attach(instance_id):
                changed = True
        elif attached is False:
            if eni.detach(eni.instance_id):
                changed = True
    except Exception as e:
        module.fail_json(msg="{0}".format(e))

    module.exit_json(changed=changed, interface=eni.get().read())


if __name__ == '__main__':
    main()

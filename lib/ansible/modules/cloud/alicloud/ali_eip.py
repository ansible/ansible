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
module: ali_eip
version_added: "2.8"
short_description: Create eip address and bind it to a specified device.
description:
    - Create and release an elastic IP address
    - Associate/disassociate an EIP with ECS instance id or SLB instance id or Elastic Network Interface (ENI) id.
    - Set an EIP name and description
options:
  state:
    description:
      -  state for operating elastic IP address
    choices: ['present', 'absent']
    default: present
  bandwidth:
    description:
      - Maximum outgoing bandwidth to the EIP, measured in Mbps (Mega bit per second)
    default: 5
  internet_charge_type:
    description:
      - Internet charge type of ECS instance
    choices: [ 'PayByBandwidth', 'PayByTraffic']
    default: 'PayByTraffic'
  name:
    description:
      - The name of the EIP. The name can contain from 2 to 128 characters including "a-z", "A-Z", "0-9", underlines,
        and hyphens. The name must start with an English letter, but cannot start with http:// or https://.
  description:
    description:
      - The description of the EIP. The description can contain from 2 to 256 characters.
        The description must start with English letters, but cannot start with http:// or https://.
  ip_address:
    description:
      - The IP address of a previously allocated EIP and it can used to associate/disassociate with a device or delete itself.
      - If present and instance_id is specified, the EIP is associated with the instance.
      - If absent and instance_id is specified, the EIP is disassociated from the instance.
    aliases: ['ip']
  instance_id:
    description:
      - The id of the device for the EIP. Can be an ECS instance id or SLB Instance id or Elastic Network Interface (ENI) id.
    aliases: ['device_id']
  release_on_disassociation:
    description:
      - whether or not to automatically release the EIP when it is disassociated
    type: bool
    default: False
  reuse_existing_ip_allowed:
    description:
      - Reuse an EIP that is not associated to a instance (when available), instead of allocating a new one.
    type: bool
    default: False
  allow_reassociation:
    description:
      -  Specify this option to allow an Elastic IP address that is already associated with another
         ECS or SLB Instance to be re-associated with the specified instance.
    type: bool
    default: False
notes:
  - A ip address or a instance id which has been associated with EIP can ensure idempotence.
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
- name: associate an elastic IP with an instance
  ali_eip:
    instance_id: i-cqhc3hf4
- name: associate an elastic IP with a device
  ali_eip:
    instance_id: eni-snc3nh438t
- name: associate an elastic IP with a instance and allow reassociation
  ali_eip:
    instance_id: i-cqhc3hf4
    allow_reassociation: True
- name: disassociate an elastic IP from an instance
  ali_eip:
    instance_id: i-cqhc3hf4
    ip: 93.184.216.119
    state: absent
- name: disassociate an elastic IP with a device
  ali_eip:
    instance_id: eni-snc3nh438t
    ip: 93.184.216.119
    state: absent
- name: allocate a new elastic IP and associate it with an instance
  ali_eip:
    instance_id: i-1212f003
- name: allocate a new elastic IP without associating it to anything and set name and description
  ali_eip:
    name: created-by-ansible
    description: "form ansible"
  register: eip
- name: output the IP
  debug:
    msg: "Allocated IP is {{ eip.public_ip }}"
'''

RETURN = '''
eip:
    description: info about the elastic IP address that was created or deleted.
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


def find_eip(conn, module, ip_address, instance_id):
    try:
        eips = conn.describe_eip_addresses()
        for e in eips:
            if instance_id and e.instance_id == instance_id:
                return e, eips
            if ip_address and e.ip_address == ip_address:
                return e, eips
        return None, eips
    except Exception as e:
        module.fail_json(msg="Failed to describe EIPs: {0}".format(e))


def unassociate_eip(eip, module, instance_id):
    try:
        if eip.get().unassociate(instance_id=instance_id):
            return True
    except Exception as e:
        module.fail_json(msg="Disassociate EIP with instance {0} failed. Error: {1}".format(instance_id, e))
    return False


def main():
    argument_spec = ecs_argument_spec()
    argument_spec.update(
        dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            ip_address=dict(type='str', aliases=['ip']),
            instance_id=dict(type='str', aliases=['device_id']),
            internet_charge_type=dict(type='str', default='PayByTraffic', choices=['PayByTraffic', 'PayByBandwidth']),
            bandwidth=dict(type='int', default=5),
            reuse_existing_ip_allowed=dict(type='bool', default=False),
            release_on_disassociation=dict(type='bool', default=False),
            allow_reassociation=dict(type='bool', default=False),
            name=dict(type='str'),
            description=dict(type='str')
        )
    )

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_FOOTMARK:
        module.fail_json(msg='footmark is required for the module ali_eip.')

    vpc = vpc_connect(module)

    # set values
    state = module.params['state']
    instance_id = module.params['instance_id']
    ip_address = module.params['ip_address']

    eip, eips = find_eip(vpc, module, ip_address, instance_id)
    changed = False

    if state == 'absent':
        if not eip:
            module.exit_json(changed=changed, eip={})

        if ip_address and instance_id and eip.ip_address != ip_address:
            module.exit_json(changed=changed, eip=eip.get.read())

        release = module.params['release_on_disassociation']
        if instance_id:
            try:
                if unassociate_eip(eip, module, instance_id):
                    changed = True
                if not release:
                    module.exit_json(changed=changed, eip=eip.get().read())
            except Exception as e:
                module.fail_json(msg="Disassociate EIP with instance {0} failed. Error: {1}".format(instance_id, e))
        else:
            release = True

        if release:
            try:
                changed = eip.release()
                module.exit_json(changed=changed, eip={})
            except Exception as e:
                module.fail_json(msg="{0}".format(e))

    # state == present
    if not eip:
        if module.params['reuse_existing_ip_allowed'] and len(eips) > 0:
            for e in eips:
                if str(e.status).lower() == "available":
                    eip = e
                    break
    if not eip:
        try:
            params = module.params
            params['client_token'] = "Ansible-Alicloud-%s-%s" % (hash(str(module.params)), str(time.time()))
            eip = vpc.allocate_eip_address(**params)
            changed = True
        except VPCResponseError as e:
            module.fail_json(msg='Unable to allocate an eip address, error: {0}'.format(e))

    # Modify EIP attribute
    name = module.params['name']
    description = module.params['description']
    bandwidth = module.params['bandwidth']
    if not name:
        name = eip.name
    if not description:
        description = eip.description
    if not bandwidth:
        bandwidth = eip.bandwidth

    try:
        if eip.modify(bandwidth, name, description):
            changed = True
    except VPCResponseError as e:
        module.fail_json(msg='Modify EIP attribute with an error {0}.'.format(e))

    # Associate instance
    if instance_id:
        if eip.instance_id and eip.instance_id != instance_id:
            if not module.params['allow_reassociation']:
                module.fail_json(msg='Target EIP {0} has been associated. Please set allow_reassociation to ture to '
                                     'associate the target instance {1}'. format(eip.ip_address, instance_id))
            try:
                if unassociate_eip(eip, module, instance_id):
                    changed = True
            except Exception as e:
                module.fail_json(msg="Unassociate EIP from instance {0} failed. Error: {1}".format(instance_id, e))
        try:
            if eip.get().associate(instance_id=instance_id):
                changed = True
        except Exception as e:
            module.fail_json(msg="Associate EIP with instance {0} failed. Error: {1}".format(instance_id, e))
    module.exit_json(changed=changed, eip=eip.get().read())


if __name__ == "__main__":
    main()

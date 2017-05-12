#!/usr/bin/python
#
# Copyright 2017 Alibaba Group Holding Limited.
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

ANSIBLE_METADATA = {'status': ['stableinterface'],
                    'supported_by': 'core',
                    'version': '1.0'}
DOCUMENTATION = """
---
module: ecs_eip
short_description: Requesting eip address, bind eip, unbind eip, modify eip attributes and release eip
common options:
  alicloud_access_key:
    description:
      - Aliyun Cloud access key. If not set then the value of the `ALICLOUD_ACCESS_KEY`, `ACS_ACCESS_KEY_ID`, 
        `ACS_ACCESS_KEY` or `ECS_ACCESS_KEY` environment variable is used.
    required: false
    default: null
    aliases: ['acs_access_key', 'ecs_access_key','access_key']
  alicloud_secret_key:
    description:
      - Aliyun Cloud secret key. If not set then the value of the `ALICLOUD_SECRET_KEY`, `ACS_SECRET_ACCESS_KEY`,
        `ACS_SECRET_KEY`, or `ECS_SECRET_KEY` environment variable is used.
    required: false
    default: null
    aliases: ['acs_secret_access_key', 'ecs_secret_key','secret_key']
  status:
    description:
      -  status for requesting eip addresses, bind eip, unbind eip, modify eip attributes and release eip
    choices: ['present', 'join', 'absent', 'leave']
    required: false
    default: present
    aliases: [ 'state' ]

function requesting eip addresses in EIP
    description: Requesting eip addresses
    status: present
    options:
      bandwidth:
        description:
          - The rate limit of the EIP.
        required: false
        default: 5Mbps
      internet_charge_type:
        description:
          - PayByBandwidth and PayByTraffic.
        required: false
        default: PayByBandwidth

function bind eip in EIP
    description: Bind eip addresses
    status: join
    options:
      allocation_id:
        description:
          - The allocation ID of the EIP to be bound. The allocation ID uniquely identifies the EIP
        required: True
        default: null
      instance_id:
        description:
          - The ID of the ECS instance to be bound
        required: True
        default: null

function unbind eip in EIP
    description: Unbind eip addresses
    status: leave
    options:
      allocation_id:
        description:
          - The allocation ID of the EIP to be unbound. The allocation ID uniquely identifies the EIP.
        required: True
        default: null
      instance_id:
        description:
          - The ID of the ECS instance to be unbound
        required: True
        default: null

function modifying eip attributes in EIP
    description: Modifying eip attributes
    status: present
    options:
      allocation_id:
        description:
          - The allocation ID of the EIP to be bound. The allocation ID uniquely identifies the EIP.
        required: True
        default: null
      bandwidth:
        description:
          - The rate limit of the EIP. If not specified.
        required: True
        default: 5Mbps

function modifying eip attributes in EIP
    description: Modifying eip attributes
    status: absent
    options:
      allocation_id:
        description:
          - The allocation ID of the EIP to be remove. The allocation ID uniquely identifies the EIP.
        required: True
        default: null

"""

EXAMPLES = """
#
# provisioning to requesting eip addresses in EIP
#

# basic provisioning example to requesting eip addresses in EIP
- name: requesting eip
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-hongkong
    internet_charge_type: PayByTraffic
    bandwidth: 5
    status: present
  tasks:
    - name: requesting eip
      ecs_eip:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        internet_charge_type: '{{ internet_charge_type }}'
        bandwidth: '{{ bandwidth }}'
        status: '{{ status }}'
      register: result

    - debug: var=result


# basic provisioning example to bind eip
- name: create disk
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-hongkong
    allocation_id: xxxxxxxxxx
    instance_id: xxxxxxxxxx
    status: join
  tasks:
    - name: Bind eip
      ecs_eip:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        allocation_id: '{{ allocation_id }}'
        instance_id: '{{ instance_id }}'
        status: '{{ status }}'
      register: result

    - debug: var=result


# basic provisioning example to unbind eip
- name: unbind eip
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-hongkong
    allocation_id: exxxxxxxxxx
    instance_id: xxxxxxxxxx
    state: leave
  tasks:
    - name: unbind eip
      ecs_eip:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        allocation_id: '{{ allocation_id }}'
        instance_id: '{{ instance_id }}'
        state: '{{ state }}'
      register: result

    - debug: var=result


# basic provisioning example to modifying eip
- name: modifying eip
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-hongkong
    allocation_id: xxxxxxxxxx
    bandwidth: 3
    status: present
  tasks:
    - name: Modify eip
      ecs_eip:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        allocation_id: '{{ allocation_id }}'
        bandwidth: '{{ bandwidth }}'
        status: '{{ status }}'
      register: result

    - debug: var=result


# basic provisioning example to release eip
- name: release eip
  hosts: localhost
  connection: local
  vars:
    alicloud_access_key: xxxxxxxxxx
    alicloud_secret_key: xxxxxxxxxx
    alicloud_region: cn-hongkong
    allocation_id: xxxxxxxxxx
    status: absent
  tasks:
    - name: release eip
      ecs_eip:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        allocation_id: '{{ allocation_id }}'
        status: '{{ status }}'
      register: result

    - debug: var=result

"""

from footmark.exception import VPCResponseError


def requesting_eip_addresses(module, vpc, bandwidth, internet_charge_type):
    """
    requesting for eip address
    :param module: Ansible module object
    :param vpc: authenticated vpc connection object
    :param bandwidth: The rate limit of the EIP. If not specified, it is 5Mbps by default
    :param internet_charge_type: PayByBandwidth and PayByTraffic. The default value is PayByBandwidth.
    :return: a dictionary contains AllocationId, EipAddress and RequestId
    """
    changed = False
    try:
        changed, result = vpc.requesting_eip_addresses(bandwidth=bandwidth, internet_charge_type=internet_charge_type)
        if 'error' in (''.join(str(result))).lower():
            module.fail_json(msg=result)

    except VPCResponseError as e:
        module.fail_json(msg='Unable to request eip address, error: {0}'.format(e))
    return changed, result


def bind_eip(module, vpc, allocation_id, instance_id):
    """
    Bind eip address
    :param module: Ansible module object
    :param vpc: authenticated vpc connection object
    :param allocation_id: The allocation ID of the EIP to be bound. The allocation ID uniquely identifies the EIP.
    :param instance_id: The ID of the ECS instance to be bound
    :return: a dictionary of information
    """
    if not allocation_id:
        module.fail_json(msg="allocation_id parameter is needed to bind eip")
    if not instance_id:
        module.fail_json(msg="instance_id parameter is needed to bind eip")

    changed = False

    verify_eip_region(module, vpc, allocation_id)

    try:
        result = vpc.bind_eip(allocation_id=allocation_id, instance_id=instance_id)

        if 'error' in (''.join(str(result))).lower():
            module.fail_json(msg=result)
        changed = True

    except VPCResponseError as e:
        module.fail_json(msg='Unable to bind eip, error: {0}'.format(e))

    return changed, result


def unbind_eip(module, vpc, allocation_id, instance_id):
    """
    Unbind eip address
    :param module: Ansible module object
    :param vpc: authenticated vpc connection object
    :param allocation_id: The allocation ID of the EIP to be unbound. The allocation ID uniquely identifies the EIP.
    :param instance_id: The ID of the ECS instance to be unbound
    :return: a dictionary of information
    """
    if not allocation_id:
        module.fail_json(msg="allocation_id parameter is needed to unbind eip")
    if not instance_id:
        module.fail_json(msg="instance_id parameter is needed to unbind eip")

    changed = False

    verify_eip_region(module, vpc, allocation_id)

    try:
        changed, result = vpc.unbind_eip(allocation_id=allocation_id, instance_id=instance_id)
        if 'error' in (''.join(str(result))).lower():
            module.fail_json(changed=changed, msg=result)

    except VPCResponseError as e:
        module.fail_json(msg='Unable to Unbind eip, error: {0}'.format(e))
    return changed, result


def modifying_eip_attributes(module, vpc, allocation_id, bandwidth):
    """
    Modify eip attributes
    :param module: Ansible module object
    :param vpc: authenticated vpc connection object
    :param allocation_id: The allocation ID of the EIP to be bound. The allocation ID uniquely identifies the EIP.
    :param bandwidth: The rate limit of the EIP
    :return: a dictionary of information
    """
    if not allocation_id:
        module.fail_json(msg="allocation_id parameter is needed to modify eip")
    if not bandwidth:
        module.fail_json(msg="bandwidth parameter is needed to modify eip")

    changed = False

    verify_eip_region(module, vpc, allocation_id)

    try:
        changed, result = vpc.modifying_eip_attributes(allocation_id=allocation_id, bandwidth=bandwidth)
        if 'error' in (''.join(str(result))).lower():
            module.fail_json(msg=result)

    except VPCResponseError as e:
        module.fail_json(msg='Unable to modify eip attributes, error: {0}'.format(e))
    return changed, result


def release_eip(module, vpc, allocation_id):
    """
    Release eip addresses
    :param module: Ansible module object
    :param vpc: authenticated vpc connection object
    :param allocation_id: The allocation ID of the EIP to be remove. The allocation ID uniquely identifies the EIP.
    :return: a dictionary of information
    """
    if not allocation_id:
        module.fail_json(msg="allocation_id parameter is needed to release eip")

    changed = False

    verify_eip_region(module, vpc, allocation_id)

    try:
        result = vpc.releasing_eip(allocation_id=allocation_id)

        if 'error' in (''.join(str(result))).lower():
            module.fail_json(msg=result)
        changed = True

    except VPCResponseError as e:
        module.fail_json(msg='Unable to release eip, error: {0}'.format(e))

    return changed, result

def verify_eip_region(module, vpc, allocation_id):
    """
    Verify if eip belongs to the provided region
    :param module: Ansible module object
    :param vpc: authenticated vpc connection object
    :param allocation_id: The allocation ID of the EIP to be remove. The allocation ID uniquely identifies the EIP.
    :return:
    """
    if allocation_id is None:
        module.fail_json("allocation_id is mandatory to verify eip region")

    try:
        eips, result = vpc.describe_eip_address(allocation_id=allocation_id)

        if eips is None:
            module.fail_json(msg=result)

        if len(eips) != 1:
            module.fail_json(msg="eip with allocation_id " + allocation_id + " does not exist in the provided region")

    except VPCResponseError as e:
        module.fail_json(msg='Unable to verify eip, error: {0}'.format(e))


def main():
    argument_spec = ecs_argument_spec()
    argument_spec.update(dict(
        status=dict(default='present', aliases=['state'], choices=['present', 'join', 'absent', 'leave']),
        allocation_id=dict(type='str'),
        instance_id=dict(type='str'),
        internet_charge_type=dict(default='PayByBandwidth', choices=['PayByTraffic', 'PayByBandwidth']),
        bandwidth=dict(type='str')

    ))

    module = AnsibleModule(argument_spec=argument_spec)
    vpc = vpc_connect(module)
    region, acs_connect_kwargs = get_acs_connection_info(module)

    # set values
    status = module.params['status']
    instance_id = module.params['instance_id']
    internet_charge_type = module.params['internet_charge_type']
    allocation_id = module.params['allocation_id']
    bandwidth = module.params['bandwidth']

    if status == 'present':

        if bandwidth is not None:
            try:
                int(bandwidth)
            except Exception as ex:
                module.fail_json(msg="provide valid bandwidth value")

        if (allocation_id and bandwidth) is not None:

            (changed, result) = modifying_eip_attributes(module=module, vpc=vpc, allocation_id=allocation_id,
                                                         bandwidth=bandwidth)
            module.exit_json(changed=changed, result=result)

        else:
            (changed, result) = requesting_eip_addresses(module=module, vpc=vpc,
                                                         bandwidth=bandwidth, internet_charge_type=internet_charge_type)
            module.exit_json(changed=changed, result=result)

    elif status == 'join':

        (changed, result) = bind_eip(module=module, vpc=vpc, allocation_id=allocation_id, instance_id=instance_id)
        module.exit_json(changed=changed, result=result)

    elif status == 'absent':

        (changed, result) = release_eip(module, vpc, allocation_id=allocation_id)
        module.exit_json(changed=changed, result=result)

    elif status == 'leave':

        (changed, result) = unbind_eip(module=module, vpc=vpc, allocation_id=allocation_id, instance_id=instance_id)
        module.exit_json(changed=changed, result=result)


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.alicloud_ecs import *

# import ECSConnection
main()

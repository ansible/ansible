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
module: alicloud_instance_facts
version_added: "2.5"
short_description: Gather facts on instances of Alibaba Cloud ECS.
description:
     - This module fetches data from the Open API in Alicloud.
       The module must be called from within the ECS instance itself.

options:
    alicloud_zone:
      description:
        - Aliyun availability zone ID in which to launch the instance
      aliases: [ 'zone_id', 'zone' ]
    instance_names:
      description:
        - A list of ECS instance names.
      aliases: [ "names"]
    instance_ids:
      description:
        - A list of ECS instance ids.
      aliases: ["ids"]
    instance_tags:
      description:
        - A hash/dictionaries of instance tags. C({"key":"value"})
      aliases: ["tags"]
author:
    - "He Guimin (@xiaozhu36)"
requirements:
    - "python >= 2.6"
    - "footmark >= 1.1.16"
extends_documentation_fragment:
    - alicloud
'''

EXAMPLES = '''
# Fetch instances details according to setting different filters
- name: fetch instances details example
  hosts: localhost
  vars:
    alicloud_access_key: <your-alicloud-access-key>
    alicloud_secret_key: <your-alicloud-secret-key>
    alicloud_region: cn-beijing
    alicloud_zone: cn-beijing-a

  tasks:
    - name: Find all instances in the specified region
      alicloud_instance_facts:
      register: all_instances
    - name: Find all instances based on the specified ids
      alicloud_instance_facts:
        instance_ids:
          - "i-35b333d9"
          - "i-ddav43kd"
      register: instances_by_ids
    - name: Find all instances based on the specified names/name-prefixes
      alicloud_instance_facts:
        instance_names:
          - "ecs_instance-1"
          - "ecs_instance_2"
      register: instances_by_ids

'''

RETURN = '''
instance_ids:
    description: List all instances's id after operating ecs instance.
    returned: when success
    type: list
    sample: ["i-2ze9zfjdhtasdrfbgay1"]
instances:
    description: Details about the ecs instances that were created.
    returned: when success
    type: list
    sample: [{
        "block_device_mapping": {
            "d-2ze9mho1vp79mctdoro0": {
                "delete_on_termination": true,
                "status": "in_use",
                "volume_id": "d-2ze9mho1vp79mctdoro0"
            }
        },
        "eip": {
            "allocation_id": "",
            "internet_charge_type": "",
            "ip_address": ""
        },
        "group_ids": {
            "security_group_id": [
                "sg-2zegcq33l0yz9sknp08o"
            ]
        },
        "host_name": "myhost",
        "id": "i-2ze9zfjdhtasdrfbgay1",
        "image_id": "ubuntu1404_64_40G_cloudinit_20160727.raw",
        "instance_name": "test-instance",
        "instance_type": "ecs.n1.small",
        "io_optimized": true,
        "key_name": "test",
        "launch_time": "2017-05-23T00:56Z",
        "private_ip": "10.31.153.209",
        "public_ip": "47.94.45.175",
        "region_id": "cn-beijing",
        "status": "running",
        "tags": {
            "create_test": "0.01"
        },
        "vpc_attributes": {
            "nat_ip_address": "",
            "private_ip_address": {
                "ip_address": []
            },
            "vpc_id": "",
            "vswitch_id": ""
        },
        "zone_id": "cn-beijing-a"
    }]
total:
    description: The number of all instances after operating ecs instance.
    returned: when success
    type: int
    sample: 1
'''

# import time
# import sys
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.alicloud_ecs import get_acs_connection_info, ecs_argument_spec, ecs_connect

HAS_FOOTMARK = False

try:
    from footmark.exception import ECSResponseError
    HAS_FOOTMARK = True
except ImportError:
    HAS_FOOTMARK = False


def get_instance_info(inst):
    """
    Retrieves instance information from an instance
    ID and returns it as a dictionary
    """
    instance_info = {'id': inst.id,
                     'private_ip': inst.inner_ip_address,
                     'public_ip': inst.public_ip_address,
                     'image_id': inst.image_id,
                     'zone_id': inst.zone_id,
                     'region_id': inst.region_id,
                     'launch_time': inst.creation_time,
                     'instance_type': inst.instance_type,
                     'instance_name': inst.instance_name,
                     'host_name': inst.host_name,
                     'group_ids': inst.security_group_ids,
                     'status': inst.status,
                     'tags': inst.tags,
                     'vpc_attributes': inst.vpc_attributes,
                     'eip': inst.eip_address,
                     'io_optimized': inst.io_optimized,
                     'key_name': inst.key_name
                     }
    try:
        bdm_dict = {}
        bdm = getattr(inst, 'block_device_mapping')
        for device_name in bdm.keys():
            bdm_dict[device_name] = {
                'status': bdm[device_name].status,
                'volume_id': bdm[device_name].volume_id,
                'delete_on_termination': bdm[device_name].delete_on_termination
            }
        instance_info['block_device_mapping'] = bdm_dict
    except AttributeError:
        instance_info['block_device_mapping'] = False

    return instance_info


def main():
    argument_spec = ecs_argument_spec()
    argument_spec.update(dict(
        alicloud_zone=dict(aliases=['zone_id', 'zone']),
        instance_ids=dict(type='list', aliases=['ids']),
        instance_names=dict(type='list', aliases=['names']),
        instance_tags=dict(type='list', aliases=['tags']),
    )
    )
    module = AnsibleModule(argument_spec=argument_spec)

    if HAS_FOOTMARK is False:
        module.fail_json(msg='footmark required for the module alicloud_instance_facts')

    ecs = ecs_connect(module)

    instances = []
    instance_ids = []
    ids = module.params['instance_ids']
    names = module.params['instance_names']
    zone_id = module.params['alicloud_zone']
    if ids and (not isinstance(ids, list) or len(ids)) < 1:
        module.fail_json(msg='instance_ids should be a list of instances, aborting')

    if names and (not isinstance(names, list) or len(names)) < 1:
        module.fail_json(msg='instance_ids should be a list of instances, aborting')

    if names:
        for name in names:
            for inst in ecs.get_all_instances(zone_id=zone_id, instance_ids=ids, instance_name=name):
                instances.append(get_instance_info(inst))
                instance_ids.append(inst.id)
    else:
        for inst in ecs.get_all_instances(zone_id=zone_id, instance_ids=ids):
            instances.append(get_instance_info(inst))
            instance_ids.append(inst.id)

    module.exit_json(changed=False, instance_ids=instance_ids, instances=instances, total=len(instances))


if __name__ == '__main__':
    main()

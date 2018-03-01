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
module: alicloud_instance
version_added: "2.5"
short_description: Create, Start, Stop, Restart or Terminate an Instance in ECS. Add or Remove Instance to/from a Security Group.
description:
    - Create, start, stop, restart, modify or terminate ecs instances.
    - Add or remove ecs instances to/from security group.
options:
    state:
      description:
        - The state of the instance after operating.
      default: 'present'
      choices: [ 'present', 'running', 'stopped', 'restarted', 'absent' ]
    alicloud_zone:
      description:
        - Aliyun availability zone ID in which to launch the instance.
          If it is not specified, it will be allocated by system automatically.
      aliases: ['zone_id', 'zone' ]
    image_id:
      description:
        - Image ID used to launch instances. Required when C(state=present) and creating new ECS instances.
      aliases: [ 'image' ]
    instance_type:
      description:
        - Instance type used to launch instances. Required when C(state=present) and creating new ECS instances.
      aliases: [ 'type' ]
    group_id:
      description:
        - Security Group id used to launch instance or join/remove existing instances to/from the specified Security Group.
      aliases: [ 'security_group_id' ]
    vswitch_id:
      description:
        - The subnet ID in which to launch the instances (VPC).
      aliases: ['subnet_id']
    instance_name:
      description:
        - The name of ECS instance, which is a string of 2 to 128 Chinese or English characters. It must begin with an
          uppercase/lowercase letter or a Chinese character and can contain numerals, ".", "_" or "-".
          It cannot begin with http:// or https://.
      aliases: ['name']
    description:
      description:
        - The description of ECS instance, which is a string of 2 to 256 characters. It cannot begin with http:// or https://.
    internet_charge_type:
      description:
        - Internet charge type of ECS instance.
      default: "PayByBandwidth"
      choices: ["PayByBandwidth", "PayByTraffic"]
    max_bandwidth_in:
      description:
        - Maximum incoming bandwidth from the public network, measured in Mbps (Mega bit per second).
      default: 200
    max_bandwidth_out:
      description:
        - Maximum outgoing bandwidth to the public network, measured in Mbps (Mega bit per second).
      default: 0
    host_name:
      description:
        - Instance host name.
    password:
      description:
        - The password to login instance. After rebooting instances, the modified password would be take effect.
    system_disk_category:
      description:
        - Category of the system disk.
      default: "cloud_efficiency"
      choices: ["cloud_efficiency", "cloud_ssd"]
    system_disk_size:
      description:
        - Size of the system disk, in GB
      default: 40
      choices: [40~500]
    system_disk_name:
      description:
        - Name of the system disk.
    system_disk_description:
      description:
        - Description of the system disk.
    count:
      description:
        - The number of the new instance. An integer value which indicates how many instances that match I(count_tag)
          should be running. Instances are either created or terminated based on this value.
      default: 1
    count_tag:
      description:
      - I(count) determines how many instances based on a specific tag criteria should be present.
        This can be expressed in multiple ways and is shown in the EXAMPLES section.
        The specified count_tag must already exist or be passed in as the I(instance_tags) option.
        If it is not specified, it will be replaced by I(instance_name).
    allocate_public_ip:
      description:
        - Whether allocate a public ip for the new instance.
      default: False
      aliases: [ 'assign_public_ip' ]
      type: bool
    instance_charge_type:
      description:
        - The charge type of the instance.
      choices: ["PrePaid", "PostPaid"]
      default: "PostPaid"
    period:
      description:
        - The charge duration of the instance. Required when C(instance_charge_type=PrePaid).
      choices: [1~9,12,24,36]
      default: 1
    auto_renew:
      description:
        - Whether automate renew the charge of the instance.
      type: bool
      default: False
    auto_renew_period:
      description:
        - The duration of the automatic renew the charge of the instance. Required when C(auto_renew=True).
      choices: [1, 2, 3, 6, 12]
    instance_ids:
      description:
        - A list of instance ids. It is required when need to operate existing instances.
          If it is specified, I(count) will lose efficacy.
    force:
      description:
        - Whether the current operation needs to be execute forcibly.
      default: False
      type: bool
    instance_tags:
      description:
        - A hash/dictionaries of instance tags, to add to the new instance or for starting/stopping instance by tag. C({"key":"value"})
      aliases: ["tags"]
    sg_action:
      description:
        - The action of operating security group.
      choices: ['join', 'leave']
    key_name:
      description:
        - The name of key pair which is used to access ECS instance in SSH.
      required: false
      aliases: ['keypair']
    user_data:
      description:
        - User-defined data to customize the startup behaviors of an ECS instance and to pass data into an ECS instance.
          It only will take effect when launching the new ECS instances.
      required: false
author:
    - "He Guimin (@xiaozhu36)"
requirements:
    - "python >= 2.6"
    - "footmark >= 1.1.16"
extends_documentation_fragment:
    - alicloud
'''

EXAMPLES = '''
# basic provisioning example vpc network
- name: basic provisioning example
  hosts: localhost
  vars:
    alicloud_access_key: <your-alicloud-access-key-id>
    alicloud_secret_key: <your-alicloud-access-secret-key>
    alicloud_region: cn-beijing
    image: ubuntu1404_64_40G_cloudinit_20160727.raw
    instance_type: ecs.n4.small
    vswitch_id: vsw-abcd1234
    assign_public_ip: True
    max_bandwidth_out: 10
    host_name: myhost
    password: mypassword
    system_disk_category: cloud_efficiency
    system_disk_size: 100
    internet_charge_type: PayByBandwidth
    group_id: sg-f2rwnfh23r
    sg_action: join

    instance_ids: ["i-abcd12346", "i-abcd12345"]
    force: True

  tasks:
    - name: launch ECS instance in VPC network
      alicloud_instance:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        image: '{{ image }}'
        system_disk_category: '{{ system_disk_category }}'
        system_disk_size: '{{ system_disk_size }}'
        instance_type: '{{ instance_type }}'
        vswitch_id: '{{ vswitch_id }}'
        assign_public_ip: '{{ assign_public_ip }}'
        internet_charge_type: '{{ internet_charge_type }}'
        max_bandwidth_out: '{{ max_bandwidth_out }}'
        instance_tags:
            Name: created_one
        host_name: '{{ host_name }}'
        password: '{{ password }}'

    - name: with count and count_tag to create a number of instances
      alicloud_instance:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        image: '{{ image }}'
        system_disk_category: '{{ system_disk_category }}'
        system_disk_size: '{{ system_disk_size }}'
        instance_type: '{{ instance_type }}'
        assign_public_ip: '{{ assign_public_ip }}'
        group_id: '{{ group_id }}'
        internet_charge_type: '{{ internet_charge_type }}'
        max_bandwidth_out: '{{ max_bandwidth_out }}'
        instance_tags:
            Name: created_one
            Version: 0.1
        count: 2
        count_tag:
            Name: created_one
        host_name: '{{ host_name }}'
        password: '{{ password }}'

    - name: start instance
      alicloud_instance:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        instance_ids: '{{ instance_ids }}'
        state: 'running'

    - name: reboot instance forcibly
      ecs:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        instance_ids: '{{ instance_ids }}'
        state: 'restarted'
        force: '{{ force }}'

    - name: Add instances to an security group
      ecs:
        alicloud_access_key: '{{ alicloud_access_key }}'
        alicloud_secret_key: '{{ alicloud_secret_key }}'
        alicloud_region: '{{ alicloud_region }}'
        instance_ids: '{{ instance_ids }}'
        group_id: '{{ group_id }}'
        sg_action: '{{ sg_action }}'
'''

RETURN = '''
instance_ids:
    description: List all instances's id after operating ecs instance.
    returned: expect absent
    type: list
    sample: ["i-35b333d9","i-ddavdaeb3"]
instance_ips:
    description: List all instances's public ip address after operating ecs instance.
    returned: expect absent
    type: list
    sample: ["10.1.1.1","10.1.1.2"]
instance_names:
    description: List all instances's name after operating ecs instance.
    returned: expect absent
    type: list
    sample: ["MyInstane","MyInstane2"]
total:
    description: The number of all instances after operating ecs instance.
    returned: expect absent
    type: int
    sample: 2
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


def get_public_ip(instance):
    if instance.public_ip_address:
        return instance.public_ip_address
    elif instance.eip:
        return instance.eip
    return ""


def create_instance(module, ecs, exact_count):
    """
    create an instance in ecs
    """
    if exact_count <= 0:
        return None
    zone_id = module.params['alicloud_zone']
    image_id = module.params['image_id']
    instance_type = module.params['instance_type']
    group_id = module.params['group_id']
    vswitch_id = module.params['vswitch_id']
    instance_name = module.params['instance_name']
    description = module.params['description']
    internet_charge_type = module.params['internet_charge_type']
    max_bandwidth_out = module.params['max_bandwidth_out']
    max_bandwidth_in = module.params['max_bandwidth_out']
    host_name = module.params['host_name']
    password = module.params['password']
    system_disk_category = module.params['system_disk_category']
    system_disk_size = module.params['system_disk_size']
    system_disk_name = module.params['system_disk_name']
    system_disk_description = module.params['system_disk_description']
    allocate_public_ip = module.params['allocate_public_ip']
    instance_tags = module.params['instance_tags']
    period = module.params['period']
    auto_renew = module.params['auto_renew']
    instance_charge_type = module.params['instance_charge_type']
    auto_renew_period = module.params['auto_renew_period']
    user_data = module.params['user_data']
    key_name = module.params['key_name']

    # check whether the required parameter passed or not
    if not image_id:
        module.fail_json(msg='image_id is required for new instance')
    if not instance_type:
        module.fail_json(msg='instance_type is required for new instance')

    client_token = "Ansible-Alicloud-%s-%s" % (hash(str(module.params)), str(time.time()))

    try:
        # call to create_instance method from footmark
        instances = ecs.create_instance(image_id=image_id, instance_type=instance_type, group_id=group_id,
                                        zone_id=zone_id, instance_name=instance_name, description=description,
                                        internet_charge_type=internet_charge_type, max_bandwidth_out=max_bandwidth_out,
                                        max_bandwidth_in=max_bandwidth_in, host_name=host_name, password=password,
                                        io_optimized='optimized', system_disk_category=system_disk_category,
                                        system_disk_size=system_disk_size, system_disk_name=system_disk_name,
                                        system_disk_description=system_disk_description,
                                        vswitch_id=vswitch_id, count=exact_count, allocate_public_ip=allocate_public_ip,
                                        instance_charge_type=instance_charge_type, period=period, auto_renew=auto_renew,
                                        auto_renew_period=auto_renew_period, instance_tags=instance_tags,
                                        key_pair_name=key_name, user_data=user_data, client_token=client_token)

    except Exception as e:
        module.fail_json(msg='Unable to create instance, error: {0}'.format(e))

    return instances


def main():
    argument_spec = ecs_argument_spec()
    argument_spec.update(dict(
        group_id=dict(type='str', aliases=['security_group_id']),
        alicloud_zone=dict(type='str', aliases=['zone_id', 'zone']),
        instance_type=dict(type='str', aliases=['type']),
        image_id=dict(type='str', aliases=['image']),
        count=dict(type='int', default=1),
        count_tag=dict(type='str'),
        vswitch_id=dict(type='str', aliases=['subnet_id']),
        instance_name=dict(type='str', aliases=['name']),
        host_name=dict(type='str'),
        password=dict(type='str', no_log=True),
        internet_charge_type=dict(type='str', default="PayByBandwidth", choices=["PayByBandwidth", "PayByTraffic"]),
        max_bandwidth_in=dict(type='int', default=200),
        max_bandwidth_out=dict(type='int', default=0),
        system_disk_category=dict(type='str', default='cloud_efficiency'),
        system_disk_size=dict(type='int', default='40'),
        system_disk_name=dict(type='str'),
        system_disk_description=dict(type='str'),
        force=dict(type='bool', default=False),
        instance_tags=dict(type='dict', aliases=['tags']),
        state=dict(default='present', choices=['present', 'running', 'stopped', 'restarted', 'absent']),
        description=dict(type='str'),
        allocate_public_ip=dict(type='bool', aliases=['assign_public_ip'], default=False),
        instance_charge_type=dict(type='str', default='PostPaid'),
        period=dict(type='int', default=1),
        auto_renew=dict(type='bool', default=False),
        instance_ids=dict(type='list'),
        sg_action=dict(type='str'),
        auto_renew_period=dict(type='int'),
        key_name=dict(type='str', aliases=['keypair']),
        user_data=dict(type='str')
    )
    )
    module = AnsibleModule(argument_spec=argument_spec)

    if HAS_FOOTMARK is False:
        module.fail_json(msg="Package 'footmark' required for the module alicloud_instance.")

    ecs = ecs_connect(module)
    state = module.params['state']
    instance_ids = module.params['instance_ids']
    count_tag = module.params['count_tag']
    count = module.params['count']
    instance_name = module.params['instance_name']
    force = module.params['force']
    zone_id = module.params['alicloud_zone']
    key_name = module.params['key_name']
    changed = False

    instances = []
    if instance_ids:
        if not isinstance(instance_ids, list):
            module.fail_json(msg='The parameter instance_ids should be a list, aborting')
        instances = ecs.get_all_instances(zone_id=zone_id, instance_ids=instance_ids)
        if not instances:
            module.fail_json(msg="There are no instances in our record based on instance_ids {0}. "
                                 "Please check it and try again.".format(instance_ids))
    elif count_tag:
        instances = ecs.get_all_instances(zone_id=zone_id, instance_tags=eval(count_tag))
    elif instance_name:
        instances = ecs.get_all_instances(zone_id=zone_id, instance_name=instance_name)

    ids = []
    ips = []
    names = []
    if state == 'present':
        if not instance_ids:
            if len(instances) > count:
                for i in range(0, len(instances) - count):
                    inst = instances[len(instances) - 1]
                    if inst.status is not 'stopped' and not force:
                        module.fail_json(msg="That to delete instance {0} is failed results from it is running, "
                                             "and please stop it or set 'force' as True.".format(inst.id))
                    try:
                        changed = inst.terminate(force=force)
                    except Exception as e:
                        module.fail_json(msg="Delete instance {0} got an error: {1}".format(inst.id, e))
                    instances.pop(len(instances) - 1)
            else:
                try:
                    new_instances = create_instance(module, ecs, count - len(instances))
                    if new_instances:
                        changed = True
                        instances.extend(new_instances)
                except Exception as e:
                    module.fail_json(msg="Create new instances got an error: {0}".format(e))

        # Security Group join/leave begin
        sg_action = module.params['sg_action']

        if sg_action:
            action = sg_action.strip().lower()

            if action not in ('join', 'leave'):
                module.fail_json(msg='To perform join_security_group or leave_security_group operation,'
                                     'sg_action must be either join or leave respectively')

            security_group_id = module.params['group_id']
            for inst in instances:
                # Adding an Instance to a Security Group
                if action == 'join':
                    if security_group_id not in inst.security_group_ids['security_group_id']:
                        changed = inst.join_security_group(security_group_id)
                else:
                    if security_group_id in inst.security_group_ids['security_group_id']:
                        changed = inst.leave_security_group(security_group_id)

        # Security Group join/leave ends here

        # Attach/Detach key pair
        inst_ids = []
        for inst in instances:
            if key_name is not None and key_name != inst.key_name:
                if key_name == "":
                    changed = inst.detach_key_pair()
                else:
                    inst_ids.append(inst.id)
        if inst_ids:
            changed = ecs.attach_key_pair(instance_ids=inst_ids, key_pair_name=key_name)

        # Modify instance attribute
        description = module.params['description']
        host_name = module.params['host_name']
        password = module.params['password']
        for inst in instances:
            update = False
            if instance_name and instance_name != inst.name:
                update = True
            else:
                name = inst.name
            if description and description != inst.description:
                update = True
            else:
                description = inst.description
            if host_name and host_name != inst.host_name:
                update = True
            else:
                host_name = inst.host_name
            if password:
                update = True

            if update:
                try:
                    changed = inst.modify(name=name, description=description, host_name=host_name, password=password)
                except Exception as e:
                    module.fail_json(msg="Modify instance attribute {0} got an error: {1}".format(inst.id, e))

            if inst.id not in ids:
                ids.append(inst.id)
                names.append(inst.name)
            ip = get_public_ip(inst)
            if ip not in ips:
                ips.append(ip)

        module.exit_json(changed=changed, instance_ids=ids, instance_ips=ips, instance_names=names, total=len(ids))

    else:
        if len(instances) < 1:
            module.fail_json(msg='Please specify ECS instances that you want to operate by using '
                                 'parameters instance_ids, instance_tags or instance_name, aborting')
        force = module.params['force']
        if state == 'running':
            try:
                for inst in instances:
                    changed = inst.start()
                    if changed:
                        ids.append(inst.id)
                        names.append(inst.name)
                        ips.append(get_public_ip(inst))

                module.exit_json(changed=changed, instance_ids=ids, instance_ips=ips, instance_names=names, total=len(ids))
            except Exception as e:
                module.fail_json(msg='Start instances got an error: {0}'.format(e))
        elif state == 'stopped':
            try:
                for inst in instances:
                    changed = inst.stop(force=force)
                    if changed:
                        ids.append(inst.id)
                        names.append(inst.name)
                        ips.append(get_public_ip(inst))

                module.exit_json(changed=changed, instance_ids=ids, instance_ips=ips, instance_names=names, total=len(ids))
            except Exception as e:
                module.fail_json(msg='Stop instances got an error: {0}'.format(e))
        elif state == 'restarted':
            try:
                for inst in instances:
                    changed = inst.reboot(force=module.params['force'])
                    if changed:
                        ids.append(inst.id)
                        names.append(inst.name)
                        ips.append(get_public_ip(inst))

                module.exit_json(changed=changed, instance_ids=ids, instance_ips=ips, instance_names=names, total=len(ids))
            except Exception as e:
                module.fail_json(msg='Reboot instances got an error: {0}'.format(e))
        else:
            try:
                for inst in instances:
                    if inst.status is not 'stopped' and not force:
                        module.fail_json(msg="Instance is running, and please stop it or set 'force' as True.")
                    changed = inst.terminate(force=module.params['force'])

                module.exit_json(changed=changed)
            except Exception as e:
                module.fail_json(msg='Delete instance got an error: {0}'.format(e))


if __name__ == '__main__':
    main()

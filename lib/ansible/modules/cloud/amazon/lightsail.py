#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: lightsail
short_description: Manage instances in AWS Lightsail
description:
     - Manage instances in AWS Lightsail.
     - Instance tagging is not yet supported in this module.
version_added: "2.4"
author:
    - "Nick Ball (@nickball)"
    - "Prasad Katti (@prasadkatti)"
options:
  state:
    description:
      - Indicate desired state of the target.
      - I(rebooted) and I(restarted) are aliases.
    default: present
    choices: ['present', 'absent', 'running', 'restarted', 'rebooted', 'stopped']
    type: str
  name:
    description: Name of the instance.
    required: true
    type: str
  zone:
    description:
      - AWS availability zone in which to launch the instance.
      - Required when I(state=present)
    type: str
  blueprint_id:
    description:
      - ID of the instance blueprint image.
      - Required when I(state=present)
    type: str
  bundle_id:
    description:
      - Bundle of specification info for the instance.
      - Required when I(state=present).
    type: str
  user_data:
    description:
      - Launch script that can configure the instance with additional data.
    type: str
  key_pair_name:
    description:
      - Name of the key pair to use with the instance.
      - If I(state=present) and a key_pair_name is not provided, the default keypair from the region will be used.
    type: str
  wait:
    description:
      - Wait for the instance to be in state 'running' before returning.
      - If I(wait=false) an ip_address may not be returned.
      - Has no effect when I(state=rebooted) or I(state=absent).
    type: bool
    default: true
  wait_timeout:
    description:
      - How long before I(wait) gives up, in seconds.
    default: 300
    type: int

requirements:
  - boto3

extends_documentation_fragment:
  - aws
  - ec2
'''


EXAMPLES = '''
# Create a new Lightsail instance
- lightsail:
    state: present
    name: my_instance
    region: us-east-1
    zone: us-east-1a
    blueprint_id: ubuntu_16_04
    bundle_id: nano_1_0
    key_pair_name: id_rsa
    user_data: " echo 'hello world' > /home/ubuntu/test.txt"
  register: my_instance

# Delete an instance
- lightsail:
    state: absent
    region: us-east-1
    name: my_instance

'''

RETURN = '''
changed:
  description: if a snapshot has been modified/created
  returned: always
  type: bool
  sample:
    changed: true
instance:
  description: instance data
  returned: always
  type: dict
  sample:
    arn: "arn:aws:lightsail:us-east-1:448830907657:Instance/1fef0175-d6c8-480e-84fa-214f969cda87"
    blueprint_id: "ubuntu_16_04"
    blueprint_name: "Ubuntu"
    bundle_id: "nano_1_0"
    created_at: "2017-03-27T08:38:59.714000-04:00"
    hardware:
      cpu_count: 1
      ram_size_in_gb: 0.5
    is_static_ip: false
    location:
      availability_zone: "us-east-1a"
      region_name: "us-east-1"
    name: "my_instance"
    networking:
      monthly_transfer:
        gb_per_month_allocated: 1024
      ports:
        - access_direction: "inbound"
          access_from: "Anywhere (0.0.0.0/0)"
          access_type: "public"
          common_name: ""
          from_port: 80
          protocol: tcp
          to_port: 80
        - access_direction: "inbound"
          access_from: "Anywhere (0.0.0.0/0)"
          access_type: "public"
          common_name: ""
          from_port: 22
          protocol: tcp
          to_port: 22
    private_ip_address: "172.26.8.14"
    public_ip_address: "34.207.152.202"
    resource_type: "Instance"
    ssh_key_name: "keypair"
    state:
      code: 16
      name: running
    support_code: "588307843083/i-0997c97831ee21e33"
    username: "ubuntu"
'''

import time

try:
    import botocore
except ImportError:
    # will be caught by AnsibleAWSModule
    pass

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict


def find_instance_info(module, client, instance_name, fail_if_not_found=False):

    try:
        res = client.get_instance(instanceName=instance_name)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NotFoundException' and not fail_if_not_found:
            return None
        module.fail_json_aws(e)
    return res['instance']


def wait_for_instance_state(module, client, instance_name, states):
    """
    `states` is a list of instance states that we are waiting for.
    """

    wait_timeout = module.params.get('wait_timeout')
    wait_max = time.time() + wait_timeout
    while wait_max > time.time():
        try:
            instance = find_instance_info(module, client, instance_name)
            if instance['state']['name'] in states:
                break
            time.sleep(5)
        except botocore.exceptions.ClientError as e:
            module.fail_json_aws(e)
    else:
        module.fail_json(msg='Timed out waiting for instance "{0}" to get to one of the following states -'
                             ' {1}'.format(instance_name, states))


def create_instance(module, client, instance_name):

    inst = find_instance_info(module, client, instance_name)
    if inst:
        module.exit_json(changed=False, instance=camel_dict_to_snake_dict(inst))
    else:
        create_params = {'instanceNames': [instance_name],
                         'availabilityZone': module.params.get('zone'),
                         'blueprintId': module.params.get('blueprint_id'),
                         'bundleId': module.params.get('bundle_id'),
                         'userData': module.params.get('user_data')}

        key_pair_name = module.params.get('key_pair_name')
        if key_pair_name:
            create_params['keyPairName'] = key_pair_name

        try:
            client.create_instances(**create_params)
        except botocore.exceptions.ClientError as e:
            module.fail_json_aws(e)

        wait = module.params.get('wait')
        if wait:
            desired_states = ['running']
            wait_for_instance_state(module, client, instance_name, desired_states)
        inst = find_instance_info(module, client, instance_name, fail_if_not_found=True)

        module.exit_json(changed=True, instance=camel_dict_to_snake_dict(inst))


def delete_instance(module, client, instance_name):

    changed = False

    inst = find_instance_info(module, client, instance_name)
    if inst is None:
        module.exit_json(changed=changed, instance={})

    # Wait for instance to exit transition state before deleting
    desired_states = ['running', 'stopped']
    wait_for_instance_state(module, client, instance_name, desired_states)

    try:
        client.delete_instance(instanceName=instance_name)
        changed = True
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)

    module.exit_json(changed=changed, instance=camel_dict_to_snake_dict(inst))


def restart_instance(module, client, instance_name):
    """
    Reboot an existing instance
    Wait will not apply here as this is an OS-level operation
    """

    changed = False

    inst = find_instance_info(module, client, instance_name, fail_if_not_found=True)

    try:
        client.reboot_instance(instanceName=instance_name)
        changed = True
    except botocore.exceptions.ClientError as e:
        module.fail_json_aws(e)

    module.exit_json(changed=changed, instance=camel_dict_to_snake_dict(inst))


def start_or_stop_instance(module, client, instance_name, state):
    """
    Start or stop an existing instance
    """

    changed = False

    inst = find_instance_info(module, client, instance_name, fail_if_not_found=True)

    # Wait for instance to exit transition state before state change
    desired_states = ['running', 'stopped']
    wait_for_instance_state(module, client, instance_name, desired_states)

    # Try state change
    if inst and inst['state']['name'] != state:
        try:
            if state == 'running':
                client.start_instance(instanceName=instance_name)
            else:
                client.stop_instance(instanceName=instance_name)
        except botocore.exceptions.ClientError as e:
            module.fail_json_aws(e)
        changed = True
        # Grab current instance info
        inst = find_instance_info(module, client, instance_name)

    wait = module.params.get('wait')
    if wait:
        desired_states = [state]
        wait_for_instance_state(module, client, instance_name, desired_states)
        inst = find_instance_info(module, client, instance_name, fail_if_not_found=True)

    module.exit_json(changed=changed, instance=camel_dict_to_snake_dict(inst))


def main():

    argument_spec = dict(
        name=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['present', 'absent', 'stopped', 'running', 'restarted',
                                                           'rebooted']),
        zone=dict(type='str'),
        blueprint_id=dict(type='str'),
        bundle_id=dict(type='str'),
        key_pair_name=dict(type='str'),
        user_data=dict(type='str', default=''),
        wait=dict(type='bool', default=True),
        wait_timeout=dict(default=300, type='int'),
    )

    module = AnsibleAWSModule(argument_spec=argument_spec,
                              required_if=[['state', 'present', ('zone', 'blueprint_id', 'bundle_id')]])

    client = module.client('lightsail')

    name = module.params.get('name')
    state = module.params.get('state')

    if state == 'present':
        create_instance(module, client, name)
    elif state == 'absent':
        delete_instance(module, client, name)
    elif state in ('running', 'stopped'):
        start_or_stop_instance(module, client, name, state)
    elif state in ('restarted', 'rebooted'):
        restart_instance(module, client, name)


if __name__ == '__main__':
    main()

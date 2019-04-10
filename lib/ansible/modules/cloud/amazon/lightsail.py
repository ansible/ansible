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
short_description: Create or delete a virtual machine instance in AWS Lightsail
description:
     - Creates or instances in AWS Lightsail and optionally wait for it to be 'running'.
version_added: "2.4"
author: "Nick Ball (@nickball)"
options:
  state:
    description:
      - Indicate desired state of the target.
    default: present
    choices: ['present', 'absent', 'running', 'restarted', 'stopped']
  name:
    description:
      - Name of the instance
    required: true
  zone:
    description:
      - AWS availability zone in which to launch the instance. Required when state='present'
  blueprint_id:
    description:
      - ID of the instance blueprint image. Required when state='present'
  bundle_id:
    description:
      - Bundle of specification info for the instance. Required when state='present'
  user_data:
    description:
      - Launch script that can configure the instance with additional data
  key_pair_name:
    description:
      - Name of the key pair to use with the instance
  wait:
    description:
      - Wait for the instance to be in state 'running' before returning.  If wait is "no" an ip_address may not be returned
    type: bool
    default: 'yes'
  wait_timeout:
    description:
      - How long before wait gives up, in seconds.
    default: 300

requirements:
  - "python >= 2.6"
  - boto3

extends_documentation_fragment:
  - aws
  - ec2
'''


EXAMPLES = '''
# Create a new Lightsail instance, register the instance details
- lightsail:
    state: present
    name: myinstance
    region: us-east-1
    zone: us-east-1a
    blueprint_id: ubuntu_16_04
    bundle_id: nano_1_0
    key_pair_name: id_rsa
    user_data: " echo 'hello world' > /home/ubuntu/test.txt"
    wait_timeout: 500
  register: my_instance

- debug:
    msg: "Name is {{ my_instance.instance.name }}"

- debug:
    msg: "IP is {{ my_instance.instance.public_ip_address }}"

# Delete an instance if present
- lightsail:
    state: absent
    region: us-east-1
    name: myinstance

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
import traceback

try:
    import botocore
    HAS_BOTOCORE = True
except ImportError:
    HAS_BOTOCORE = False

try:
    import boto3
except ImportError:
    # will be caught by imported HAS_BOTO3
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (ec2_argument_spec, get_aws_connection_info, boto3_conn,
                                      HAS_BOTO3, camel_dict_to_snake_dict)


def create_instance(module, client, instance_name):
    """
    Create an instance

    module: Ansible module object
    client: authenticated lightsail connection object
    instance_name: name of instance to delete

    Returns a dictionary of instance information
    about the new instance.

    """

    changed = False

    # Check if instance already exists
    inst = None
    try:
        inst = _find_instance_info(client, instance_name)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != 'NotFoundException':
            module.fail_json(msg='Error finding instance {0}, error: {1}'.format(instance_name, e))

    zone = module.params.get('zone')
    blueprint_id = module.params.get('blueprint_id')
    bundle_id = module.params.get('bundle_id')
    key_pair_name = module.params.get('key_pair_name')
    user_data = module.params.get('user_data')
    user_data = '' if user_data is None else user_data

    resp = None
    if inst is None:
        try:
            resp = client.create_instances(
                instanceNames=[
                    instance_name
                ],
                availabilityZone=zone,
                blueprintId=blueprint_id,
                bundleId=bundle_id,
                userData=user_data,
                keyPairName=key_pair_name,
            )
            resp = resp['operations'][0]
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg='Unable to create instance {0}, error: {1}'.format(instance_name, e))
        changed = True

    inst = _find_instance_info(client, instance_name)

    return (changed, inst)


def delete_instance(module, client, instance_name):
    """
    Terminates an instance

    module: Ansible module object
    client: authenticated lightsail connection object
    instance_name: name of instance to delete

    Returns a dictionary of instance information
    about the instance deleted (pre-deletion).

    If the instance to be deleted is running
    "changed" will be set to False.

    """

    # It looks like deleting removes the instance immediately, nothing to wait for
    wait = module.params.get('wait')
    wait_timeout = int(module.params.get('wait_timeout'))
    wait_max = time.time() + wait_timeout

    changed = False

    inst = None
    try:
        inst = _find_instance_info(client, instance_name)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != 'NotFoundException':
            module.fail_json(msg='Error finding instance {0}, error: {1}'.format(instance_name, e))

    # Wait for instance to exit transition state before deleting
    if wait:
        while wait_max > time.time() and inst is not None and inst['state']['name'] in ('pending', 'stopping'):
            try:
                time.sleep(5)
                inst = _find_instance_info(client, instance_name)
            except botocore.exceptions.ClientError as e:
                if e.response['ResponseMetadata']['HTTPStatusCode'] == "403":
                    module.fail_json(msg="Failed to delete instance {0}. Check that you have permissions to perform the operation.".format(instance_name),
                                     exception=traceback.format_exc())
                elif e.response['Error']['Code'] == "RequestExpired":
                    module.fail_json(msg="RequestExpired: Failed to delete instance {0}.".format(instance_name), exception=traceback.format_exc())
                # sleep and retry
                time.sleep(10)

    # Attempt to delete
    if inst is not None:
        while not changed and ((wait and wait_max > time.time()) or (not wait)):
            try:
                client.delete_instance(instanceName=instance_name)
                changed = True
            except botocore.exceptions.ClientError as e:
                module.fail_json(msg='Error deleting instance {0}, error: {1}'.format(instance_name, e))

    # Timed out
    if wait and not changed and wait_max <= time.time():
        module.fail_json(msg="wait for instance delete timeout at %s" % time.asctime())

    return (changed, inst)


def restart_instance(module, client, instance_name):
    """
    Reboot an existing instance

    module: Ansible module object
    client: authenticated lightsail connection object
    instance_name: name of instance to reboot

    Returns a dictionary of instance information
    about the restarted instance

    If the instance was not able to reboot,
    "changed" will be set to False.

    Wait will not apply here as this is an OS-level operation
    """
    wait = module.params.get('wait')
    wait_timeout = int(module.params.get('wait_timeout'))
    wait_max = time.time() + wait_timeout

    changed = False

    inst = None
    try:
        inst = _find_instance_info(client, instance_name)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != 'NotFoundException':
            module.fail_json(msg='Error finding instance {0}, error: {1}'.format(instance_name, e))

    # Wait for instance to exit transition state before state change
    if wait:
        while wait_max > time.time() and inst is not None and inst['state']['name'] in ('pending', 'stopping'):
            try:
                time.sleep(5)
                inst = _find_instance_info(client, instance_name)
            except botocore.exceptions.ClientError as e:
                if e.response['ResponseMetadata']['HTTPStatusCode'] == "403":
                    module.fail_json(msg="Failed to restart instance {0}. Check that you have permissions to perform the operation.".format(instance_name),
                                     exception=traceback.format_exc())
                elif e.response['Error']['Code'] == "RequestExpired":
                    module.fail_json(msg="RequestExpired: Failed to restart instance {0}.".format(instance_name), exception=traceback.format_exc())
                time.sleep(3)

    # send reboot
    if inst is not None:
        try:
            client.reboot_instance(instanceName=instance_name)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] != 'NotFoundException':
                module.fail_json(msg='Unable to reboot instance {0}, error: {1}'.format(instance_name, e))
        changed = True

    return (changed, inst)


def startstop_instance(module, client, instance_name, state):
    """
    Starts or stops an existing instance

    module: Ansible module object
    client: authenticated lightsail connection object
    instance_name: name of instance to start/stop
    state: Target state ("running" or "stopped")

    Returns a dictionary of instance information
    about the instance started/stopped

    If the instance was not able to state change,
    "changed" will be set to False.

    """
    wait = module.params.get('wait')
    wait_timeout = int(module.params.get('wait_timeout'))
    wait_max = time.time() + wait_timeout

    changed = False

    inst = None
    try:
        inst = _find_instance_info(client, instance_name)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] != 'NotFoundException':
            module.fail_json(msg='Error finding instance {0}, error: {1}'.format(instance_name, e))

    # Wait for instance to exit transition state before state change
    if wait:
        while wait_max > time.time() and inst is not None and inst['state']['name'] in ('pending', 'stopping'):
            try:
                time.sleep(5)
                inst = _find_instance_info(client, instance_name)
            except botocore.exceptions.ClientError as e:
                if e.response['ResponseMetadata']['HTTPStatusCode'] == "403":
                    module.fail_json(msg="Failed to start/stop instance {0}. Check that you have permissions to perform the operation".format(instance_name),
                                     exception=traceback.format_exc())
                elif e.response['Error']['Code'] == "RequestExpired":
                    module.fail_json(msg="RequestExpired: Failed to start/stop instance {0}.".format(instance_name), exception=traceback.format_exc())
                time.sleep(1)

    # Try state change
    if inst is not None and inst['state']['name'] != state:
        try:
            if state == 'running':
                client.start_instance(instanceName=instance_name)
            else:
                client.stop_instance(instanceName=instance_name)
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg='Unable to change state for instance {0}, error: {1}'.format(instance_name, e))
        changed = True
        # Grab current instance info
        inst = _find_instance_info(client, instance_name)

    return (changed, inst)


def core(module):
    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    if not region:
        module.fail_json(msg='region must be specified')

    client = None
    try:
        client = boto3_conn(module, conn_type='client', resource='lightsail',
                            region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except (botocore.exceptions.ClientError, botocore.exceptions.ValidationError) as e:
        module.fail_json(msg='Failed while connecting to the lightsail service: %s' % e, exception=traceback.format_exc())

    changed = False
    state = module.params['state']
    name = module.params['name']

    if state == 'absent':
        changed, instance_dict = delete_instance(module, client, name)
    elif state in ('running', 'stopped'):
        changed, instance_dict = startstop_instance(module, client, name, state)
    elif state == 'restarted':
        changed, instance_dict = restart_instance(module, client, name)
    elif state == 'present':
        changed, instance_dict = create_instance(module, client, name)

    module.exit_json(changed=changed, instance=camel_dict_to_snake_dict(instance_dict))


def _find_instance_info(client, instance_name):
    ''' handle exceptions where this function is called '''
    inst = None
    try:
        inst = client.get_instance(instanceName=instance_name)
    except botocore.exceptions.ClientError as e:
        raise
    return inst['instance']


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        name=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['present', 'absent', 'stopped', 'running', 'restarted']),
        zone=dict(type='str'),
        blueprint_id=dict(type='str'),
        bundle_id=dict(type='str'),
        key_pair_name=dict(type='str'),
        user_data=dict(type='str'),
        wait=dict(type='bool', default=True),
        wait_timeout=dict(default=300, type='int'),
    ))

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='Python module "boto3" is missing, please install it')

    if not HAS_BOTOCORE:
        module.fail_json(msg='Python module "botocore" is missing, please install it')

    try:
        core(module)
    except (botocore.exceptions.ClientError, Exception) as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())


if __name__ == '__main__':
    main()

#!/usr/bin/python

# Copyright: (c) 2018, Aaron Smith <ajsmith10381@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: dms_instance
short_description: Manage replication instances for AWS Database Migration Service.
description:
    - Create, update, and destroy AWS Database Migration Service replication instances.
author: "Aaron Smith (@slapula)"
version_added: "2.6"
requirements: [ 'botocore', 'boto3' ]
options:
  name:
    description:
    - The replication instance identifier.
    - This parameter is stored as a lowercase string.
    required: true
  state:
    description:
    - Whether the replication instance should be exist or not.
    choices: ['present', 'absent']
    default: 'present'
  storage:
    description:
    - The amount of storage (in gigabytes) to be initially allocated for the replication instance.
  instance_type:
    description:
    - The compute and memory capacity of the replication instance as specified by the replication instance class.
    required: true
    choices: ['dms.t2.micro', 'dms.t2.small', 'dms.t2.medium', 'dms.t2.large', 'dms.c4.large', 'dms.c4.xlarge', 'dms.c4.2xlarge', 'dms.c4.4xlarge']
  vpc_security_groups:
    description:
    - Specifies the VPC security group to be used with the replication instance.
    - The VPC security group must work with the VPC containing the replication instance.
  availability_zone:
    description:
    - The EC2 Availability Zone that the replication instance will be created in.
  subnet_group:
    description:
    - A replication subnet group to associate with the instance.
  maintenance_window:
    description:
    - The weekly time range during which system maintenance can occur, in Universal Coordinated Time (UTC).
  multi_az:
    description:
    - Specifies if the replication instance is a Multi-AZ deployment.
    - You cannot set the AvailabilityZone parameter if the Multi-AZ parameter is set to `true`.
    type: 'bool'
    default: false
  engine_version:
    description:
    - The engine version number of the replication instance.
  auto_minor_version_upgrade:
    description:
    - Indicates that minor engine upgrades will be applied automatically to the replication instance during the maintenance window.
    type: 'bool'
    default: true
  tags:
    description:
    - Tags to be added to the replication instance.
  kms_key_id:
    description:
    - The KMS key identifier that will be used to encrypt the content on the replication instance.
  publicly_accessible:
    description:
    - Specifies the accessibility options for the replication instance.
    type: 'bool'
    default: true
extends_documentation_fragment:
    - ec2
    - aws
'''


EXAMPLES = r'''
- name: Create replication instance for DMS tasks
  dms_instance:
    name: 'my-dms-instance'
    state: present
    instance_type: 'dms.t2.micro'
    auto_minor_version_upgrade: false
    multi_az: true

- name: Destroy replication instance
  dms_instance:
    name: 'my-dms-instance'
    state: absent
    instance_type: 'dms.t2.micro'
'''


RETURN = r'''
instance_arn:
    description: The ARN of the replication instance you just created or updated.
    returned: always
    type: string
'''

import os
import time

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, AWSRetry
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, boto3_tag_list_to_ansible_dict

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # handled by AnsibleAWSModule


def instance_exists(client, module, result):
    try:
        response = client.describe_replication_instances()
        for i in response['ReplicationInstances']:
            if i['ReplicationInstanceIdentifier'] == module.params.get('name'):
                result['current_config'] = i
                result['instance_arn'] = i['ReplicationInstanceArn']
                return True
    except (ClientError, IndexError):
        return False

    return False


def instance_update_waiter(client, module):
    try:
        instance_ready = False
        while instance_ready is False:
            time.sleep(5)
            status_check = client.describe_replication_instances()
            for i in status_check['ReplicationInstances']:
                if i['ReplicationInstanceIdentifier'] == module.params.get('name'):
                    if i['ReplicationInstanceStatus'] == 'available':
                        instance_ready = True
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed while waiting on replication instance status")


def instance_delete_waiter(client, module):
    try:
        instance_deleted = False
        while instance_deleted is False:
            time.sleep(5)
            status_check = client.describe_replication_instances()
            for i in status_check['ReplicationInstances']:
                if i['ReplicationInstanceIdentifier'] == module.params.get('name'):
                    instance_deleted = False
                else:
                    instance_deleted = True
            if not status_check['ReplicationInstances']:
                instance_deleted = True
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed while waiting on replication instance status")


def create_instance(client, module, params, result):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.create_replication_instance(**params)
        instance_update_waiter(client, module)
        result['instance_arn'] = response['ReplicationInstance']['ReplicationInstanceArn']
        result['changed'] = True
        return result
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to create replication instance")

    return result


def update_instance(client, module, params, result):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        if 'Tags' in params:
            del params['Tags']
        if 'KmsKeyId' in params:
            del params['KmsKeyId']
        if 'PubliclyAccessible' in params:
            del params['PubliclyAccessible']
        if 'AvailabilityZone' in params:
            del params['AvailabilityZone']
        if 'ReplicationSubnetGroupIdentifier' in params:
            del params['ReplicationSubnetGroupIdentifier']

        param_changed = []
        param_keys = list(params.keys())
        current_keys = list(result['current_config'].keys())
        common_keys = set(param_keys) - (set(param_keys) - set(current_keys))
        for key in common_keys:
            if (params[key] != result['current_config'][key]):
                param_changed.append(True)
            else:
                param_changed.append(False)

        params['ReplicationInstanceArn'] = result['instance_arn']
        del result['current_config']

        if any(param_changed):
            response = client.modify_replication_instance(**params)
            instance_update_waiter(client, module)
            result['changed'] = True
            return result
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to update replication instance")

    return result


def delete_instance(client, module, result):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.delete_replication_instance(
            ReplicationInstanceArn=result['instance_arn']
        )
        instance_delete_waiter(client, module)
        del result['current_config']
        result['changed'] = True
        return result
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to delete replication instance")

    return result


def main():
    module = AnsibleAWSModule(
        argument_spec={
            'name': dict(type='str', required=True),
            'state': dict(type='str', choices=['present', 'absent'], default='present'),
            'storage': dict(type='int'),
            'instance_type': dict(
                type='str',
                choices=[
                    'dms.t2.micro',
                    'dms.t2.small',
                    'dms.t2.medium',
                    'dms.t2.large',
                    'dms.c4.large',
                    'dms.c4.xlarge',
                    'dms.c4.2xlarge',
                    'dms.c4.4xlarge'
                ],
                required=True
            ),
            'vpc_security_groups': dict(type='str'),
            'availability_zone': dict(type='str'),
            'subnet_group': dict(type='str'),
            'maintenance_window': dict(type='int'),
            'multi_az': dict(type='bool', default=False),
            'engine_version': dict(type='str'),
            'auto_minor_version_upgrade': dict(type='bool', default=True),
            'tags': dict(type='list'),
            'kms_key_id': dict(type='str'),
            'publicly_accessible': dict(type='bool', default=True),
        },
        supports_check_mode=True,
    )

    result = {
        'changed': False
    }

    params = {}
    params['ReplicationInstanceIdentifier'] = module.params.get('name')
    params['ReplicationInstanceClass'] = module.params.get('instance_type')
    if module.params.get('storage'):
        params['AllocatedStorage'] = module.params.get('storage')
    if module.params.get('vpc_security_groups'):
        params['VpcSecurityGroupIds'] = module.params.get('vpc_security_groups')
    if module.params.get('availability_zone'):
        params['AvailabilityZone'] = module.params.get('availability_zone')
    if module.params.get('subnet_group'):
        params['ReplicationSubnetGroupIdentifier'] = module.params.get('subnet_group')
    if module.params.get('maintenance_window'):
        params['PreferredMaintenanceWindow'] = module.params.get('maintenance_window')
    if module.params.get('multi_az'):
        params['MultiAZ'] = module.params.get('multi_az')
    if module.params.get('engine_version'):
        params['EngineVersion'] = module.params.get('engine_version')
    if module.params.get('tags'):
        params['Tags'] = module.params.get('tags')
    if module.params.get('auto_minor_version_upgrade'):
        params['AutoMinorVersionUpgrade'] = module.params.get('auto_minor_version_upgrade')
    if module.params.get('kms_key_id'):
        params['KmsKeyId'] = module.params.get('kms_key_id')
    if module.params.get('publicly_accessible'):
        params['PubliclyAccessible'] = module.params.get('publicly_accessible')

    client = module.client('dms')

    instance_status = instance_exists(client, module, result)

    desired_state = module.params.get('state')

    if desired_state == 'present':
        if not instance_status:
            create_instance(client, module, params, result)
        if instance_status:
            update_instance(client, module, params, result)

    if desired_state == 'absent':
        if instance_status:
            delete_instance(client, module, result)

    if 'instance_arn' in result:
        output = result['instance_arn']
    else:
        output = ''

    module.exit_json(changed=result['changed'], instance_arn=output)


if __name__ == '__main__':
    main()

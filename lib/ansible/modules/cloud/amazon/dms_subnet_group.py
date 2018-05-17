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
module: dms_subnet_group
short_description: Manage subnet groups for AWS Database Migration Service.
description:
    - Create, update, and destroy AWS Database Migration Service subnet groups.
author: "Aaron Smith (@slapula)"
version_added: "2.6"
requirements: [ 'botocore', 'boto3' ]
options:
  name:
    description:
    - The name for the replication subnet group. This value is stored as a lowercase string.
    required: true
  state:
    description:
     - Whether the replication subnet group should be exist or not.
    required: true
    choices: ['present', 'absent']
  description:
    description:
    - The description for the subnet group.
    required: true
  subnet_ids:
    description:
    - The EC2 subnet IDs for the subnet group.
    required: true
extends_documentation_fragment:
    - ec2
    - aws
'''


EXAMPLES = r'''
- name: Create replication subnet group for DMS instances
  dms_subnet_group:
    name: 'my_dms_subnet_group'
    state: present
    subnet_ids:
      - 'subnet-1a2b3c4d'
      - 'subnet-4d3c2b1a'

- name: Remove replication subnet group
  dms_subnet_group:
    name: 'my_dms_subnet_group'
    state: absent
    subnet_ids:
      - 'subnet-1a2b3c4d'
      - 'subnet-4d3c2b1a'
'''


RETURN = r'''#'''

import os
import time

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, AWSRetry
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, boto3_tag_list_to_ansible_dict

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # handled by AnsibleAWSModule


def group_exists(client, module, result):
    try:
        response = client.describe_replication_subnet_groups()
        for i in response['ReplicationSubnetGroups']:
            if i['ReplicationSubnetGroupIdentifier'] == module.params.get('name'):
                result['current_config'] = i
                return True
    except (ClientError, IndexError):
        return False

    return False


def group_waiter(client, module):
    try:
        group_ready = False
        while group_ready is False:
            time.sleep(5)
            status_check = client.describe_replication_subnet_groups()
            for i in status_check['ReplicationSubnetGroups']:
                if i['ReplicationSubnetGroupIdentifier'] == module.params.get('name'):
                    if i['SubnetGroupStatus'] == 'Complete':
                        group_ready = True
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed while waiting on replication subnet group status")


def create_group(client, module, params, result):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.create_replication_subnet_group(**params)
        group_waiter(client, module)
        result['changed'] = True
        return result
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to create replication subnet group")

    return result


def update_group(client, module, params, result):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        updated_params = {}
        param_changed = []
        updated_params['ReplicationSubnetGroupIdentifier'] = params['ReplicationSubnetGroupIdentifier']
        if params['ReplicationSubnetGroupDescription'] != result['current_config']['ReplicationSubnetGroupDescription']:
            updated_params['ReplicationSubnetGroupDescription'] = params['ReplicationSubnetGroupDescription']
            param_changed.append(True)
        else:
            param_changed.append(False)
        updated_params['SubnetIds'] = params['SubnetIds']
        current_subnets = [n['SubnetIdentifier'] for n in result['current_config']['Subnets']]
        if sorted(updated_params['SubnetIds']) != sorted(current_subnets):
            param_changed.append(True)
        else:
            param_changed.append(False)
        if any(param_changed):
            response = client.modify_replication_subnet_group(**updated_params)
            group_waiter(client, module)
            result['changed'] = True
            return result
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to update replication subnet group")

    return result


def delete_group(client, module, result):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.delete_replication_subnet_group(
            ReplicationSubnetGroupIdentifier=module.params.get('name')
        )
        result['changed'] = True
        return result
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to delete replication subnet group")

    return result


def main():
    module = AnsibleAWSModule(
        argument_spec={
            'name': dict(type='str', required=True),
            'state': dict(type='str', choices=['present', 'absent'], required=True),
            'description': dict(type='str', required=True),
            'subnet_ids': dict(type='list', required=True),
        },
        supports_check_mode=True,
    )

    result = {
        'changed': False
    }

    params = {}
    params['ReplicationSubnetGroupIdentifier'] = module.params.get('name')
    params['ReplicationSubnetGroupDescription'] = module.params.get('description')
    params['SubnetIds'] = module.params.get('subnet_ids')

    client = module.client('dms')

    group_status = group_exists(client, module, result)

    desired_state = module.params.get('state')

    if desired_state == 'present':
        if not group_status:
            create_group(client, module, params, result)
        if group_status:
            update_group(client, module, params, result)

    if desired_state == 'absent':
        if group_status:
            delete_group(client, module, result)

    module.exit_json(changed=result['changed'], output=result)


if __name__ == '__main__':
    main()

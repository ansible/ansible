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
module: dms_replication_task
short_description: Manage replication tasks for AWS Database Migration Service.
description:
    - Create, update, and destroy AWS Database Migration Service replication tasks.
    - Tasks must be in a stopped or failed state for updates to be applied.
author: "Aaron Smith (@slapula)"
version_added: "2.6"
requirements: [ 'botocore', 'boto3' ]
options:
  name:
    description:
    - The replication task identifier.
    - This parameter is stored as a lowercase string.
    required: true
  state:
    description:
    - Whether the replication task should be exist or not.
    choices: ['present', 'absent']
    default: 'present'
  source_endpoint:
    description:
    - The Amazon Resource Name (ARN) string that uniquely identifies the source endpoint.
    required: true
  target_endpoint:
    description:
    - The Amazon Resource Name (ARN) string that uniquely identifies the target endpoint.
    required: true
  replication_instance:
    description:
    - The Amazon Resource Name (ARN) of the replication instance.
    required: true
  migration_type:
    description:
    - The migration type.
    choices: ['full-load', 'cdc', 'full-load-and-cdc']
    default: 'full-load'
  table_mappings:
    description:
    - the path of the JSON file that contains the table mappings.
    - Precede the path with "file://".
    required: true
  settings:
    description:
    - Settings for the task, such as target metadata settings.
  cdc_start_time:
    description:
    - Indicates the start time for a change data capture (CDC) operation.
    - Use either `cdc_start_time` or `cdc_start_position` to specify when you want a CDC operation to start. Specifying both values results in an error.
  cdc_start_position:
    description:
    - Indicates when you want a change data capture (CDC) operation to start.
    - Use either `cdc_start_time` or `cdc_start_position` to specify when you want a CDC operation to start. Specifying both values results in an error.
  cdc_stop_position:
    description:
    - Indicates when you want a change data capture (CDC) operation to stop.
  tags:
    description:
    - Tags to be added to the replication instance.
extends_documentation_fragment:
    - ec2
    - aws
'''


EXAMPLES = r'''
- name: Create replication task
  dms_replication_task:
    name: 'my-dms-task'
    state: present
    source_endpoint: 'arn:aws:dms:us-east-2:123456789012:endpoint:BATR4T27ZSU5FS4PQQM3N8CW90'
    target_endpoint: 'arn:aws:dms:us-east-2:123456789012:endpoint:RAAR3R22XSH46S3PWLC3NJAWKM'
    replication_instance: 'arn:aws:dms:us-east-2:123456789012:rep:NVP1QVZRFXISB5AXBQHS2Z7IDE'
    migration_type: 'full-load'
    table_mappings: "file://mappings.json"

- name: Destroy replication task
  dms_replication_task:
    name: 'my-dms-task'
    state: absent
    source_endpoint: 'arn:aws:dms:us-east-2:123456789012:endpoint:BATR4T27ZSU5FS4PQQM3N8CW90'
    target_endpoint: 'arn:aws:dms:us-east-2:123456789012:endpoint:RAAR3R22XSH46S3PWLC3NJAWKM'
    replication_instance: 'arn:aws:dms:us-east-2:123456789012:rep:NVP1QVZRFXISB5AXBQHS2Z7IDE'
    migration_type: 'full-load'
    table_mappings: "file://mappings.json"
'''


RETURN = r'''
task_arn:
    description: The ARN of the replication task you just created or updated.
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


def task_exists(client, module, result):
    try:
        response = client.describe_replication_tasks()
        for i in response['ReplicationTasks']:
            if i['ReplicationTaskIdentifier'] == module.params.get('name'):
                result['current_config'] = i
                result['task_arn'] = i['ReplicationTaskArn']
                return True
    except (ClientError, IndexError):
        return False

    return False


def task_update_waiter(client, module):
    try:
        task_ready = False
        while task_ready is False:
            time.sleep(5)
            status_check = client.describe_replication_tasks()
            for i in status_check['ReplicationTasks']:
                if i['ReplicationTaskIdentifier'] == module.params.get('name'):
                    if i['ReplicationInstanceStatus'] == 'ready':
                        instance_ready = True
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed while waiting on replication task status")


def task_delete_waiter(client, module):
    try:
        task_deleted = False
        while task_deleted is False:
            time.sleep(5)
            status_check = client.describe_replication_tasks()
            for i in status_check['ReplicationTasks']:
                if i['ReplicationTaskIdentifier'] == module.params.get('name'):
                    task_deleted = False
                else:
                    task_deleted = True
            if not status_check['ReplicationTasks']:
                instance_deleted = True
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed while waiting on replication task status")


def create_task(client, module, params, result):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.create_replication_task(**params)
        task_update_waiter(client, module)
        result['task_arn'] = response['ReplicationTask']['ReplicationTaskArn']
        result['changed'] = True
        return result
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to create replication task")

    return result


def update_task(client, module, params, result):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        del params['SourceEndpointArn']
        del params['TargetEndpointArn']
        del params['ReplicationInstanceArn']
        if 'Tags' in params:
            del params['Tags']

        param_changed = []
        param_keys = list(params.keys())
        current_keys = list(result['current_config'].keys())
        common_keys = set(param_keys) - (set(param_keys) - set(current_keys))
        for key in common_keys:
            if (params[key] != result['current_config'][key]):
                param_changed.append(True)
            else:
                param_changed.append(False)

        params['ReplicationTaskArn'] = result['task_arn']
        del result['current_config']

        if any(param_changed):
            response = client.modify_replication_task(**params)
            task_update_waiter(client, module)
            result['changed'] = True
            return result
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to update replication task")

    return result


def delete_task(client, module, result):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.delete_replication_task(
            ReplicationTaskArn=result['task_arn']
        )
        task_delete_waiter(client, module)
        del result['current_config']
        result['changed'] = True
        return result
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to delete replication task")

    return result


def main():
    module = AnsibleAWSModule(
        argument_spec={
            'name': dict(type='str', required=True),
            'state': dict(type='str', choices=['present', 'absent'], default='present'),
            'source_endpoint': dict(type='str', required=True),
            'target_endpoint': dict(type='str', required=True),
            'replication_instance': dict(type='str', required=True),
            'migration_type': dict(type='str', choices=['full-load', 'cdc', 'full-load-and-cdc'], default='full-load'),
            'table_mappings': dict(type='str', required=True),
            'settings': dict(type='str'),
            'cdc_start_time': dict(type='datetime'),
            'cdc_start_position': dict(type='str'),
            'cdc_stop_position': dict(type='str'),
            'tags': dict(type='list'),
        },
        supports_check_mode=True,
    )

    result = {
        'changed': False
    }

    params = {}
    params['ReplicationTaskIdentifier'] = module.params.get('name')
    params['SourceEndpointArn'] = module.params.get('source_endpoint')
    params['TargetEndpointArn'] = module.params.get('target_endpoint')
    params['ReplicationInstanceArn'] = module.params.get('replication_instance')
    if module.params.get('migration_type'):
        params['MigrationType'] = module.params.get('migration_type')
    params['TableMappings'] = module.params.get('table_mappings')
    if module.params.get('settings'):
        params['ReplicationTaskSettings'] = module.params.get('settings')
    if module.params.get('cdc_start_time'):
        params['CdcStartTime'] = module.params.get('cdc_start_time')
    if module.params.get('cdc_start_position'):
        params['CdcStartPosition'] = module.params.get('cdc_start_position')
    if module.params.get('cdc_stop_position'):
        params['CdcStopPosition'] = module.params.get('cdc_stop_position')
    if module.params.get('tags'):
        params['Tags'] = module.params.get('tags')

    client = module.client('dms')

    task_status = task_exists(client, module, result)

    desired_state = module.params.get('state')

    if desired_state == 'present':
        if not task_status:
            create_task(client, module, params, result)
        if task_status:
            update_task(client, module, params, result)

    if desired_state == 'absent':
        if task_status:
            delete_task(client, module, result)

    if 'task_arn' in result:
        output = result['task_arn']
    else:
        output = ''

    module.exit_json(changed=result['changed'], task_arn=output)


if __name__ == '__main__':
    main()

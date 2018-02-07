#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cloudwatchlogs_log_group
short_description: create or delete log_group in CloudWatchLogs
notes:
    - for details of the parameters and returns see U(http://boto3.readthedocs.io/en/latest/reference/services/logs.html)
description:
    - Create or delete log_group in CloudWatchLogs.
version_added: "2.5"
author:
    - Willian Ricardo(@willricardo) <willricardo@gmail.com>
requirements: [ json, botocore, boto3 ]
options:
    state:
      description:
        - Whether the rule is present, absent or get
      choices: ["present", "absent"]
      default: present
      required: false
    log_group_name:
      description:
        - The name of the log group.
      required: true
    kms_key_id:
      description:
        - The Amazon Resource Name (ARN) of the CMK to use when encrypting log data.
      required: false
    tags:
      description:
        - The key-value pairs to use for the tags.
      required: false
    retention:
      description:
        - "The number of days to retain the log events in the specified log group.
           Valid values are: [1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653]"
      required: false
    overwrite:
     description:
        - Whether an existing log group should be overwritten on create.
     default: false
     required: false
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- cloudwatchlogs_log_group:
    log_group_name: test-log-group

- cloudwatchlogs_log_group:
    state: present
    log_group_name: test-log-group
    tags: { "Name": "test-log-group", "Env" : "QA" }

- cloudwatchlogs_log_group:
    state: present
    log_group_name: test-log-group
    tags: { "Name": "test-log-group", "Env" : "QA" }
    kms_key_id: arn:aws:kms:region:account-id:key/key-id

- cloudwatchlogs_log_group:
    state: absent
    log_group_name: test-log-group

'''

RETURN = '''
log_groups:
    description: Return the list of complex objetcs representing log groups
    returned: success
    type: complex
    contains:
        log_group_name:
            description: The name of the log group.
            returned: always
            type: string
        creation_time:
            description: The creation time of the log group.
            returned: always
            type: integer
        retention_in_days:
            description: The number of days to retain the log events in the specified log group.
            returned: always
            type: integer
        metric_filter_count:
            description: The number of metric filters.
            returned: always
            type: integer
        arn:
            description: The Amazon Resource Name (ARN) of the log group.
            returned: always
            type: string
        stored_bytes:
            description: The number of bytes stored.
            returned: always
            type: string
        kms_key_id:
            description: The Amazon Resource Name (ARN) of the CMK to use when encrypting log data.
            returned: always
            type: string
'''

import traceback
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import HAS_BOTO3, camel_dict_to_snake_dict, boto3_conn, ec2_argument_spec, get_aws_connection_info

try:
    import botocore
except ImportError:
    pass  # will be detected by imported HAS_BOTO3


def create_log_group(client, log_group_name, kms_key_id, tags, retention, module):
    request = {'logGroupName': log_group_name}
    if kms_key_id:
        request['kmsKeyId'] = kms_key_id
    if tags:
        request['tags'] = tags

    try:
        client.create_log_group(**request)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Unable to create log group: {0}".format(to_native(e)),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Unable to create log group: {0}".format(to_native(e)),
                         exception=traceback.format_exc())

    if retention:
        input_retention_policy(client=client,
                               log_group_name=log_group_name,
                               retention=retention, module=module)

    desc_log_group = describe_log_group(client=client,
                                        log_group_name=log_group_name,
                                        module=module)

    if 'logGroups' in desc_log_group:
        for i in desc_log_group['logGroups']:
            if log_group_name == i['logGroupName']:
                return i
    module.fail_json(msg="The aws CloudWatchLogs log group was not created. \n please try again!")


def input_retention_policy(client, log_group_name, retention, module):
    try:
        permited_values = [1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653]

        if retention in permited_values:
            response = client.put_retention_policy(logGroupName=log_group_name,
                                                   retentionInDays=retention)
        else:
            delete_log_group(client=client, log_group_name=log_group_name, module=module)
            module.fail_json(msg="Invalid retention value. Valid values are: [1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653]")
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Unable to put retention policy for log group {0}: {1}".format(log_group_name, to_native(e)),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Unable to put retention policy for log group {0}: {1}".format(log_group_name, to_native(e)),
                         exception=traceback.format_exc())


def delete_log_group(client, log_group_name, module):
    desc_log_group = describe_log_group(client=client,
                                        log_group_name=log_group_name,
                                        module=module)

    try:
        if 'logGroups' in desc_log_group:
            for i in desc_log_group['logGroups']:
                if log_group_name == i['logGroupName']:
                    client.delete_log_group(logGroupName=log_group_name)

    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Unable to delete log group {0}: {1}".format(log_group_name, to_native(e)),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Unable to delete log group {0}: {1}".format(log_group_name, to_native(e)),
                         exception=traceback.format_exc())


def describe_log_group(client, log_group_name, module):
    try:
        desc_log_group = client.describe_log_groups(logGroupNamePrefix=log_group_name)
        return desc_log_group
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Unable to describe log group {0}: {1}".format(log_group_name, to_native(e)),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Unable to describe log group {0}: {1}".format(log_group_name, to_native(e)),
                         exception=traceback.format_exc())


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        log_group_name=dict(required=True, type='str'),
        state=dict(choices=['present', 'absent'],
                   default='present'),
        kms_key_id=dict(required=False, type='str'),
        tags=dict(required=False, type='dict'),
        retention=dict(required=False, type='int'),
        overwrite=dict(required=False, type='bool', default=False)
    ))

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required.')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    logs = boto3_conn(module, conn_type='client', resource='logs', region=region, endpoint=ec2_url, **aws_connect_kwargs)

    state = module.params.get('state')
    changed = False

    # Determine if the log group exists
    desc_log_group = describe_log_group(client=logs, log_group_name=module.params['log_group_name'], module=module)
    found_log_group = {}
    for i in desc_log_group.get('logGroups', []):
        if module.params['log_group_name'] == i['logGroupName']:
            found_log_group = i
            break

    if state == 'present':
        if found_log_group and module.params['overwrite'] is True:
                changed = True
                delete_log_group(client=logs, log_group_name=module.params['log_group_name'], module=module)
                found_log_group = create_log_group(client=logs,
                                                   log_group_name=module.params['log_group_name'],
                                                   kms_key_id=module.params['kms_key_id'],
                                                   tags=module.params['tags'],
                                                   retention=module.params['retention'],
                                                   module=module)
        elif not found_log_group:
            changed = True
            found_log_group = create_log_group(client=logs,
                                               log_group_name=module.params['log_group_name'],
                                               kms_key_id=module.params['kms_key_id'],
                                               tags=module.params['tags'],
                                               retention=module.params['retention'],
                                               module=module)

        module.exit_json(changed=changed, **camel_dict_to_snake_dict(found_log_group))

    elif state == 'absent':
        if found_log_group:
            changed = True
            delete_log_group(client=logs,
                             log_group_name=module.params['log_group_name'],
                             module=module)

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()

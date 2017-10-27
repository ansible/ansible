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
        - Whether the rule is present or absent
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

# TODO: Disabled the RETURN as it was breaking docs building. Someone needs to
# fix this
RETURN = '''# '''

try:
    import boto3
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import _camel_to_snake, camel_dict_to_snake_dict, boto3_conn, ec2_argument_spec, get_aws_connection_info

try:
    import botocore
except ImportError:
    pass  # will be detected by imported HAS_BOTO3


def create_log_group(client, log_group_name, kms_key_id, tags):

    request = {
        'logGroupName': log_group_name
    }
    if kms_key_id:
        request['kmsKeyId'] = kms_key_id
    if tags:
        request['tags'] = tags

    client.create_log_group(**request)


def delete_log_group(client, log_group_name):
    desc_log_group = client.describe_log_groups(logGroupNamePrefix=log_group_name)

    if 'logGroups' in desc_log_group:
        for i in desc_log_group['logGroups']:
            if log_group_name in i['logGroupName']:
                client.delete_log_group(logGroupName=log_group_name)


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        log_group_name=dict(required=True, type='str'),
        state=dict(choices=['present', 'absent'],
                   default='present'),
        kms_key_id=dict(required=False, type='str'),
        tags=dict(required=False, type='dict')
    ))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required.')

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        if not region:
            module.fail_json(msg="Region must be specified as a parameter, in EC2_REGION or AWS_REGION environment variables or in boto configuration file")
        logs = boto3_conn(module, conn_type='client', resource='logs', region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except botocore.exceptions.ProfileNotFound as e:
        module.fail_json(msg=str(e))

    state = module.params.get('state')

    if state == 'present':
        create_log_group(client=logs, log_group_name=module.params['log_group_name'], kms_key_id=module.params['kms_key_id'], tags=module.params['tags'])
    elif state == 'absent':
        delete_log_group(client=logs, log_group_name=module.params['log_group_name'])
    else:
        module.fail_json(msg="Invalid state '{0}' provided".format(state))

    module.exit_json()


if __name__ == '__main__':
    main()

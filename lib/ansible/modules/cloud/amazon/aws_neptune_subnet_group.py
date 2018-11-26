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
module: aws_neptune_subnet_group
short_description: Manage database subnet groups on AWS Neptune.
description:
    - Create, modify, and destroy database subnet groups on AWS Neptune
version_added: "2.8"
requirements: [ 'botocore>=1.10.30', 'boto3' ]
author:
    - "Aaron Smith (@slapula)"
options:
  name:
    description:
    - The name for the DB subnet group.
    - This value is stored as a lowercase string.
    required: true
  state:
    description:
    - Whether the resource should be present or absent.
    default: present
    choices: ['present', 'absent']
  description:
    description:
    - The description for the DB subnet group.
    required: true
  subnet_ids:
    description:
    - The EC2 Subnet IDs for the DB subnet group.
    required: true
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = r'''
  - name: Create a new database subnet group
    aws_neptune_subnet_group:
      name: "example-subnet-group"
      state: present
      description: 'This is an example of what you can do with this module.'
      subnet_ids:
        - 'subnet-1q2w3e4r'
        - 'subnet-4r3e2w1q'
'''

RETURN = r'''
db_subnet_group_arn:
    description: The ARN of the database subnet group you just created or updated.
    returned: always
    type: string
'''

try:
    import botocore
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.aws.waiters import get_waiter


def group_exists(client, module, params):
    if module.check_mode and module.params.get('state') == 'absent':
        return {'exists': False}
    try:
        response = client.describe_db_subnet_groups(
            DBSubnetGroupName=params['DBSubnetGroupName']
        )
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'DBSubnetGroupNotFoundFault':
            return {'exists': False}
        else:
            module.fail_json_aws(e, msg="Couldn't verify existence of database subnet group")
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json_aws(e, msg="Couldn't verify existence of database subnet group")

    return {'current_config': response['DBSubnetGroups'][0], 'exists': True}


def create_group(client, module, params):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.create_db_subnet_group(**params)
        get_waiter(
            client, 'subnet_group_available'
        ).wait(
            DBSubnetGroupName=params['DBSubnetGroupName']
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't create database subnet group")

    return {'db_subnet_group_arn': response['DBSubnetGroup']['DBSubnetGroupArn'], 'changed': True}


def update_group(client, module, params, group_status):
    if module.check_mode:
        module.exit_json(changed=True)
    param_changed = []
    param_keys = list(params.keys())
    current_keys = list(group_status['current_config'].keys())
    common_keys = set(param_keys) - (set(param_keys) - set(current_keys))
    for key in common_keys:
        if (params[key] != group_status['current_config'][key]):
            param_changed.append(True)
        else:
            param_changed.append(False)

    if any(param_changed):
        try:
            response = client.modify_db_subnet_group(**params)
            get_waiter(
                client, 'subnet_group_available'
            ).wait(
                DBSubnetGroupName=params['DBSubnetGroupName']
            )
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Couldn't update database subnet group")
        return {'db_subnet_group_arn': response['DBSubnetGroup']['DBSubnetGroupArn'], 'changed': True}
    else:
        return {'db_subnet_group_arn': group_status['current_config']['DBSubnetGroupArn'], 'changed': False}


def delete_group(client, module, params):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.delete_db_subnet_group(
            DBSubnetGroupName=params['DBSubnetGroupName']
        )
        get_waiter(
            client, 'subnet_group_deleted'
        ).wait(
            DBSubnetGroupName=params['DBSubnetGroupName']
        )
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Couldn't delete database subnet group")

    return {'db_subnet_group_arn': '', 'changed': True}


def main():
    module = AnsibleAWSModule(
        argument_spec={
            'name': dict(type='str', required=True),
            'state': dict(type='str', choices=['present', 'absent'], default='present'),
            'description': dict(type='str', required=True),
            'subnet_ids': dict(type='list', required=True),
        },
        supports_check_mode=True,
    )

    if not module.botocore_at_least('1.10.30'):
        module.fail_json(msg="This module requires botocore >= 1.10.30")

    result = {
        'changed': False,
        'db_subnet_group_arn': ''
    }

    desired_state = module.params.get('state')

    params = {}
    params['DBSubnetGroupName'] = module.params.get('name')
    params['DBSubnetGroupDescription'] = module.params.get('description')
    params['SubnetIds'] = module.params.get('subnet_ids')

    client = module.client('neptune')

    group_status = group_exists(client, module, params)

    if desired_state == 'present':
        if not group_status['exists']:
            result = create_group(client, module, params)
        if group_status['exists']:
            result = update_group(client, module, params, group_status)

    if desired_state == 'absent':
        if group_status['exists']:
            result = delete_group(client, module, params)

    module.exit_json(changed=result['changed'], db_subnet_group_arn=result['db_subnet_group_arn'])


if __name__ == '__main__':
    main()

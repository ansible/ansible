#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Kamil Potrec <kamilpotrec@googlemail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
module: aws_scp
short_description: Manage AWS Service Control Policies
description:
  - Manage AWS Service Control Policies
version_added: "2.10"
author:
  - Kamil Potrec (@p0tr3c)
options:
  name:
    description:
      - Name of the service control policy
    required: true
    type: str
  state:
    description:
      - State of the service control policy
    default: present
    type: str
    choices:
      - present
      - absent
  policy:
    description:
      - JSON policy document
    type: json
  description:
    description:
      - Short description of the policy
    type: str
  policy_id:
    description:
      - Policy ID
    type: str
extends_documentation_fragment:
  - aws
  - ec2
requirements:
  - boto3
  - botocore
"""

EXAMPLES = """
- name: Create Service Control Policy
  aws_scp:
    name: AllowAll
    state: present
    description: Allow All policy
    policy: |
      {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "*",
                "Resource": "*"
            }
        ]
      }

- name: Delete Service Control Policy
  aws_scp:
    name: AllowAll
    state: absent

- name: Update Service Control Policy
  aws_scp:
    name: AllowAll
    description: Change into deny
    policy: |
      {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Deny",
                "Action": "*",
                "Resource": "*"
            }
        ]
      }
"""

RETURN = """
name:
  description: Name of the policy
  returned: always
  type: str
  sample: AllowAll
state:
  description: State of the policy
  returned: always
  type: str
  sample: present
policy:
  description: JSON policy document
  returned: sucess
  type: dict
"""

import json

try:
    import boto3
    import botocore.exceptions
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    # handled by AnsibleAWSModule
    pass

from ansible.module_utils.ec2 import AWSRetry, boto3_tag_list_to_ansible_dict, ansible_dict_to_boto3_tag_list, camel_dict_to_snake_dict, compare_policies
from ansible.module_utils.aws.core import AnsibleAWSModule, is_boto3_error_code
from ansible.module_utils._text import to_native


def aws_get_scp_by_id(client, policy_id):
    policy = client.describe_policy(PolicyId=policy_id)
    if policy is None:
        return None
    return policy['Policy']


def aws_get_scp_by_name(client, name):
    paginator = client.get_paginator('list_policies')
    for page in paginator.paginate(Filter='SERVICE_CONTROL_POLICY'):
        for policy in page['Policies']:
            if policy['Name'] == name:
                return aws_get_scp_by_id(client, policy['Id'])
    return None


def aws_get_scp(client, name):
    return aws_get_scp_by_name(client, name)


def aws_create_scp(client, name, description, policy):
    policy = client.create_policy(
        Content=policy,
        Description=description,
        Name=name,
        Type='SERVICE_CONTROL_POLICY'
    )
    return policy['Policy']


def aws_delete_scp(client, policy_id):
    client.delete_policy(PolicyId=policy_id)


def aws_update_scp(client, policy_id, new_policy):
    policy = client.update_policy(
        PolicyId=policy_id,
        Name=new_policy['Name'],
        Description=new_policy['Description'],
        Content=new_policy['Content'])
    return policy['Policy']


def aws_compare_scp(current_scp, new_scp):
    result_scp = dict(
        Name=current_scp['PolicySummary']['Name'],
        Description=current_scp['PolicySummary']['Description'],
        Content=current_scp['Content'],
        changed=False)

    if compare_policies(current_scp['Content'], new_scp['Content']):
        result_scp['Content'] = new_scp['Content']
        result_scp['changed'] = True

    if current_scp['PolicySummary']['Description'] != new_scp['Description']:
        result_scp['Description'] = new_scp['Description']
        result_scp['changed'] = True

    if current_scp['PolicySummary']['Name'] != new_scp['Name']:
        result_scp['Name'] = new_scp['Name']
        result_scp['changed'] = True

    return result_scp


def main():
    argument_spec = dict(
        policy_id=dict(type='str'),
        name=dict(type='str'),
        state=dict(default='present', choices=['absent', 'present']),
        policy=dict(type='json'),
        description=dict(type='str', default='')
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[
            ['state', 'present', ['name', 'policy']],
            ['state', 'absent', ['name']]
        ]
    )

    policy_name = module.params.get('name')
    state = module.params.get('state')
    policy_description = module.params.get('description')
    policy_id = module.params.get('policy_id')

    if module.params.get('policy') is not None:
        try:
            policy_document = json.dumps(json.loads(module.params.get('policy')))
        except json.JSONDecodeError as e:
            module.fail_json(msg="Failed to parse policy document: {0}".format(e))
    else:
        policy_document = None

    try:
        client = module.client('organizations')
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS")

    if policy_id is not None:
        try:
            policy = aws_get_scp_by_id(client, policy_id)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e)
    else:
        try:
            policy = aws_get_scp(client, policy_name)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e)

    if policy is not None:
        new_policy = aws_compare_scp(policy, dict(
            Name=policy_name,
            Description=policy_description,
            Content=policy_document))

    result = dict(
        name=policy_name,
        description=policy_description,
        policy=policy,
        changed=False,
        state=state
    )

    if module.check_mode:
        if state == "absent":
            if policy is None:
                result['changed'] = False
            else:
                result['changed'] = True
        if state == "present":
            if policy is None:
                result['changed'] = True
            else:
                if new_policy['changed']:
                    result['changed'] = True
                else:
                    result['changed'] = False
    else:
        if state == "present":
            if policy is None:
                try:
                    policy = aws_create_scp(client, policy_name, policy_description, policy_document)
                except (BotoCoreError, ClientError) as e:
                    module.fail_json_aws(e, msg="Failed to create policy")
                else:
                    result['changed'] = True
                    result['policy'] = policy
            else:
                if new_policy['changed']:
                    try:
                        policy = aws_update_scp(client, policy['PolicySummary']['Id'], new_policy)
                    except (BotoCoreError, ClientError) as e:
                        module.fail_json_aws(e, msg="Failed to update policy")
                    else:
                        result['policy'] = policy
                        result['changed'] = True
                else:
                    result['changed'] = False
        elif state == "absent":
            if policy is None:
                result['changed'] = False
            else:
                try:
                    aws_delete_scp(client, policy['PolicySummary']['Id'])
                except (BotoCoreError, ClientError) as e:
                    module.fail_json_aws(e, msg="Failed to delete policy")
                else:
                    result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()

#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Sean Summers <seansummers@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'supported_by': 'community',
    'status': ['preview']
}

DOCUMENTATION = r'''
---
module: aws_organizations_facts
short_description: Obtain facts about AWS Organizations
description:
  - Gets information about AWS Organizations
requirements: [botocore, boto3]
version_added: '2.9'
author: 'Sean Summers (@SeanSummers)'
options:
    all_facts:
        description:
          - Get all AWS Organization information
        type: bool
        required: false
        default: 'no'
    accounts:
        description:
          - Get list of accounts in the AWS Organization
        type: bool
        required: false
        default: 'no'
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = r'''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Gather facts about the organization
  aws_organizations_facts:

- name: Facts are published in ansible_facts['organizations']
  debug:
    msg: "{{ ansible_facts['organizations'] }}"

- name: Include a list of accounts in the AWS Organization
  aws_organizations_facts:
    accounts: true

- name: Facts are published in ansible_facts['organizations']
  debug:
    msg: "{{ ansible_facts['organizations'] }}"
'''

RETURN = r'''
organizations:
  description: AWS Organization Facts.
  returned: success
  type: dict
  sample:
    id: o-abcde01234
    arn: arn:aws:organizations::123456789012:organization/o-abcde01234
    feature_set: ALL
    master_account_arn: arn:aws:organizations::123456789012:account/o-abcde01234/123456789012
    master_account_id: 123456789012
    master_account_email: mailbox@example.com
    available_policy_types:
      - Type: SERVICE_CONTROL_POLICY
        Status: ENABLED
    accounts:
      returned: success
      type: list
      sample:
        - arn: arn:aws:organizations::210987654321:account/o-abcde01234/210987654321
          email: mailbox+account@example.com
          id: '210987654321'
          joined_method: CREATED
          joined_timestamp: 2019-01-01 16:33:33.333000
          name: Another AWS Account
          status: ACTIVE
        - arn: arn:aws:organizations::123456789012:account/o-abcde01234/123456789012
          email: mailbox@example.com
          id: '123456789012'
          joined_method: CREATED
          joined_timestamp: 2018-01-01 15:22:22.222000
          name: Master AWS Account
          status: ACTIVE
'''
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (AWSRetry, camel_dict_to_snake_dict)

from botocore.exceptions import (BotoCoreError, ClientError)


def describe_organization(client, aws_retry=True):
    return client.describe_organization(aws_retry=aws_retry)['Organization']


def list_accounts(client):
    paginator = client.get_paginator('list_accounts')
    return paginator.paginate().build_full_result()['Accounts']


def main():
    argument_spec = dict(all_facts=dict(type='bool',
                                        required=False,
                                        default=False),
                         accounts=dict(type='bool',
                                       required=False,
                                       default=False))
    module = AnsibleAWSModule(argument_spec=argument_spec,
                              supports_check_mode=True)

    client = module.client('organizations',
                           retry_decorator=AWSRetry.jittered_backoff(
                               retries=10, delay=3, max_delay=30))

    result = {'ansible_facts': {}}

    try:
        organizations = describe_organization(client)
        result['ansible_facts']['organizations'] = camel_dict_to_snake_dict(
            organizations)

        # Optional outputs
        all_facts = module.params.get('all_facts')
        if all_facts or module.params.get('accounts'):
            accounts = (camel_dict_to_snake_dict(dummy)
                        for dummy in list_accounts(client))
            result['ansible_facts']['organizations']['accounts'] = tuple(
                accounts)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e)

    result['changed'] = False
    module.exit_json(**result)


if __name__ == '__main__':
    main()

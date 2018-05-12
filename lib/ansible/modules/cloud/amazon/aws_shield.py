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
module: aws_shield
short_description: Enable/Disable AWS Shield Advanced protection.
description:
    - Enable/Disable AWS Shield Advanced protection on a given resource.
author: "Aaron Smith (@slapula)"
version_added: "2.6"
requirements: [ 'botocore', 'boto3' ]
options:
  name:
    description:
    - Friendly name for the protection you are creating.
    required: true
  state:
    description:
    - Whether the protection should be exist or not.
    required: true
    choices: ['present', 'absent']
  resource:
    description:
    - The ARN of the resource to be protected.
    - Valid resources can be Elastic IP allocations, Elastic and Application Load Balancers, Cloudfront distributions,
      or Route 53 hosted zones.
    required: true
extends_documentation_fragment:
    - ec2
    - aws
notes:
  - AWS Shield Advanced protection requires a 1-year subscription.
  - See AWS documentation for details `https://aws.amazon.com/shield/`
'''


EXAMPLES = r'''
- name: add AWS Shield protection to an ELB
  aws_shield:
    name: 'shield_test'
    state: present
    resource: 'arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/my-load-balancer'

- name: remove AWS Shield protection from an ELB
  aws_shield:
    name: 'shield_test'
    state: absent
    resource: 'arn:aws:elasticloadbalancing:us-east-1:123456789012:loadbalancer/my-load-balancer'
'''


RETURN = r'''
protection_id:
    description: The unique identifier (ID) for the Protection object that is created.
    returned: changed
    type: string
'''

import os

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, AWSRetry
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, boto3_tag_list_to_ansible_dict

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # handled by AnsibleAWSModule


def subscription_exists(client, module):
    if module.check_mode:
        return
    try:
        response = client.get_subscription_state()
        if response['SubscriptionState'] == 'INACTIVE':
            module.fail_json_aws(msg="AWS Shield Advanced subscription is not active. Please activate it before using this module.")
    except (ClientError, IndexError) as e:
        module.fail_json_aws(e, msg="Couldn't verify AWS Shield Advanced subscription state.")


def shield_exists(client, module, result):
    if module.check_mode and module.params.get('state') == 'absent':
        return True
    try:
        response = client.list_protections()
        for i in response['Protections']:
            if i['Name'] == module.params.get('name'):
                result['protection_id'] = i['Id']
                return True
    except (ClientError, IndexError):
        return False

    return False


def create_shield(client, module, result):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.create_protection(
            Name=module.params.get('name'),
            ResourceArn=module.params.get('resource')
        )
        result['protection_id'] = response['ProtectionId']
        result['changed'] = True
        return result
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to create AWS Shield protection")


def delete_shield(client, module, result):
    if module.check_mode:
        module.exit_json(changed=True)
    try:
        response = client.delete_protection(
            ProtectionId=result['protection_id']
        )
        result['changed'] = True
        return result
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Failed to delete AWS Shield protection")


def main():
    module = AnsibleAWSModule(
        argument_spec={
            'name': dict(type='str', required=True),
            'state': dict(type='str', choices=['present', 'absent'], required=True),
            'resource': dict(type='str', required=True),
        },
        supports_check_mode=True,
    )

    result = {
        'changed': False
    }

    desired_state = module.params.get('state')

    client = module.client('shield')

    subscription_exists(client, module)

    shield_status = shield_exists(client, module, result)

    if desired_state == 'present':
        if not shield_status:
            create_shield(client, module, result)

    if desired_state == 'absent':
        if shield_status:
            delete_shield(client, module, result)

    module.exit_json(changed=result['changed'], results=result)


if __name__ == '__main__':
    main()

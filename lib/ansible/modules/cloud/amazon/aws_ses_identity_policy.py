#!/usr/bin/python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: aws_ses_identity_policy
short_description: Manages SES sending authorization policies
description:
    - This module allows the user to manage sending authorization policies associated with an SES identity (email or domain).
    - SES authorization sending policies can be used to control what actors are able to send email
      on behalf of the validated identity and what conditions must be met by the sent emails.
version_added: "2.6"
author: Ed Costello    (@orthanc)

options:
    identity:
        description: |
            The SES identity to attach or remove a policy from. This can be either the full ARN or just
            the verified email or domain.
        required: true
    policy_name:
        description: The name used to identify the policy within the scope of the identity it's attached to.
        required: true
    policy:
        description: A properly formatted JSON sending authorization policy. Required when I(state=present).
    state:
        description: Whether to create(or update) or delete the authorization policy on the identity.
        default: present
        choices: [ 'present', 'absent' ]
requirements: [ 'botocore', 'boto3' ]
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: add sending authorization policy to domain identity
  aws_ses_identity_policy:
    identity: example.com
    policy_name: ExamplePolicy
    policy: "{{ lookup('template', 'policy.json.j2') }}"
    state: present

- name: add sending authorization policy to email identity
  aws_ses_identity_policy:
    identity: example@example.com
    policy_name: ExamplePolicy
    policy: "{{ lookup('template', 'policy.json.j2') }}"
    state: present

- name: add sending authorization policy to identity using ARN
  aws_ses_identity_policy:
    identity: "arn:aws:ses:us-east-1:12345678:identity/example.com"
    policy_name: ExamplePolicy
    policy: "{{ lookup('template', 'policy.json.j2') }}"
    state: present

- name: remove sending authorization policy
  aws_ses_identity_policy:
    identity: example.com
    policy_name: ExamplePolicy
    state: absent
'''

RETURN = '''
policies:
    description: A list of all policies present on the identity after the operation.
    returned: success
    type: list
    sample: [ExamplePolicy]
'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import compare_policies, AWSRetry

import json

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass  # caught by imported HAS_BOTO3


def get_identity_policy(connection, module, identity, policy_name):
    try:
        response = connection.get_identity_policies(Identity=identity, PolicyNames=[policy_name], aws_retry=True)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Failed to retrieve identity policy {policy}'.format(policy=policy_name))
    policies = response['Policies']
    if policy_name in policies:
        return policies[policy_name]
    return None


def create_or_update_identity_policy(connection, module):
    identity = module.params.get('identity')
    policy_name = module.params.get('policy_name')
    required_policy = module.params.get('policy')
    required_policy_dict = json.loads(required_policy)

    changed = False
    policy = get_identity_policy(connection, module, identity, policy_name)
    policy_dict = json.loads(policy) if policy else None
    if compare_policies(policy_dict, required_policy_dict):
        changed = True
        try:
            if not module.check_mode:
                connection.put_identity_policy(Identity=identity, PolicyName=policy_name, Policy=required_policy, aws_retry=True)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg='Failed to put identity policy {policy}'.format(policy=policy_name))

    # Load the list of applied policies to include in the response.
    # In principle we should be able to just return the response, but given
    # eventual consistency behaviours in AWS it's plausible that we could
    # end up with a list that doesn't contain the policy we just added.
    # So out of paranoia check for this case and if we're missing the policy
    # just make sure it's present.
    #
    # As a nice side benefit this also means the return is correct in check mode
    try:
        policies_present = connection.list_identity_policies(Identity=identity, aws_retry=True)['PolicyNames']
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Failed to list identity policies')
    if policy_name is not None and policy_name not in policies_present:
        policies_present = list(policies_present)
        policies_present.append(policy_name)
    module.exit_json(
        changed=changed,
        policies=policies_present,
    )


def delete_identity_policy(connection, module):
    identity = module.params.get('identity')
    policy_name = module.params.get('policy_name')

    changed = False
    try:
        policies_present = connection.list_identity_policies(Identity=identity, aws_retry=True)['PolicyNames']
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg='Failed to list identity policies')
    if policy_name in policies_present:
        try:
            if not module.check_mode:
                connection.delete_identity_policy(Identity=identity, PolicyName=policy_name, aws_retry=True)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg='Failed to delete identity policy {policy}'.format(policy=policy_name))
        changed = True
        policies_present = list(policies_present)
        policies_present.remove(policy_name)

    module.exit_json(
        changed=changed,
        policies=policies_present,
    )


def main():
    module = AnsibleAWSModule(
        argument_spec={
            'identity': dict(required=True, type='str'),
            'state': dict(default='present', choices=['present', 'absent']),
            'policy_name': dict(required=True, type='str'),
            'policy': dict(type='json', default=None),
        },
        required_if=[['state', 'present', ['policy']]],
        supports_check_mode=True,
    )

    # SES APIs seem to have a much lower throttling threshold than most of the rest of the AWS APIs.
    # Docs say 1 call per second. This shouldn't actually be a big problem for normal usage, but
    # the ansible build runs multiple instances of the test in parallel that's caused throttling
    # failures so apply a jittered backoff to call SES calls.
    connection = module.client('ses', retry_decorator=AWSRetry.jittered_backoff())

    state = module.params.get("state")

    if state == 'present':
        create_or_update_identity_policy(connection, module)
    else:
        delete_identity_policy(connection, module)


if __name__ == '__main__':
    main()

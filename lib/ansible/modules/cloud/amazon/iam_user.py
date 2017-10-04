#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: iam_user
short_description: Manage AWS IAM users
description:
  - Manage AWS IAM users
version_added: "2.5"
author: Josh Souza, @joshsouza
options:
  name:
    description:
      - The name of the user to create.
    required: true
  managed_policy:
    description:
      - A list of managed policy ARNs or friendly names to attach to the user. To embed an inline policy, use M(iam_policy).
    required: false
  state:
    description:
      - Create or remove the IAM user
    required: true
    choices: [ 'present', 'absent' ]
  purge_policy:
    description:
      - Detach policies which are not included in managed_policy list
    required: false
    default: false
requirements: [ botocore, boto3 ]
extends_documentation_fragment:
  - aws
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.
# Note: This module does not allow management of groups that users belong to.
#       Groups should manage their membership directly using `iam_group`,
#       as users belong to them.

# Create a user
- iam_user:
    name: testuser1
    state: present

# Create a user and attach a managed policy using its ARN
- iam_user:
    name: testuser1
    managed_policy:
      - arn:aws:iam::aws:policy/AmazonSNSFullAccess
    state: present

# Remove all managed policies from an existing user with an empty list
- iam_user:
    name: testuser1
    state: present
    purge_policy: true

# Delete the user
- iam_user:
    name: testuser1
    state: absent

'''
RETURN = '''
user:
    description: dictionary containing all the user information
    returned: success
    type: complex
    contains:
        arn:
            description: the Amazon Resource Name (ARN) specifying the user
            type: string
            sample: "arn:aws:iam::1234567890:user/testuser1"
        create_date:
            description: the date and time, in ISO 8601 date-time format, when the user was created
            type: string
            sample: "2017-02-08T04:36:28+00:00"
        user_id:
            description: the stable and unique string identifying the user
            type: string
            sample: AGPAIDBWE12NSFINE55TM
        user_name:
            description: the friendly name that identifies the user
            type: string
            sample: testuser1
        path:
            description: the path to the user
            type: string
            sample: /
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, ec2_argument_spec, get_aws_connection_info, boto3_conn
from ansible.module_utils.ec2 import HAS_BOTO3

import traceback

try:
    from botocore.exceptions import ClientError, ParamValidationError
except ImportError:
    pass  # caught by imported HAS_BOTO3


def compare_attached_policies(current_attached_policies, new_attached_policies):

    # If new_attached_policies is None it means we want to remove all policies
    if len(current_attached_policies) > 0 and new_attached_policies is None:
        return False

    current_attached_policies_arn_list = []
    for policy in current_attached_policies:
        current_attached_policies_arn_list.append(policy['PolicyArn'])

    if not set(current_attached_policies_arn_list).symmetric_difference(set(new_attached_policies)):
        return True
    else:
        return False


def convert_friendly_names_to_arns(connection, module, policy_names):

    # List comprehension that looks for any policy in the 'policy_names' list
    # that does not begin with 'arn'. If there aren't any, short circuit.
    # If there are, translate friendly name to the full arn
    if not any([not policy.startswith('arn:') for policy in policy_names if policy is not None]):
        return policy_names
    allpolicies = {}
    paginator = connection.get_paginator('list_policies')
    policies = paginator.paginate().build_full_result()['Policies']

    for policy in policies:
        allpolicies[policy['PolicyName']] = policy['Arn']
        allpolicies[policy['Arn']] = policy['Arn']
    try:
        return [allpolicies[policy] for policy in policy_names]
    except KeyError as e:
        module.fail_json(msg="Couldn't find policy: " + str(e))


def create_or_update_user(connection, module):

    params = dict()
    params['UserName'] = module.params.get('name')
    managed_policies = module.params.get('managed_policy')
    purge_policy = module.params.get('purge_policy')
    changed = False
    if managed_policies:
        managed_policies = convert_friendly_names_to_arns(connection, module, managed_policies)

    # Get user
    user = get_user(connection, module, params['UserName'])

    # If user is None, create it
    if user is None:
        # Check mode means we would create the user
        if module.check_mode:
            module.exit_json(changed=True)

        try:
            user = connection.create_user(**params)
            changed = True
        except ClientError as e:
            module.fail_json(msg=e.message, exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))
        except ParamValidationError as e:
            module.fail_json(msg=e.message, exception=traceback.format_exc())

    # Manage managed policies
    current_attached_policies = get_attached_policy_list(connection, module, params['UserName'])
    if not compare_attached_policies(current_attached_policies, managed_policies):
        current_attached_policies_arn_list = []
        for policy in current_attached_policies:
            current_attached_policies_arn_list.append(policy['PolicyArn'])

        # If managed_policies has a single empty element we want to remove all attached policies
        if purge_policy:
            # Detach policies not present
            for policy_arn in list(set(current_attached_policies_arn_list) - set(managed_policies)):
                changed = True
                if not module.check_mode:
                    try:
                        connection.detach_user_policy(UserName=params['UserName'], PolicyArn=policy_arn)
                    except ClientError as e:
                        module.fail_json(msg=e.message, exception=traceback.format_exc(),
                                         **camel_dict_to_snake_dict(e.response))
                    except ParamValidationError as e:
                        module.fail_json(msg=e.message, exception=traceback.format_exc())

        # If there are policies to adjust that aren't in the current list, then things have changed
        # Otherwise the only changes were in purging above
        if set(managed_policies).difference(set(current_attached_policies_arn_list)):
            changed = True
            # If there are policies in managed_policies attach each policy
            if managed_policies != [None] and not module.check_mode:
                for policy_arn in managed_policies:
                    try:
                        connection.attach_user_policy(UserName=params['UserName'], PolicyArn=policy_arn)
                    except ClientError as e:
                        module.fail_json(msg=e.message, exception=traceback.format_exc(),
                                         **camel_dict_to_snake_dict(e.response))
                    except ParamValidationError as e:
                        module.fail_json(msg=e.message, exception=traceback.format_exc())
    if module.check_mode:
        module.exit_json(changed=changed)

    # Get the user again
    user = get_user(connection, module, params['UserName'])

    module.exit_json(changed=changed, iam_user=camel_dict_to_snake_dict(user))


def destroy_user(connection, module):

    params = dict()
    params['UserName'] = module.params.get('name')

    if get_user(connection, module, params['UserName']):
        # Check mode means we would remove this user
        if module.check_mode:
            module.exit_json(changed=True)

        # Remove any attached policies otherwise deletion fails
        try:
            for policy in get_attached_policy_list(connection, module, params['UserName']):
                connection.detach_user_policy(UserName=params['UserName'], PolicyArn=policy['PolicyArn'])
        except ClientError as e:
            module.fail_json(msg=e.message, exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))
        except ParamValidationError as e:
            module.fail_json(msg=e.message, exception=traceback.format_exc())

        try:
            connection.delete_user(**params)
        except ClientError as e:
            module.fail_json(msg=e.message, exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))
        except ParamValidationError as e:
            module.fail_json(msg=e.message, exception=traceback.format_exc())

    else:
        module.exit_json(changed=False)

    module.exit_json(changed=True)


def get_user(connection, module, name):

    params = dict()
    params['UserName'] = name

    try:
        return connection.get_user(**params)
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            return None
        else:
            module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))


def get_attached_policy_list(connection, module, name):

    try:
        return connection.list_attached_user_policies(UserName=name)['AttachedPolicies']
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            return None
        else:
            module.fail_json(msg=e.message, **camel_dict_to_snake_dict(e.response))


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True, type='str'),
            managed_policy=dict(default=[], type='list'),
            state=dict(choices=['present', 'absent'], required=True),
            purge_policy=dict(default=False, type='bool')
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )
    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    connection = boto3_conn(module, conn_type='client', resource='iam', region=region, endpoint=ec2_url, **aws_connect_params)

    state = module.params.get("state")

    if state == 'present':
        create_or_update_user(connection, module)
    else:
        destroy_user(connection, module)


if __name__ == '__main__':
    main()

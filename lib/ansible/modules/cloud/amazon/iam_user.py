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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: iam_user
short_description: Manage AWS IAM users
description:
  - Manage AWS IAM roles
version_added: "2.4"
author: Maksym Postument, @infectsoldier
options:
  name:
    description:
      - The name of the user.
    required: true
  password:
    description:
      - The password of the user.
  path:
    description:
      - The path to the user. For more information about paths, see U(http://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html).
    required: false
    default: "/"
  managed_policy:
    description:
      - A list of managed policy ARNs or friendly names to attach to the role. To embed an inline policy, use M(iam_policy).
    required: true
  groups:
    description:
      -List of groups which should be assigned to user
    required: false
  state:
    description:
      - Create or remove the IAM user.
    required: true
    choices: [ 'present', 'absent' ]
  purge_policy:
    description:
      - Deatach policy which not included in managed_policy list
    required: false
    default: false
  purge_users:
    description:
      - Deatach users which not included in users list
    required: false
    default: false
requirements: [ botocore, boto3 ]
extends_documentation_fragment:
  - aws
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.
# Create a user
- iam_user:
    name: test_user1
    state: present
# Create a user and attach a managed policy called "ReadOnlyAccess"
- iam_user:
    name:  test_user1
    state: present
    managed_policy:
      - arn:aws:iam::aws:policy/ReadOnlyAccess
# Keep the user created above but remove all managed policies
- iam_user:
    name: test_user1
    state: present
    purge_policy: true
# Delete the user
- iam_user:
    name: test_user1
    state: absent
# Keep the user created above but remove all groups
- iam_user:
    name: test_user1
    state: present
    purge_groups: true
'''
RETURN = '''
iam_user:
    description: dictionary containing all the user information
    returned: success
    type: dictionary
    contains:
        arn:
            description: the Amazon Resource Name (ARN) specifying the user
            type: string
            sample: "arn:aws:iam::1111111111:user/asdasds"
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
            sample: testgroup1
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


def compare_attached_user_policies(current_attached_policies, new_attached_policies):

    # If new_attached_policies is None it means we want to remove all policies
    if len(current_attached_policies) > 0 and new_attached_policies is None:
        return False

    current_attached_policies_arn_list = []
    for policy in current_attached_policies:
        current_attached_policies_arn_list.append(policy['PolicyArn'])

    if set(current_attached_policies_arn_list) == set(new_attached_policies):
        return True
    else:
        return False


def compare_group_members(current_group_members, new_group_members):

    # If new_attached_policies is None it means we want to remove all policies
    if len(current_group_members) > 0 and new_group_members is None:
        return False

    if set(current_group_members) == set(new_group_members):
        return True
    else:
        return False


def create_or_update_user(connection, module):

    params = dict()
    params['UserName'] = module.params.get('name')
    params['Path'] = module.params.get('path')
    managed_policies = module.params.get('managed_policy')
    groups = module.params.get('groups')
    purge_policy = module.params.get('purge_policy')
    purge_groups = module.params.get('purge_groups')
    changed = False

    # Get role
    user = get_user(connection, module, params['UserName'])

    # If user is None, create it
    if user is None:
        try:
            user = connection.create_user(**params)
            changed = True
        except ClientError as e:
            module.fail_json(msg=e.message, exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))
        except ParamValidationError as e:
            module.fail_json(msg=e.message, exception=traceback.format_exc())

        # Check attached managed policies
    current_attached_policies = get_attached_policy_list(connection, module, params['UserName'])

    if not compare_attached_user_policies(current_attached_policies, managed_policies):
        # If managed_policies has a single empty element we want to remove all attached policies
        if purge_policy:
            # Detach policies not present
            current_attached_policies_arn_list = []
            for policy in current_attached_policies:
                current_attached_policies_arn_list.append(policy['PolicyArn'])

            for policy_arn in list(set(current_attached_policies_arn_list) - set(managed_policies)):
                try:
                    connection.detach_user_policy(UserName=params['UserName'], PolicyArn=policy_arn)
                except ClientError as e:
                    module.fail_json(msg=e.message, exception=traceback.format_exc(),
                                     **camel_dict_to_snake_dict(e.response))
                except ParamValidationError as e:
                    module.fail_json(msg=e.message, exception=traceback.format_exc())
    # Attach each policy
        if managed_policies != [None]:
            for policy_arn in managed_policies:
                try:
                    connection.attach_user_policy(UserName=params['UserName'], PolicyArn=policy_arn)
                except ClientError as e:
                    module.fail_json(msg=e.message, exception=traceback.format_exc(),
                                     **camel_dict_to_snake_dict(e.response))
                except ParamValidationError as e:
                    module.fail_json(msg=e.message, exception=traceback.format_exc())

        changed = True

    current_group_members = get_group(connection, module, params['UserName'])
    current_group_members_list = []
    for member in current_group_members:
        current_group_members_list.append(member['GroupName'])

    if not compare_group_members(current_group_members_list, groups):
        if purge_groups:
            for group in list(set(current_group_members_list) - set(groups)):
                try:
                    connection.remove_user_from_group(GroupName=group, UserName=params['UserName'])
                except ClientError as e:
                    module.fail_json(msg=e.message, exception=traceback.format_exc(),
                                     **camel_dict_to_snake_dict(e.response))
                except ParamValidationError as e:
                    module.fail_json(msg=e.message, exception=traceback.format_exc())

        if groups != [None]:
            for group in groups:
                try:
                    connection.add_user_to_group(GroupName=group, UserName=params['UserName'])
                except ClientError as e:
                    module.fail_json(msg=e.message, exception=traceback.format_exc(),
                                     **camel_dict_to_snake_dict(e.response))
                except ParamValidationError as e:
                    module.fail_json(msg=e.message, exception=traceback.format_exc())

        changed = True

    user = get_user(connection, module, params['UserName'])
    module.exit_json(changed=changed, iam_user=camel_dict_to_snake_dict(user))


def destroy_user(connection, module):

    params = dict()
    params['UserName'] = module.params.get('name')

    if get_user(connection, module, params['UserName']):

        # Remove any attached policies otherwise deletion fails
        try:
            for policy in get_attached_policy_list(connection, module, params['UserName']):
                connection.detach_user_policy(UserName=params['UserName'], PolicyArn=policy['PolicyArn'])
        except ClientError as e:
            module.fail_json(msg=e.message, exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))
        except ParamValidationError as e:
            module.fail_json(msg=e.message, exception=traceback.format_exc())

        # Remove any groups otherwise deletion fails
        current_group_members = get_group(connection, module, params['UserName'])
        current_group_members_list = []
        for member in current_group_members:
            current_group_members_list.append(member['GroupName'])
        for group in current_group_members_list:
            try:
                connection.remove_user_from_group(GroupName=group, UserName=params['UserName'])
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
        return connection.get_user(**params)['User']
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


def get_group(connection, module, name):

    try:
        return connection.list_groups_for_user(UserName=name)['Groups']
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
            path=dict(default="/", required=False, type='str'),
            managed_policy=dict(default=[], type='list'),
            groups=dict(default=[], type='list'),
            state=dict(default=None, choices=['present', 'absent'], required=True),
            purge_policy=dict(default=False, type='bool'),
            purge_groups=dict(default=False, type='bool')
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
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

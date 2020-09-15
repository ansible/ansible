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

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: iam_group
short_description: Manage AWS IAM groups
description:
  - Manage AWS IAM groups
version_added: "2.4"
author:
- Nick Aslanidis (@naslanidis)
- Maksym Postument (@infectsoldier)
options:
  name:
    description:
      - The name of the group to create.
    required: true
    type: str
  managed_policy:
    description:
      - A list of managed policy ARNs or friendly names to attach to the role. To embed an inline policy, use M(iam_policy).
    required: false
    type: list
  users:
    description:
      - A list of existing users to add as members of the group.
    required: false
    type: list
  state:
    description:
      - Create or remove the IAM group
    required: true
    choices: [ 'present', 'absent' ]
    type: str
  purge_policy:
    description:
      - Detach policy which not included in managed_policy list
    required: false
    default: false
    type: bool
  purge_users:
    description:
      - Detach users which not included in users list
    required: false
    default: false
    type: bool
requirements: [ botocore, boto3 ]
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create a group
- iam_group:
    name: testgroup1
    state: present

# Create a group and attach a managed policy using its ARN
- iam_group:
    name: testgroup1
    managed_policy:
      - arn:aws:iam::aws:policy/AmazonSNSFullAccess
    state: present

# Create a group with users as members and attach a managed policy using its ARN
- iam_group:
    name: testgroup1
    managed_policy:
      - arn:aws:iam::aws:policy/AmazonSNSFullAccess
    users:
      - test_user1
      - test_user2
    state: present

# Remove all managed policies from an existing group with an empty list
- iam_group:
    name: testgroup1
    state: present
    purge_policy: true

# Remove all group members from an existing group
- iam_group:
    name: testgroup1
    managed_policy:
      - arn:aws:iam::aws:policy/AmazonSNSFullAccess
    purge_users: true
    state: present


# Delete the group
- iam_group:
    name: testgroup1
    state: absent

'''
RETURN = '''
group:
    description: dictionary containing all the group information
    returned: success
    type: complex
    contains:
        arn:
            description: the Amazon Resource Name (ARN) specifying the group
            type: str
            sample: "arn:aws:iam::1234567890:group/testgroup1"
        create_date:
            description: the date and time, in ISO 8601 date-time format, when the group was created
            type: str
            sample: "2017-02-08T04:36:28+00:00"
        group_id:
            description: the stable and unique string identifying the group
            type: str
            sample: AGPAIDBWE12NSFINE55TM
        group_name:
            description: the friendly name that identifies the group
            type: str
            sample: testgroup1
        path:
            description: the path to the group
            type: str
            sample: /
users:
    description: list containing all the group members
    returned: success
    type: complex
    contains:
        arn:
            description: the Amazon Resource Name (ARN) specifying the user
            type: str
            sample: "arn:aws:iam::1234567890:user/test_user1"
        create_date:
            description: the date and time, in ISO 8601 date-time format, when the user was created
            type: str
            sample: "2017-02-08T04:36:28+00:00"
        user_id:
            description: the stable and unique string identifying the user
            type: str
            sample: AIDAIZTPY123YQRS22YU2
        user_name:
            description: the friendly name that identifies the user
            type: str
            sample: testgroup1
        path:
            description: the path to the user
            type: str
            sample: /
'''

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict
from ansible.module_utils.ec2 import AWSRetry

try:
    from botocore.exceptions import BotoCoreError, ClientError, ParamValidationError
except ImportError:
    pass  # caught by imported HAS_BOTO3


def compare_attached_group_policies(current_attached_policies, new_attached_policies):

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


def convert_friendly_names_to_arns(connection, module, policy_names):

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


def create_or_update_group(connection, module):

    params = dict()
    params['GroupName'] = module.params.get('name')
    managed_policies = module.params.get('managed_policy')
    users = module.params.get('users')
    purge_users = module.params.get('purge_users')
    purge_policy = module.params.get('purge_policy')
    changed = False
    if managed_policies:
        managed_policies = convert_friendly_names_to_arns(connection, module, managed_policies)

    # Get group
    try:
        group = get_group(connection, module, params['GroupName'])
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Couldn't get group")

    # If group is None, create it
    if group is None:
        # Check mode means we would create the group
        if module.check_mode:
            module.exit_json(changed=True)

        try:
            group = connection.create_group(**params)
            changed = True
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Couldn't create group")

    # Manage managed policies
    current_attached_policies = get_attached_policy_list(connection, module, params['GroupName'])
    if not compare_attached_group_policies(current_attached_policies, managed_policies):
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
                        connection.detach_group_policy(GroupName=params['GroupName'], PolicyArn=policy_arn)
                    except (BotoCoreError, ClientError) as e:
                        module.fail_json_aws(e, msg="Couldn't detach policy from group %s" % params['GroupName'])
        # If there are policies to adjust that aren't in the current list, then things have changed
        # Otherwise the only changes were in purging above
        if set(managed_policies) - set(current_attached_policies_arn_list):
            changed = True
            # If there are policies in managed_policies attach each policy
            if managed_policies != [None] and not module.check_mode:
                for policy_arn in managed_policies:
                    try:
                        connection.attach_group_policy(GroupName=params['GroupName'], PolicyArn=policy_arn)
                    except (BotoCoreError, ClientError) as e:
                        module.fail_json_aws(e, msg="Couldn't attach policy to group %s" % params['GroupName'])

    # Manage group memberships
    try:
        current_group_members = get_group(connection, module, params['GroupName'])['Users']
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, "Couldn't get group %s" % params['GroupName'])

    current_group_members_list = []
    for member in current_group_members:
        current_group_members_list.append(member['UserName'])

    if not compare_group_members(current_group_members_list, users):

        if purge_users:
            for user in list(set(current_group_members_list) - set(users)):
                # Ensure we mark things have changed if any user gets purged
                changed = True
                # Skip actions for check mode
                if not module.check_mode:
                    try:
                        connection.remove_user_from_group(GroupName=params['GroupName'], UserName=user)
                    except (BotoCoreError, ClientError) as e:
                        module.fail_json_aws(e, msg="Couldn't remove user %s from group %s" % (user, params['GroupName']))
        # If there are users to adjust that aren't in the current list, then things have changed
        # Otherwise the only changes were in purging above
        if set(users) - set(current_group_members_list):
            changed = True
            # Skip actions for check mode
            if users != [None] and not module.check_mode:
                for user in users:
                    try:
                        connection.add_user_to_group(GroupName=params['GroupName'], UserName=user)
                    except (BotoCoreError, ClientError) as e:
                        module.fail_json_aws(e, msg="Couldn't add user %s to group %s" % (user, params['GroupName']))
    if module.check_mode:
        module.exit_json(changed=changed)

    # Get the group again
    try:
        group = get_group(connection, module, params['GroupName'])
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, "Couldn't get group %s" % params['GroupName'])

    module.exit_json(changed=changed, iam_group=camel_dict_to_snake_dict(group))


def destroy_group(connection, module):

    params = dict()
    params['GroupName'] = module.params.get('name')

    try:
        group = get_group(connection, module, params['GroupName'])
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, "Couldn't get group %s" % params['GroupName'])
    if group:
        # Check mode means we would remove this group
        if module.check_mode:
            module.exit_json(changed=True)

        # Remove any attached policies otherwise deletion fails
        try:
            for policy in get_attached_policy_list(connection, module, params['GroupName']):
                connection.detach_group_policy(GroupName=params['GroupName'], PolicyArn=policy['PolicyArn'])
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Couldn't remove policy from group %s" % params['GroupName'])

        # Remove any users in the group otherwise deletion fails
        current_group_members_list = []
        try:
            current_group_members = get_group(connection, module, params['GroupName'])['Users']
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, "Couldn't get group %s" % params['GroupName'])
        for member in current_group_members:
            current_group_members_list.append(member['UserName'])
        for user in current_group_members_list:
            try:
                connection.remove_user_from_group(GroupName=params['GroupName'], UserName=user)
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, "Couldn't remove user %s from group %s" % (user, params['GroupName']))

        try:
            connection.delete_group(**params)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, "Couldn't delete group %s" % params['GroupName'])

    else:
        module.exit_json(changed=False)

    module.exit_json(changed=True)


@AWSRetry.exponential_backoff()
def get_group(connection, module, name):
    try:
        paginator = connection.get_paginator('get_group')
        return paginator.paginate(GroupName=name).build_full_result()
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            return None
        else:
            raise


@AWSRetry.exponential_backoff()
def get_attached_policy_list(connection, module, name):

    try:
        paginator = connection.get_paginator('list_attached_group_policies')
        return paginator.paginate(GroupName=name).build_full_result()['AttachedPolicies']
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            return None
        else:
            raise


def main():

    argument_spec = dict(
        name=dict(required=True),
        managed_policy=dict(default=[], type='list'),
        users=dict(default=[], type='list'),
        state=dict(choices=['present', 'absent'], required=True),
        purge_users=dict(default=False, type='bool'),
        purge_policy=dict(default=False, type='bool')
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    connection = module.client('iam')

    state = module.params.get("state")

    if state == 'present':
        create_or_update_group(connection, module)
    else:
        destroy_group(connection, module)


if __name__ == '__main__':
    main()

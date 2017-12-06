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
module: iam_role
short_description: Manage AWS IAM roles
description:
  - Manage AWS IAM roles
version_added: "2.3"
author: Rob White, @wimnat
options:
  path:
    description:
      - The path to the role. For more information about paths, see U(http://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html).
    required: false
    default: "/"
  name:
    description:
      - The name of the role to create.
    required: true
  description:
    description:
      - Provide a description of the new role
    required: false
    version_added: "2.5"
  assume_role_policy_document:
    description:
      - "The trust relationship policy document that grants an entity permission to assume the role.  This parameter is required when state: present."
    required: false
  managed_policy:
    description:
      - A list of managed policy ARNs or, since Ansible 2.4, a list of either managed policy ARNs or friendly names.
        To embed an inline policy, use M(iam_policy). To remove existing policies, use an empty list item.
    required: true
    aliases: ['managed_policies']
  state:
    description:
      - Create or remove the IAM role
    required: true
    choices: [ 'present', 'absent' ]
  create_instance_profile:
    description:
      - Creates an IAM instance profile along with the role
    type: bool
    default: true
    version_added: 2.5
requirements: [ botocore, boto3 ]
extends_documentation_fragment:
  - aws
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Create a role with description
- iam_role:
    name: mynewrole
    assume_role_policy_document: "{{ lookup('file','policy.json') }}"
    description: This is My New Role
    state: present

# Create a role and attach a managed policy called "PowerUserAccess"
- iam_role:
    name: mynewrole
    assume_role_policy_document: "{{ lookup('file','policy.json') }}"
    state: present
    managed_policy:
      - arn:aws:iam::aws:policy/PowerUserAccess

# Keep the role created above but remove all managed policies
- iam_role:
    name: mynewrole
    assume_role_policy_document: "{{ lookup('file','policy.json') }}"
    state: present
    managed_policy:
      -

# Delete the role
- iam_role:
    name: mynewrole
    assume_role_policy_document: "{{ lookup('file','policy.json') }}"
    state: absent

'''
RETURN = '''
iam_role:
    description: dictionary containing the IAM Role data
    returned: success
    type: complex
    contains:
        path:
            description: the path to the role
            type: string
            returned: always
            sample: /
        role_name:
            description: the friendly name that identifies the role
            type: string
            returned: always
            sample: myrole
        role_id:
            description: the stable and unique string identifying the role
            type: string
            returned: always
            sample: ABCDEFF4EZ4ABCDEFV4ZC
        arn:
            description: the Amazon Resource Name (ARN) specifying the role
            type: string
            returned: always
            sample: "arn:aws:iam::1234567890:role/mynewrole"
        create_date:
            description: the date and time, in ISO 8601 date-time format, when the role was created
            type: string
            returned: always
            sample: "2016-08-14T04:36:28+00:00"
        assume_role_policy_document:
            description: the policy that grants an entity permission to assume the role
            type: string
            returned: always
            sample: {
                        'statement': [
                            {
                                'action': 'sts:AssumeRole',
                                'effect': 'Allow',
                                'principal': {
                                    'service': 'ec2.amazonaws.com'
                                },
                                'sid': ''
                            }
                        ],
                        'version': '2012-10-17'
                    }
        attached_policies:
            description: a list of dicts containing the name and ARN of the managed IAM policies attached to the role
            type: list
            returned: always
            sample: [
                {
                    'policy_arn': 'arn:aws:iam::aws:policy/PowerUserAccess',
                    'policy_name': 'PowerUserAccess'
                }
            ]
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, ec2_argument_spec, get_aws_connection_info, boto3_conn, sort_json_policy_dict
from ansible.module_utils.ec2 import HAS_BOTO3

import json
import traceback

try:
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    pass  # caught by imported HAS_BOTO3


def compare_assume_role_policy_doc(current_policy_doc, new_policy_doc):

    if sort_json_policy_dict(current_policy_doc) == sort_json_policy_dict(json.loads(new_policy_doc)):
        return True
    else:
        return False


def compare_attached_role_policies(current_attached_policies, new_attached_policies):

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


def convert_friendly_names_to_arns(connection, module, policy_names):
    if not any([not policy.startswith('arn:') for policy in policy_names]):
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


def create_or_update_role(connection, module):

    params = dict()
    params['Path'] = module.params.get('path')
    params['RoleName'] = module.params.get('name')
    params['AssumeRolePolicyDocument'] = module.params.get('assume_role_policy_document')
    if module.params.get('description') is not None:
        params['Description'] = module.params.get('description')
    managed_policies = module.params.get('managed_policy')
    create_instance_profile = module.params.get('create_instance_profile')
    if managed_policies:
        managed_policies = convert_friendly_names_to_arns(connection, module, managed_policies)
    changed = False

    # Get role
    role = get_role(connection, module, params['RoleName'])

    # If role is None, create it
    if role is None:
        try:
            role = connection.create_role(**params)
            changed = True
        except ClientError as e:
            module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    else:
        # Check Assumed Policy document
        if not compare_assume_role_policy_doc(role['AssumeRolePolicyDocument'], params['AssumeRolePolicyDocument']):
            try:
                connection.update_assume_role_policy(RoleName=params['RoleName'], PolicyDocument=json.dumps(json.loads(params['AssumeRolePolicyDocument'])))
                changed = True
            except ClientError as e:
                module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    if managed_policies is not None:
        # Get list of current attached managed policies
        current_attached_policies = get_attached_policy_list(connection, module, params['RoleName'])

        # If a single empty list item then all managed policies to be removed
        if len(managed_policies) == 1 and not managed_policies[0]:
            for policy in current_attached_policies:
                try:
                    connection.detach_role_policy(RoleName=params['RoleName'], PolicyArn=policy['PolicyArn'])
                except ClientError as e:
                    module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
                changed = True
        else:
            # Make a list of the ARNs from the attached policies
            current_attached_policies_arn_list = []
            for policy in current_attached_policies:
                current_attached_policies_arn_list.append(policy['PolicyArn'])

            # Detach roles not defined in task
            for policy_arn in list(set(current_attached_policies_arn_list) - set(managed_policies)):
                try:
                    connection.detach_role_policy(RoleName=params['RoleName'], PolicyArn=policy_arn)
                except ClientError as e:
                    module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
                changed = True

            # Attach roles not already attached
            for policy_arn in list(set(managed_policies) - set(current_attached_policies_arn_list)):
                try:
                    connection.attach_role_policy(RoleName=params['RoleName'], PolicyArn=policy_arn)
                except ClientError as e:
                    module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
                changed = True

    # Instance profile
    if create_instance_profile:
        try:
            instance_profiles = connection.list_instance_profiles_for_role(RoleName=params['RoleName'])['InstanceProfiles']
        except ClientError as e:
            module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
        if not any(p['InstanceProfileName'] == params['RoleName'] for p in instance_profiles):
            # Make sure an instance profile is attached
            try:
                connection.create_instance_profile(InstanceProfileName=params['RoleName'], Path=params['Path'])
                changed = True
            except ClientError as e:
                # If the profile already exists, no problem, move on
                if e.response['Error']['Code'] == 'EntityAlreadyExists':
                    pass
                else:
                    module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
            connection.add_role_to_instance_profile(InstanceProfileName=params['RoleName'], RoleName=params['RoleName'])

    # Get the role again
    role = get_role(connection, module, params['RoleName'])

    role['attached_policies'] = get_attached_policy_list(connection, module, params['RoleName'])
    module.exit_json(changed=changed, iam_role=camel_dict_to_snake_dict(role), **camel_dict_to_snake_dict(role))


def destroy_role(connection, module):

    params = dict()
    params['RoleName'] = module.params.get('name')

    if get_role(connection, module, params['RoleName']):

        # We need to remove any instance profiles from the role before we delete it
        try:
            instance_profiles = connection.list_instance_profiles_for_role(RoleName=params['RoleName'])['InstanceProfiles']
        except ClientError as e:
            module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

        # Now remove the role from the instance profile(s)
        for profile in instance_profiles:
            try:
                connection.remove_role_from_instance_profile(InstanceProfileName=profile['InstanceProfileName'], RoleName=params['RoleName'])
            except ClientError as e:
                module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

        # Now remove any attached policies otherwise deletion fails
        try:
            for policy in get_attached_policy_list(connection, module, params['RoleName']):
                connection.detach_role_policy(RoleName=params['RoleName'], PolicyArn=policy['PolicyArn'])
        except ClientError as e:
            module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

        try:
            connection.delete_role(**params)
        except ClientError as e:
            module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    else:
        module.exit_json(changed=False)

    module.exit_json(changed=True)


def get_role(connection, module, name):
    try:
        return connection.get_role(RoleName=name)['Role']
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            return None
        else:
            module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except NoCredentialsError as e:
        module.fail_json(msg="AWS authentication problem. " + e.message, exception=traceback.format_exc())


def get_attached_policy_list(connection, module, name):

    try:
        return connection.list_attached_role_policies(RoleName=name)['AttachedPolicies']
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            return None
        else:
            module.fail_json(msg=e.message, exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))


def main():

    argument_spec = ec2_argument_spec()
    argument_spec.update(
        dict(
            name=dict(required=True, type='str'),
            path=dict(default="/", type='str'),
            assume_role_policy_document=dict(type='json'),
            managed_policy=dict(type='list', aliases=['managed_policies']),
            state=dict(choices=['present', 'absent'], required=True),
            description=dict(required=False, type='str'),
            create_instance_profile=dict(type='bool', default=True)
        )
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=[('state', 'present', ['assume_role_policy_document'])])

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    region, ec2_url, aws_connect_params = get_aws_connection_info(module, boto3=True)

    connection = boto3_conn(module, conn_type='client', resource='iam', region=region, endpoint=ec2_url, **aws_connect_params)

    state = module.params.get("state")

    if state == 'present':
        create_or_update_role(connection, module)
    else:
        destroy_role(connection, module)

if __name__ == '__main__':
    main()

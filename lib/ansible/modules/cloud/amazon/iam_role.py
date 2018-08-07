#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

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
author: "Rob White (@wimnat)"
options:
  path:
    description:
      - The path to the role. For more information about paths, see U(http://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html).
    default: "/"
  name:
    description:
      - The name of the role to create.
    required: true
  description:
    description:
      - Provide a description of the new role
    version_added: "2.5"
  boundary:
    description:
      - Add the ARN of an IAM managed policy to restrict the permissions this role can pass on to IAM roles/users that it creates.
      - Boundaries cannot be set on Instance Profiles, so if this option is specified then C(create_instance_profile) must be false.
      - This is intended for roles/users that have permissions to create new IAM objects.
      - For more information on boundaries, see U(https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html)
    aliases: [boundary_policy_arn]
    version_added: "2.7"
  assume_role_policy_document:
    description:
      - The trust relationship policy document that grants an entity permission to assume the role.
      - "This parameter is required when C(state=present)."
  managed_policy:
    description:
      - A list of managed policy ARNs or, since Ansible 2.4, a list of either managed policy ARNs or friendly names.
        To embed an inline policy, use M(iam_policy). To remove existing policies, use an empty list item.
    aliases: [ managed_policies ]
  purge_policies:
    description:
      - Detaches any managed policies not listed in the "managed_policy" option. Set to false if you want to attach policies elsewhere.
    type: bool
    default: true
    version_added: "2.5"
  state:
    description:
      - Create or remove the IAM role
    default: present
    choices: [ present, absent ]
  create_instance_profile:
    description:
      - Creates an IAM instance profile along with the role
    type: bool
    default: yes
    version_added: "2.5"
requirements: [ botocore, boto3 ]
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Create a role with description
  iam_role:
    name: mynewrole
    assume_role_policy_document: "{{ lookup('file','policy.json') }}"
    description: This is My New Role

- name: "Create a role and attach a managed policy called 'PowerUserAccess'"
  iam_role:
    name: mynewrole
    assume_role_policy_document: "{{ lookup('file','policy.json') }}"
    managed_policy:
      - arn:aws:iam::aws:policy/PowerUserAccess

- name: Keep the role created above but remove all managed policies
  iam_role:
    name: mynewrole
    assume_role_policy_document: "{{ lookup('file','policy.json') }}"
    managed_policy:
      -

- name: Delete the role
  iam_role:
    name: mynewrole
    assume_role_policy_document: "{{ lookup('file', 'policy.json') }}"
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

from ansible.module_utils._text import to_native
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, ec2_argument_spec, get_aws_connection_info, boto3_conn, sort_json_policy_dict
from ansible.module_utils.ec2 import AWSRetry

import json
import traceback

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # caught by AnsibleAWSModule


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


def remove_policies(connection, module, policies_to_remove, params):
    for policy in policies_to_remove:
        try:
            if not module.check_mode:
                connection.detach_role_policy(RoleName=params['RoleName'], PolicyArn=policy)
        except ClientError as e:
            module.fail_json(msg="Unable to detach policy {0} from {1}: {2}".format(policy, params['RoleName'], to_native(e)),
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
        except BotoCoreError as e:
            module.fail_json(msg="Unable to detach policy {0} from {1}: {2}".format(policy, params['RoleName'], to_native(e)),
                             exception=traceback.format_exc())
        return True


def create_or_update_role(connection, module):
    params = dict()
    params['Path'] = module.params.get('path')
    params['RoleName'] = module.params.get('name')
    params['AssumeRolePolicyDocument'] = module.params.get('assume_role_policy_document')
    if module.params.get('description') is not None:
        params['Description'] = module.params.get('description')
    if module.params.get('boundary') is not None:
        params['PermissionsBoundary'] = module.params.get('boundary')
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
            if not module.check_mode:
                role = connection.create_role(**params)
                # 'Description' is documented as key of the role returned by create_role
                # but appears to be an AWS bug (the value is not returned using the AWS CLI either).
                # Get the role after creating it.
                role = get_role_with_backoff(connection, module, params['RoleName'])
            else:
                role = {'MadeInCheckMode': True}
                role['AssumeRolePolicyDocument'] = json.loads(params['AssumeRolePolicyDocument'])
            changed = True
        except ClientError as e:
            module.fail_json(msg="Unable to create role: {0}".format(to_native(e)),
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
        except BotoCoreError as e:
            module.fail_json(msg="Unable to create role: {0}".format(to_native(e)),
                             exception=traceback.format_exc())
    else:
        # Check Assumed Policy document
        if not compare_assume_role_policy_doc(role['AssumeRolePolicyDocument'], params['AssumeRolePolicyDocument']):
            try:
                if not module.check_mode:
                    connection.update_assume_role_policy(RoleName=params['RoleName'], PolicyDocument=json.dumps(json.loads(params['AssumeRolePolicyDocument'])))
                changed = True
            except ClientError as e:
                module.fail_json(msg="Unable to update assume role policy for role {0}: {1}".format(params['RoleName'], to_native(e)),
                                 exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
            except BotoCoreError as e:
                module.fail_json(msg="Unable to update assume role policy for role {0}: {1}".format(params['RoleName'], to_native(e)),
                                 exception=traceback.format_exc())

    if managed_policies is not None:
        # Get list of current attached managed policies
        current_attached_policies = get_attached_policy_list(connection, module, params['RoleName'])
        current_attached_policies_arn_list = [policy['PolicyArn'] for policy in current_attached_policies]

        # If a single empty list item then all managed policies to be removed
        if len(managed_policies) == 1 and not managed_policies[0] and module.params.get('purge_policies'):

            # Detach policies not present
            if remove_policies(connection, module, set(current_attached_policies_arn_list) - set(managed_policies), params):
                changed = True
        else:
            # Make a list of the ARNs from the attached policies

            # Detach roles not defined in task
            if module.params.get('purge_policies'):
                if remove_policies(connection, module, set(current_attached_policies_arn_list) - set(managed_policies), params):
                    changed = True

            # Attach roles not already attached
            for policy_arn in set(managed_policies) - set(current_attached_policies_arn_list):
                try:
                    if not module.check_mode:
                        connection.attach_role_policy(RoleName=params['RoleName'], PolicyArn=policy_arn)
                except ClientError as e:
                    module.fail_json(msg="Unable to attach policy {0} to role {1}: {2}".format(policy_arn, params['RoleName'], to_native(e)),
                                     exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
                except BotoCoreError as e:
                    module.fail_json(msg="Unable to attach policy {0} to role {1}: {2}".format(policy_arn, params['RoleName'], to_native(e)),
                                     exception=traceback.format_exc())
                changed = True

    # Instance profile
    if create_instance_profile and not role.get('MadeInCheckMode', False):
        try:
            instance_profiles = connection.list_instance_profiles_for_role(RoleName=params['RoleName'])['InstanceProfiles']
        except ClientError as e:
            module.fail_json(msg="Unable to list instance profiles for role {0}: {1}".format(params['RoleName'], to_native(e)),
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
        except BotoCoreError as e:
            module.fail_json(msg="Unable to list instance profiles for role {0}: {1}".format(params['RoleName'], to_native(e)),
                             exception=traceback.format_exc())
        if not any(p['InstanceProfileName'] == params['RoleName'] for p in instance_profiles):
            # Make sure an instance profile is attached
            try:
                if not module.check_mode:
                    connection.create_instance_profile(InstanceProfileName=params['RoleName'], Path=params['Path'])
                changed = True
            except ClientError as e:
                # If the profile already exists, no problem, move on
                if e.response['Error']['Code'] == 'EntityAlreadyExists':
                    pass
                else:
                    module.fail_json(msg="Unable to create instance profile for role {0}: {1}".format(params['RoleName'], to_native(e)),
                                     exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
            except BotoCoreError as e:
                module.fail_json(msg="Unable to create instance profile for role {0}: {1}".format(params['RoleName'], to_native(e)),
                                 exception=traceback.format_exc())
            if not module.check_mode:
                connection.add_role_to_instance_profile(InstanceProfileName=params['RoleName'], RoleName=params['RoleName'])

    # Check Description update
    if not role.get('MadeInCheckMode') and params.get('Description') and role['Description'] != params['Description']:
        try:
            if not module.check_mode:
                connection.update_role_description(RoleName=params['RoleName'], Description=params['Description'])

            changed = True
        except (BotoCoreError, ClientError) as e:
            module.fail_json(msg="Unable to update description for role {0}: {1}".format(params['RoleName'], to_native(e)),
                             exception=traceback.format_exc())

    # Check if permission boundary needs update
    if not role.get('MadeInCheckMode') and (
            (role.get('PermissionsBoundary') or {}).get('PermissionsBoundaryArn') or
            params.get('PermissionsBoundary') is not None):
        # the existing role has a boundary
        if module.params.get('boundary') is None:
            pass
        elif module.params.get('boundary') == '':
            if (role.get('PermissionsBoundary') or {}).get('PermissionsBoundaryArn'):
                try:
                    if not module.check_mode:
                        connection.delete_role_permissions_boundary(RoleName=params['RoleName'])
                    changed = True
                except (BotoCoreError, ClientError) as e:
                    module.fail_json_aws(e, msg="Unable to remove permission boundary for role {0}: {1}".format(params['RoleName'], to_native(e)))
        elif (role.get('PermissionsBoundary') or {}).get('PermissionsBoundaryArn') != params['PermissionsBoundary']:
            try:
                if not module.check_mode:
                    connection.put_role_permissions_boundary(RoleName=params['RoleName'], PermissionsBoundary=params['PermissionsBoundary'])
                changed = True
            except (BotoCoreError, ClientError) as e:
                module.fail_json_aws(e, msg="Unable to update permission boundary for role {0}: {1}".format(params['RoleName'], to_native(e)))

    # Get the role again
    if not role.get('MadeInCheckMode', False):
        role = get_role(connection, module, params['RoleName'])
        role['attached_policies'] = get_attached_policy_list(connection, module, params['RoleName'])

    module.exit_json(changed=changed, iam_role=camel_dict_to_snake_dict(role), **camel_dict_to_snake_dict(role))


def destroy_role(connection, module):

    params = dict()
    params['RoleName'] = module.params.get('name')

    role = get_role(connection, module, params['RoleName'])

    if role:

        # We need to remove any instance profiles from the role before we delete it
        try:
            instance_profiles = connection.list_instance_profiles_for_role(RoleName=params['RoleName'])['InstanceProfiles']
        except ClientError as e:
            module.fail_json(msg="Unable to list instance profiles for role {0}: {1}".format(params['RoleName'], to_native(e)),
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
        except BotoCoreError as e:
            module.fail_json(msg="Unable to list instance profiles for role {0}: {1}".format(params['RoleName'], to_native(e)),
                             exception=traceback.format_exc())

        if role.get('PermissionsBoundary') is not None:
            try:
                connection.delete_role_permissions_boundary(RoleName=params['RoleName'])
            except (ClientError, BotoCoreError) as e:
                module.fail_json_aws(e, msg="Could not delete role permission boundary on role {0}: {1}".format(params['RoleName'], e))

        # Now remove the role from the instance profile(s)
        for profile in instance_profiles:
            try:
                if not module.check_mode:
                    connection.remove_role_from_instance_profile(InstanceProfileName=profile['InstanceProfileName'], RoleName=params['RoleName'])
            except ClientError as e:
                module.fail_json(msg="Unable to remove role {0} from instance profile {1}: {2}".format(
                                 params['RoleName'], profile['InstanceProfileName'], to_native(e)),
                                 exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
            except BotoCoreError as e:
                module.fail_json(msg="Unable to remove role {0} from instance profile {1}: {2}".format(
                                 params['RoleName'], profile['InstanceProfileName'], to_native(e)),
                                 exception=traceback.format_exc())

        # Now remove any attached policies otherwise deletion fails
        try:
            for policy in get_attached_policy_list(connection, module, params['RoleName']):
                if not module.check_mode:
                    connection.detach_role_policy(RoleName=params['RoleName'], PolicyArn=policy['PolicyArn'])
        except ClientError as e:
            module.fail_json(msg="Unable to detach policy {0} from role {1}: {2}".format(policy['PolicyArn'], params['RoleName'], to_native(e)),
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
        except BotoCoreError as e:
            module.fail_json(msg="Unable to detach policy {0} from role {1}: {2}".format(policy['PolicyArn'], params['RoleName'], to_native(e)),
                             exception=traceback.format_exc())

        try:
            if not module.check_mode:
                connection.delete_role(**params)
        except ClientError as e:
            module.fail_json(msg="Unable to delete role: {0}".format(to_native(e)),
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
        except BotoCoreError as e:
            module.fail_json(msg="Unable to delete role: {0}".format(to_native(e)), exception=traceback.format_exc())
    else:
        module.exit_json(changed=False)

    module.exit_json(changed=True)


def get_role_with_backoff(connection, module, name):
    try:
        return AWSRetry.jittered_backoff(catch_extra_error_codes=['NoSuchEntity'])(connection.get_role)(RoleName=name)['Role']
    except (BotoCoreError, ClientError) as e:
        module.fail_json(msg="Unable to get role {0}: {1}".format(name, to_native(e)), exception=traceback.format_exc())


def get_role(connection, module, name):
    try:
        return connection.get_role(RoleName=name)['Role']
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            return None
        else:
            module.fail_json(msg="Unable to get role {0}: {1}".format(name, to_native(e)),
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except BotoCoreError as e:
        module.fail_json(msg="Unable to get role {0}: {1}".format(name, to_native(e)), exception=traceback.format_exc())


def get_attached_policy_list(connection, module, name):

    try:
        return connection.list_attached_role_policies(RoleName=name)['AttachedPolicies']
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            return []
        else:
            module.fail_json(msg="Unable to list attached policies for role {0}: {1}".format(name, to_native(e)),
                             exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except BotoCoreError as e:
        module.fail_json(msg="Unable to list attached policies for role {0}: {1}".format(name, to_native(e)),
                         exception=traceback.format_exc())


def main():

    argument_spec = dict(
        name=dict(type='str', required=True),
        path=dict(type='str', default="/"),
        assume_role_policy_document=dict(type='json'),
        managed_policy=dict(type='list', aliases=['managed_policies']),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
        description=dict(type='str'),
        boundary=dict(type='str', aliases=['boundary_policy_arn']),
        create_instance_profile=dict(type='bool', default=True),
        purge_policies=dict(type='bool', default=True),
    )
    module = AnsibleAWSModule(argument_spec=argument_spec,
                              required_if=[('state', 'present', ['assume_role_policy_document'])],
                              supports_check_mode=True)

    if module.params.get('boundary') and module.params.get('create_instance_profile'):
        module.fail_json(msg="When using a boundary policy, `create_instance_profile` must be set to `false`.")
    if module.params.get('boundary') is not None and not module.botocore_at_least('1.10.57'):
        module.fail_json(msg="When using a boundary policy, botocore must be at least v1.10.57. "
                         "Current versions: boto3-{boto3_version} botocore-{botocore_version}".format(**module._gather_versions()))

    connection = module.client('iam')

    state = module.params.get("state")

    if state == 'present':
        create_or_update_role(connection, module)
    else:
        destroy_role(connection, module)


if __name__ == '__main__':
    main()

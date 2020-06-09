#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: iam_role
short_description: Manage AWS IAM roles
description:
  - Manage AWS IAM roles.
version_added: "2.3"
author: "Rob White (@wimnat)"
options:
  path:
    description:
      - The path to the role. For more information about paths, see U(https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html).
    default: "/"
    type: str
  name:
    description:
      - The name of the role to create.
    required: true
    type: str
  description:
    description:
      - Provides a description of the role.
    version_added: "2.5"
    type: str
  boundary:
    description:
      - The ARN of an IAM managed policy to use to restrict the permissions this role can pass on to IAM roles/users that it creates.
      - Boundaries cannot be set on Instance Profiles, as such if this option is specified then I(create_instance_profile) must be C(false).
      - This is intended for roles/users that have permissions to create new IAM objects.
      - For more information on boundaries, see U(https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_boundaries.html).
      - Requires botocore 1.10.57 or above.
    aliases: [boundary_policy_arn]
    version_added: "2.7"
    type: str
  assume_role_policy_document:
    description:
      - The trust relationship policy document that grants an entity permission to assume the role.
      - This parameter is required when I(state=present).
    type: json
  managed_policies:
    description:
      - A list of managed policy ARNs or, since Ansible 2.4, a list of either managed policy ARNs or friendly names.
      - To remove all policies set I(purge_polices=true) and I(managed_policies=[None]).
      - To embed an inline policy, use M(iam_policy).
    aliases: ['managed_policy']
    type: list
  max_session_duration:
    description:
      - The maximum duration (in seconds) of a session when assuming the role.
      - Valid values are between 1 and 12 hours (3600 and 43200 seconds).
    version_added: "2.10"
    type: int
  purge_policies:
    description:
      - When I(purge_policies=true) any managed policies not listed in I(managed_policies) will be detatched.
      - By default I(purge_policies=true).  In Ansible 2.14 this will be changed to I(purge_policies=false).
    version_added: "2.5"
    type: bool
    aliases: ['purge_policy', 'purge_managed_policies']
  state:
    description:
      - Create or remove the IAM role.
    default: present
    choices: [ present, absent ]
    type: str
  create_instance_profile:
    description:
      - Creates an IAM instance profile along with the role.
    default: true
    version_added: "2.5"
    type: bool
  delete_instance_profile:
    description:
      - When I(delete_instance_profile=true) and I(state=absent) deleting a role will also delete the instance
        profile created with the same I(name) as the role.
      - Only applies when I(state=absent).
    default: false
    version_added: "2.10"
    type: bool
  tags:
    description:
      - Tag dict to apply to the queue.
      - Requires botocore 1.12.46 or above.
    version_added: "2.10"
    type: dict
  purge_tags:
    description:
      - Remove tags not listed in I(tags) when tags is specified.
    default: true
    version_added: "2.10"
    type: bool
requirements: [ botocore, boto3 ]
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

- name: Create a role with description and tags
  iam_role:
    name: mynewrole
    assume_role_policy_document: "{{ lookup('file','policy.json') }}"
    description: This is My New Role
    tags:
      env: dev

- name: "Create a role and attach a managed policy called 'PowerUserAccess'"
  iam_role:
    name: mynewrole
    assume_role_policy_document: "{{ lookup('file','policy.json') }}"
    managed_policies:
      - arn:aws:iam::aws:policy/PowerUserAccess

- name: Keep the role created above but remove all managed policies
  iam_role:
    name: mynewrole
    assume_role_policy_document: "{{ lookup('file','policy.json') }}"
    managed_policies: []

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
            type: str
            returned: always
            sample: /
        role_name:
            description: the friendly name that identifies the role
            type: str
            returned: always
            sample: myrole
        role_id:
            description: the stable and unique string identifying the role
            type: str
            returned: always
            sample: ABCDEFF4EZ4ABCDEFV4ZC
        arn:
            description: the Amazon Resource Name (ARN) specifying the role
            type: str
            returned: always
            sample: "arn:aws:iam::1234567890:role/mynewrole"
        create_date:
            description: the date and time, in ISO 8601 date-time format, when the role was created
            type: str
            returned: always
            sample: "2016-08-14T04:36:28+00:00"
        assume_role_policy_document:
            description: the policy that grants an entity permission to assume the role
            type: str
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
        tags:
            description: role tags
            type: dict
            returned: always
            sample: '{"Env": "Prod"}'
'''

import json

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import camel_dict_to_snake_dict, compare_policies
from ansible.module_utils.ec2 import AWSRetry, ansible_dict_to_boto3_tag_list, boto3_tag_list_to_ansible_dict, compare_aws_tags

try:
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    pass  # caught by AnsibleAWSModule


def compare_assume_role_policy_doc(current_policy_doc, new_policy_doc):
    if not compare_policies(current_policy_doc, json.loads(new_policy_doc)):
        return True
    else:
        return False


@AWSRetry.jittered_backoff()
def _list_policies(connection):
    paginator = connection.get_paginator('list_policies')
    return paginator.paginate().build_full_result()['Policies']


def convert_friendly_names_to_arns(connection, module, policy_names):
    if not any([not policy.startswith('arn:') for policy in policy_names]):
        return policy_names
    allpolicies = {}
    policies = _list_policies(connection)

    for policy in policies:
        allpolicies[policy['PolicyName']] = policy['Arn']
        allpolicies[policy['Arn']] = policy['Arn']
    try:
        return [allpolicies[policy] for policy in policy_names]
    except KeyError as e:
        module.fail_json_aws(e, msg="Couldn't find policy")


def attach_policies(connection, module, policies_to_attach, params):
    changed = False
    for policy_arn in policies_to_attach:
        try:
            if not module.check_mode:
                connection.attach_role_policy(RoleName=params['RoleName'], PolicyArn=policy_arn, aws_retry=True)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Unable to attach policy {0} to role {1}".format(policy_arn, params['RoleName']))
        changed = True
    return changed


def remove_policies(connection, module, policies_to_remove, params):
    changed = False
    for policy in policies_to_remove:
        try:
            if not module.check_mode:
                connection.detach_role_policy(RoleName=params['RoleName'], PolicyArn=policy, aws_retry=True)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Unable to detach policy {0} from {1}".format(policy, params['RoleName']))
        changed = True
    return changed


def generate_create_params(module):
    params = dict()
    params['Path'] = module.params.get('path')
    params['RoleName'] = module.params.get('name')
    params['AssumeRolePolicyDocument'] = module.params.get('assume_role_policy_document')
    if module.params.get('description') is not None:
        params['Description'] = module.params.get('description')
    if module.params.get('max_session_duration') is not None:
        params['MaxSessionDuration'] = module.params.get('max_session_duration')
    if module.params.get('boundary') is not None:
        params['PermissionsBoundary'] = module.params.get('boundary')
    if module.params.get('tags') is not None:
        params['Tags'] = ansible_dict_to_boto3_tag_list(module.params.get('tags'))

    return params


def create_basic_role(connection, module, params):
    """
    Perform the Role creation.
    Assumes tests for the role existing have already been performed.
    """

    try:
        if not module.check_mode:
            role = connection.create_role(aws_retry=True, **params)
            # 'Description' is documented as key of the role returned by create_role
            # but appears to be an AWS bug (the value is not returned using the AWS CLI either).
            # Get the role after creating it.
            role = get_role_with_backoff(connection, module, params['RoleName'])
        else:
            role = {'MadeInCheckMode': True}
            role['AssumeRolePolicyDocument'] = json.loads(params['AssumeRolePolicyDocument'])
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Unable to create role")

    return role


def update_role_assumed_policy(connection, module, params, role):
    # Check Assumed Policy document
    if compare_assume_role_policy_doc(role['AssumeRolePolicyDocument'], params['AssumeRolePolicyDocument']):
        return False

    if module.check_mode:
        return True

    try:
        connection.update_assume_role_policy(
            RoleName=params['RoleName'],
            PolicyDocument=json.dumps(json.loads(params['AssumeRolePolicyDocument'])),
            aws_retry=True)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Unable to update assume role policy for role {0}".format(params['RoleName']))
    return True


def update_role_description(connection, module, params, role):
    # Check Description update
    if params.get('Description') is None:
        return False
    if role.get('Description') == params['Description']:
        return False

    if module.check_mode:
        return True

    try:
        connection.update_role_description(RoleName=params['RoleName'], Description=params['Description'], aws_retry=True)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Unable to update description for role {0}".format(params['RoleName']))
    return True


def update_role_max_session_duration(connection, module, params, role):
    # Check MaxSessionDuration update
    if params.get('MaxSessionDuration') is None:
        return False
    if role.get('MaxSessionDuration') == params['MaxSessionDuration']:
        return False

    if module.check_mode:
        return True

    try:
        connection.update_role(RoleName=params['RoleName'], MaxSessionDuration=params['MaxSessionDuration'], aws_retry=True)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Unable to update maximum session duration for role {0}".format(params['RoleName']))
    return True


def update_role_permissions_boundary(connection, module, params, role):
    # Check PermissionsBoundary
    if params.get('PermissionsBoundary') is None:
        return False
    if params.get('PermissionsBoundary') == role.get('PermissionsBoundary', {}).get('PermissionsBoundaryArn', ''):
        return False

    if module.check_mode:
        return True

    if params.get('PermissionsBoundary') == '':
        try:
            connection.delete_role_permissions_boundary(RoleName=params['RoleName'], aws_retry=True)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Unable to remove permission boundary for role {0}".format(params['RoleName']))
    else:
        try:
            connection.put_role_permissions_boundary(RoleName=params['RoleName'], PermissionsBoundary=params['PermissionsBoundary'], aws_retry=True)
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Unable to update permission boundary for role {0}".format(params['RoleName']))
    return True


def update_managed_policies(connection, module, params, role, managed_policies, purge_policies):
    # Check Managed Policies
    if managed_policies is None:
        return False

    # If we're manipulating a fake role
    if role.get('MadeInCheckMode', False):
        role['AttachedPolicies'] = list(map(lambda x: {'PolicyArn': x, 'PolicyName': x.split(':')[5]}, managed_policies))
        return True

    # Get list of current attached managed policies
    current_attached_policies = get_attached_policy_list(connection, module, params['RoleName'])
    current_attached_policies_arn_list = [policy['PolicyArn'] for policy in current_attached_policies]

    if len(managed_policies) == 1 and managed_policies[0] is None:
        managed_policies = []

    policies_to_remove = set(current_attached_policies_arn_list) - set(managed_policies)
    policies_to_attach = set(managed_policies) - set(current_attached_policies_arn_list)

    changed = False

    if purge_policies:
        changed |= remove_policies(connection, module, policies_to_remove, params)

    changed |= attach_policies(connection, module, policies_to_attach, params)

    return changed


def create_or_update_role(connection, module):

    params = generate_create_params(module)
    role_name = params['RoleName']
    create_instance_profile = module.params.get('create_instance_profile')
    purge_policies = module.params.get('purge_policies')
    if purge_policies is None:
        purge_policies = True
    managed_policies = module.params.get('managed_policies')
    if managed_policies:
        # Attempt to list the policies early so we don't leave things behind if we can't find them.
        managed_policies = convert_friendly_names_to_arns(connection, module, managed_policies)

    changed = False

    # Get role
    role = get_role(connection, module, role_name)

    # If role is None, create it
    if role is None:
        role = create_basic_role(connection, module, params)
        changed = True
    else:
        changed |= update_role_tags(connection, module, params, role)
        changed |= update_role_assumed_policy(connection, module, params, role)
        changed |= update_role_description(connection, module, params, role)
        changed |= update_role_max_session_duration(connection, module, params, role)
        changed |= update_role_permissions_boundary(connection, module, params, role)

    if create_instance_profile:
        changed |= create_instance_profiles(connection, module, params, role)

    changed |= update_managed_policies(connection, module, params, role, managed_policies, purge_policies)

    # Get the role again
    if not role.get('MadeInCheckMode', False):
        role = get_role(connection, module, params['RoleName'])
        role['AttachedPolicies'] = get_attached_policy_list(connection, module, params['RoleName'])
        role['tags'] = get_role_tags(connection, module)

    module.exit_json(
        changed=changed, iam_role=camel_dict_to_snake_dict(role, ignore_list=['tags']),
        **camel_dict_to_snake_dict(role, ignore_list=['tags']))


def create_instance_profiles(connection, module, params, role):

    if role.get('MadeInCheckMode', False):
        return False

    # Fetch existing Profiles
    try:
        instance_profiles = connection.list_instance_profiles_for_role(RoleName=params['RoleName'], aws_retry=True)['InstanceProfiles']
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Unable to list instance profiles for role {0}".format(params['RoleName']))

    # Profile already exists
    if any(p['InstanceProfileName'] == params['RoleName'] for p in instance_profiles):
        return False

    if module.check_mode:
        return True

    # Make sure an instance profile is created
    try:
        connection.create_instance_profile(InstanceProfileName=params['RoleName'], Path=params['Path'], aws_retry=True)
    except ClientError as e:
        # If the profile already exists, no problem, move on.
        # Implies someone's changing things at the same time...
        if e.response['Error']['Code'] == 'EntityAlreadyExists':
            return False
        else:
            module.fail_json_aws(e, msg="Unable to create instance profile for role {0}".format(params['RoleName']))
    except BotoCoreError as e:
        module.fail_json_aws(e, msg="Unable to create instance profile for role {0}".format(params['RoleName']))

    # And attach the role to the profile
    try:
        connection.add_role_to_instance_profile(InstanceProfileName=params['RoleName'], RoleName=params['RoleName'], aws_retry=True)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Unable to attach role {0} to instance profile {0}".format(params['RoleName']))

    return True


def remove_instance_profiles(connection, module, role_params, role):
    role_name = module.params.get('name')
    delete_profiles = module.params.get("delete_instance_profile")

    try:
        instance_profiles = connection.list_instance_profiles_for_role(aws_retry=True, **role_params)['InstanceProfiles']
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Unable to list instance profiles for role {0}".format(role_name))

    # Remove the role from the instance profile(s)
    for profile in instance_profiles:
        profile_name = profile['InstanceProfileName']
        try:
            if not module.check_mode:
                connection.remove_role_from_instance_profile(aws_retry=True, InstanceProfileName=profile_name, **role_params)
                if profile_name == role_name:
                    if delete_profiles:
                        try:
                            connection.delete_instance_profile(InstanceProfileName=profile_name, aws_retry=True)
                        except (BotoCoreError, ClientError) as e:
                            module.fail_json_aws(e, msg="Unable to remove instance profile {0}".format(profile_name))
        except (BotoCoreError, ClientError) as e:
            module.fail_json_aws(e, msg="Unable to remove role {0} from instance profile {1}".format(role_name, profile_name))


def destroy_role(connection, module):

    role_name = module.params.get('name')
    role = get_role(connection, module, role_name)
    role_params = dict()
    role_params['RoleName'] = role_name
    boundary_params = dict(role_params)
    boundary_params['PermissionsBoundary'] = ''

    if role is None:
        module.exit_json(changed=False)

    # Before we try to delete the role we need to remove any
    # - attached instance profiles
    # - attached managed policies
    # - permissions boundary
    remove_instance_profiles(connection, module, role_params, role)
    update_managed_policies(connection, module, role_params, role, [], True)
    update_role_permissions_boundary(connection, module, boundary_params, role)

    try:
        if not module.check_mode:
            connection.delete_role(aws_retry=True, **role_params)
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Unable to delete role")

    module.exit_json(changed=True)


def get_role_with_backoff(connection, module, name):
    try:
        return AWSRetry.jittered_backoff(catch_extra_error_codes=['NoSuchEntity'])(connection.get_role)(RoleName=name)['Role']
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e, msg="Unable to get role {0}".format(name))


def get_role(connection, module, name):
    try:
        return connection.get_role(RoleName=name, aws_retry=True)['Role']
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            return None
        else:
            module.fail_json_aws(e, msg="Unable to get role {0}".format(name))
    except BotoCoreError as e:
        module.fail_json_aws(e, msg="Unable to get role {0}".format(name))


def get_attached_policy_list(connection, module, name):
    try:
        return connection.list_attached_role_policies(RoleName=name, aws_retry=True)['AttachedPolicies']
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to list attached policies for role {0}".format(name))


def get_role_tags(connection, module):
    role_name = module.params.get('name')
    if not hasattr(connection, 'list_role_tags'):
        return {}
    try:
        return boto3_tag_list_to_ansible_dict(connection.list_role_tags(RoleName=role_name, aws_retry=True)['Tags'])
    except (ClientError, BotoCoreError) as e:
        module.fail_json_aws(e, msg="Unable to list tags for role {0}".format(role_name))


def update_role_tags(connection, module, params, role):
    new_tags = params.get('Tags')
    if new_tags is None:
        return False
    new_tags = boto3_tag_list_to_ansible_dict(new_tags)

    role_name = module.params.get('name')
    purge_tags = module.params.get('purge_tags')

    try:
        existing_tags = boto3_tag_list_to_ansible_dict(connection.list_role_tags(RoleName=role_name, aws_retry=True)['Tags'])
    except (ClientError, KeyError):
        existing_tags = {}

    tags_to_add, tags_to_remove = compare_aws_tags(existing_tags, new_tags, purge_tags=purge_tags)

    if not module.check_mode:
        try:
            if tags_to_remove:
                connection.untag_role(RoleName=role_name, TagKeys=tags_to_remove, aws_retry=True)
            if tags_to_add:
                connection.tag_role(RoleName=role_name, Tags=ansible_dict_to_boto3_tag_list(tags_to_add), aws_retry=True)
        except (ClientError, BotoCoreError) as e:
            module.fail_json_aws(e, msg='Unable to set tags for role %s' % role_name)

    changed = bool(tags_to_add) or bool(tags_to_remove)
    return changed


def main():

    argument_spec = dict(
        name=dict(type='str', required=True),
        path=dict(type='str', default="/"),
        assume_role_policy_document=dict(type='json'),
        managed_policies=dict(type='list', aliases=['managed_policy']),
        max_session_duration=dict(type='int'),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
        description=dict(type='str'),
        boundary=dict(type='str', aliases=['boundary_policy_arn']),
        create_instance_profile=dict(type='bool', default=True),
        delete_instance_profile=dict(type='bool', default=False),
        purge_policies=dict(type='bool', aliases=['purge_policy', 'purge_managed_policies']),
        tags=dict(type='dict'),
        purge_tags=dict(type='bool', default=True),
    )
    module = AnsibleAWSModule(argument_spec=argument_spec,
                              required_if=[('state', 'present', ['assume_role_policy_document'])],
                              supports_check_mode=True)

    if module.params.get('purge_policies') is None:
        module.deprecate('In Ansible 2.14 the default value of purge_policies will change from true to false.'
                         '  To maintain the existing behaviour explicity set purge_policies=true',
                         version='2.14', collection_name='ansible.builtin')

    if module.params.get('boundary'):
        if module.params.get('create_instance_profile'):
            module.fail_json(msg="When using a boundary policy, `create_instance_profile` must be set to `false`.")
        if not module.params.get('boundary').startswith('arn:aws:iam'):
            module.fail_json(msg="Boundary policy must be an ARN")
    if module.params.get('tags') is not None and not module.botocore_at_least('1.12.46'):
        module.fail_json(msg="When managing tags botocore must be at least v1.12.46. "
                         "Current versions: boto3-{boto3_version} botocore-{botocore_version}".format(**module._gather_versions()))
    if module.params.get('boundary') is not None and not module.botocore_at_least('1.10.57'):
        module.fail_json(msg="When using a boundary policy, botocore must be at least v1.10.57. "
                         "Current versions: boto3-{boto3_version} botocore-{botocore_version}".format(**module._gather_versions()))
    if module.params.get('max_session_duration'):
        max_session_duration = module.params.get('max_session_duration')
        if max_session_duration < 3600 or max_session_duration > 43200:
            module.fail_json(msg="max_session_duration must be between 1 and 12 hours (3600 and 43200 seconds)")
    if module.params.get('path'):
        path = module.params.get('path')
        if not path.endswith('/') or not path.startswith('/'):
            module.fail_json(msg="path must begin and end with /")

    connection = module.client('iam', retry_decorator=AWSRetry.jittered_backoff())

    state = module.params.get("state")

    if state == 'present':
        create_or_update_role(connection, module)
    else:
        destroy_role(connection, module)


if __name__ == '__main__':
    main()

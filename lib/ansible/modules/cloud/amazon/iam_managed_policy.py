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
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>
ANSIBLE_METADATA = {'status': ['stableinterface'],
                    'supported_by': 'community',
                    'metadata_version': '1.0'}

DOCUMENTATION = '''
---
module: iam_managed_policy
short_description: Manage User Managed IAM policies
description:
    - Allows creating and removing managed IAM policies
version_added: "2.4"
options:
  policy_name:
    description:
      - The name of the managed policy.
    required: True
  policy_description:
    description:
      - A helpful description of this policy, this value is immuteable and only set when creating a new policy.
    default: ''
  policy:
    description:
      - A properly json formatted policy
  make_default:
    description:
      - Make this revision the default revision.
    default: True
  only_version:
    description:
      - Remove all other non default revisions, if this is used with C(make_default) it will result in all other versions of this policy being deleted.
    required: False
    default: False
  state:
    description:
      - Should this managed policy be present or absent. Set to absent to detach all entities from this policy and remove it if found.
    required: True
    default: null
    choices: [ "present", "absent" ]
author: "Dan Kozlowski (@dkhenry)"
requirements:
    - boto3
    - botocore
'''

EXAMPLES = '''
# Create Policy ex nihilo
- name: Create IAM Managed Policy
  iam_managed_policy:
    policy_name: "ManagedPolicy"
    policy_description: "A Helpful managed policy"
    policy: "{{ lookup('template', 'managed_policy.json.j2') }}"
    state: present

# Update a policy with a new default version
- name: Create IAM Managed Policy
  iam_managed_policy:
    policy_name: "ManagedPolicy"
    policy: "{{ lookup('file', 'managed_policy_update.json') }}"
    state: present

# Update a policy with a new non default version
- name: Create IAM Managed Policy
  iam_managed_policy:
    policy_name: "ManagedPolicy"
    policy: "{{ lookup('file', 'managed_policy_update.json') }}"
    make_default: false
    state: present

# Update a policy and make it the only version and the default version
- name: Create IAM Managed Policy
  iam_managed_policy:
    policy_name: "ManagedPolicy"
    policy: "{ 'Version': '2012-10-17', 'Statement':[{'Effect': 'Allow','Action': '*','Resource': '*'}]}"
    only_version: true
    state: present

# Remove a policy
- name: Create IAM Managed Policy
  iam_managed_policy:
    policy_name: "ManagedPolicy"
    state: absent
'''

RETURN = '''
policy:
  description: Returns the policy json structure, when state == absent this will return the value of the removed policy.
  returned: success
  type: string
  sample: '{
        "Arn": "arn:aws:iam::aws:policy/AdministratorAccess "
        "AttachmentCount": 0,
        "CreateDate": "2017-03-01T15:42:55.981000+00:00",
        "DefaultVersionId": "v1",
        "IsAttachable": true,
        "Path": "/",
        "PolicyId": "ANPALM4KLDMTFXGOOJIHL",
        "PolicyName": "AdministratorAccess",
        "UpdateDate": "2017-03-01T15:42:55.981000+00:00"
  }'
'''
from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.ec2
from ansible.module_utils.ec2 import sort_json_policy_dict
import json

try:
    import boto3
    import botocore
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def get_policy_by_name(iam, name, **kwargs):
    response = iam.list_policies(Scope='Local', **kwargs)
    for policy in response['Policies']:
        if policy['PolicyName'] == name:
            return policy
    if response['IsTruncated']:
        return get_policy_by_name(iam, name, marker=response['marker'])
    return None


def delete_oldest_non_default_version(iam, policy):
    versions = [v for v in iam.list_policy_versions(PolicyArn=policy['Arn'])[
        'Versions'] if not v['IsDefaultVersion']]
    versions.sort(key=lambda v: v['CreateDate'], reverse=True)
    for v in versions[-1:]:
        iam.delete_policy_version(
            PolicyArn=policy['Arn'],
            VersionId=v['VersionId']
        )

# This needs to return policy_version, changed


def get_or_create_policy_version(iam, policy, policy_document):
    versions = iam.list_policy_versions(PolicyArn=policy['Arn'])['Versions']
    for v in versions:
        document = iam.get_policy_version(
            PolicyArn=policy['Arn'],
            VersionId=v['VersionId'])['PolicyVersion']['Document']
        if sort_json_policy_dict(document) == sort_json_policy_dict(
                json.loads(policy_document)):
            return v, False

    # No existing version so create one
    # Instead of testing the versions list for the magic number 5, we are
    # going to attempt to create a version and catch the error
    try:
        return iam.create_policy_version(
            PolicyArn=policy['Arn'],
            PolicyDocument=policy_document
        )['PolicyVersion'], True
    except Exception as e:
        delete_oldest_non_default_version(iam, policy)
        return iam.create_policy_version(
            PolicyArn=policy['Arn'],
            PolicyDocument=policy_document
        )['PolicyVersion'], True


def set_if_default(iam, policy, policy_version, is_default):
    if is_default and not policy_version['IsDefaultVersion']:
        iam.set_default_policy_version(
            PolicyArn=policy['Arn'],
            VersionId=policy_version['VersionId']
        )
        return True
    return False


def set_if_only(iam, policy, policy_version, is_only):
    if is_only:
        versions = [v for v in iam.list_policy_versions(PolicyArn=policy['Arn'])[
            'Versions'] if not v['IsDefaultVersion']]
        for v in versions:
            iam.delete_policy_version(
                PolicyArn=policy['Arn'],
                VersionId=v['VersionId']
            )
        return len(versions) > 0
    return False


def detach_all_entities(iam, policy, **kwargs):
    entities = iam.list_entities_for_policy(PolicyArn=policy['Arn'], **kwargs)
    for g in entities['PolicyGroups']:
        iam.detach_group_policy(
            PolicyArn=policy['Arn'],
            GroupName=g['GroupName']
        )
    for u in entities['PolicyUsers']:
        iam.detach_user_policy(
            PolicyArn=policy['Arn'],
            UserName=u['UserName']
        )
    for r in entities['PolicyRoles']:
        iam.detach_role_policy(
            PolicyArn=policy['Arn'],
            RoleName=r['RoleName']
        )
    if entities['IsTruncated']:
        detach_all_entities(iam, policy, marker=entities['Marker'])


def main():
    argument_spec = ansible.module_utils.ec2.ec2_argument_spec()
    argument_spec.update(dict(
        policy_name=dict(required=True),
        policy_description=dict(required=False, default=''),
        policy=dict(type='json', required=False, default=None),
        make_default=dict(type='bool', required=False, default=True),
        only_version=dict(type='bool', required=False, default=False),
        fail_on_delete=dict(type='bool', required=False, default=True),
        state=dict(required=True, default=None, choices=['present', 'absent']),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required for this module')

    name = module.params.get('policy_name')
    description = module.params.get('policy_description')
    state = module.params.get('state')
    default = module.params.get('make_default')
    only = module.params.get('only_version')

    policy = None

    if module.params.get('policy') is not None:
        policy = json.dumps(json.loads(module.params.get('policy')))

    if state == 'present' and policy is None:
        module.fail_json(msg='if state is present policy is required')

    try:
        region, ec2_url, aws_connect_kwargs = ansible.module_utils.ec2.get_aws_connection_info(
            module, boto3=True)
        iam = ansible.module_utils.ec2.boto3_conn(
            module,
            conn_type='client',
            resource='iam',
            region=region,
            endpoint=ec2_url,
            **aws_connect_kwargs)
    except botocore.exceptions.NoCredentialsError as e:
        module.fail_json(msg=boto_exception(e))

    p = get_policy_by_name(iam, name)
    if state == 'present':
        if p is None:
            # No Policy so just create one
            rvalue = iam.create_policy(
                PolicyName=name,
                Path='/',
                PolicyDocument=policy,
                Description=description
            )
            module.exit_json(changed=True, policy=rvalue['Policy'])
        else:
            policy_version, changed = get_or_create_policy_version(
                iam, p, policy)
            changed = set_if_default(
                iam, p, policy_version, default) or changed
            changed = set_if_only(iam, p, policy_version, only) or changed
            # If anything has changed we needto refresh the policy
            if changed:
                p = iam.get_policy(PolicyArn=p['Arn'])['Policy']

            module.exit_json(changed=changed, policy=p)
    else:
        # Check for existing policy
        if p:
            # Detach policy
            detach_all_entities(iam, p)
            # Delete Versions
            for v in iam.list_policy_versions(PolicyArn=p['Arn'])['Versions']:
                if not v['IsDefaultVersion']:
                    iam.delete_policy_version(
                        PolicyArn=p['Arn'], VersionId=v['VersionId'])
            # Delete policy
            iam.delete_policy(PolicyArn=p['Arn'])
            # This is the one case where we will return the old policy
            module.exit_json(changed=True, policy=p)
        else:
            module.exit_json(changed=False, policy=None)
# end main


# import module snippets
if __name__ == '__main__':
    main()

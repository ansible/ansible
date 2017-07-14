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
        "arn": "arn:aws:iam::aws:policy/AdministratorAccess "
        "attachment_count": 0,
        "create_date": "2017-03-01T15:42:55.981000+00:00",
        "default_version_id": "v1",
        "is_attachable": true,
        "path": "/",
        "policy_id": "ANPALM4KLDMTFXGOOJIHL",
        "policy_name": "AdministratorAccess",
        "update_date": "2017-03-01T15:42:55.981000+00:00"
  }'
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import boto3_conn, get_aws_connection_info, ec2_argument_spec, AWSRetry
from ansible.module_utils.ec2 import sort_json_policy_dict, camel_dict_to_snake_dict, HAS_BOTO3
import json
import traceback

try:
    import botocore
except ImportError:
    pass  # caught by imported HAS_BOTO3


@AWSRetry.backoff(tries=5, delay=5, backoff=2.0)
def list_policies_with_backoff(iam):
    paginator = iam.get_paginator('list_policies')
    return paginator.paginate(Scope='Local').build_full_result()


def get_policy_by_name(module, iam, name):
    try:
        response = list_policies_with_backoff(iam)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Couldn't list policies: %s" % str(e),
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))
    for policy in response['Policies']:
        if policy['PolicyName'] == name:
            return policy
    return None


def delete_oldest_non_default_version(module, iam, policy):
    try:
        versions = [v for v in iam.list_policy_versions(PolicyArn=policy['Arn'])['Versions']
                    if not v['IsDefaultVersion']]
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Couldn't list policy versions: %s" % str(e),
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))
    versions.sort(key=lambda v: v['CreateDate'], reverse=True)
    for v in versions[-1:]:
        try:
            iam.delete_policy_version(PolicyArn=policy['Arn'], VersionId=v['VersionId'])
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Couldn't delete policy version: %s" % str(e),
                             exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))


# This needs to return policy_version, changed
def get_or_create_policy_version(module, iam, policy, policy_document):
    try:
        versions = iam.list_policy_versions(PolicyArn=policy['Arn'])['Versions']
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Couldn't list policy versions: %s" % str(e),
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))
    for v in versions:
        try:
            document = iam.get_policy_version(PolicyArn=policy['Arn'],
                                              VersionId=v['VersionId'])['PolicyVersion']['Document']
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Couldn't get policy version %s: %s" % (v['VersionId'], str(e)),
                             exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))
        if sort_json_policy_dict(document) == sort_json_policy_dict(
                json.loads(policy_document)):
            return v, False

    # No existing version so create one
    # There is a service limit (typically 5) of policy versions.
    #
    # Rather than assume that it is 5, we'll try to create the policy
    # and if that doesn't work, delete the oldest non default policy version
    # and try again.
    try:
        version = iam.create_policy_version(PolicyArn=policy['Arn'], PolicyDocument=policy_document)['PolicyVersion']
        return version, True
    except botocore.exceptions.ClientError as e:
        if e['Error']['Code'] == 'LimitExceeded':
            delete_oldest_non_default_version(module, iam, policy)
            try:
                version = iam.create_policy_version(PolicyArn=policy['Arn'], PolicyDocument=policy_document)['PolicyVersion']
                return version, True
            except botocore.exceptions.ClientError as e:
                pass
        # Handle both when the exception isn't LimitExceeded or
        # the second attempt still failed
        module.fail_json(msg="Couldn't create policy version: %s" % str(e),
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))


def set_if_default(module, iam, policy, policy_version, is_default):
    if is_default and not policy_version['IsDefaultVersion']:
        try:
            iam.set_default_policy_version(PolicyArn=policy['Arn'], VersionId=policy_version['VersionId'])
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Couldn't set default policy version: %s" % str(e),
                             exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))
        return True
    return False


def set_if_only(module, iam, policy, policy_version, is_only):
    if is_only:
        try:
            versions = [v for v in iam.list_policy_versions(PolicyArn=policy['Arn'])[
                'Versions'] if not v['IsDefaultVersion']]
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Couldn't list policy versions: %s" % str(e),
                             exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))
        for v in versions:
            try:
                iam.delete_policy_version(PolicyArn=policy['Arn'], VersionId=v['VersionId'])
            except botocore.exceptions.ClientError as e:
                module.fail_json(msg="Couldn't delete policy version: %s" % str(e),
                                 exception=traceback.format_exc(),
                                 **camel_dict_to_snake_dict(e.response))
        return len(versions) > 0
    return False


def detach_all_entities(module, iam, policy, **kwargs):
    try:
        entities = iam.list_entities_for_policy(PolicyArn=policy['Arn'], **kwargs)
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Couldn't detach list entities for policy %s: %s" % (policy['PolicyName'], str(e)),
                         exception=traceback.format_exc(),
                         **camel_dict_to_snake_dict(e.response))

    for g in entities['PolicyGroups']:
        try:
            iam.detach_group_policy(PolicyArn=policy['Arn'], GroupName=g['GroupName'])
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Couldn't detach group policy %s: %s" % (g['GroupName'], str(e)),
                             exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))
    for u in entities['PolicyUsers']:
        try:
            iam.detach_user_policy(PolicyArn=policy['Arn'], UserName=u['UserName'])
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Couldn't detach user policy %s: %s" % (u['UserName'], str(e)),
                             exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))
    for r in entities['PolicyRoles']:
        try:
            iam.detach_role_policy(PolicyArn=policy['Arn'], RoleName=r['RoleName'])
        except botocore.exceptions.ClientError as e:
            module.fail_json(msg="Couldn't detach role policy %s: %s" % (r['RoleName'], str(e)),
                             exception=traceback.format_exc(),
                             **camel_dict_to_snake_dict(e.response))
    if entities['IsTruncated']:
        detach_all_entities(module, iam, policy, marker=entities['Marker'])


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        policy_name=dict(required=True),
        policy_description=dict(default=''),
        policy=dict(type='json'),
        make_default=dict(type='bool', default=True),
        only_version=dict(type='bool', default=False),
        fail_on_delete=dict(type='bool', default=True),
        state=dict(required=True, choices=['present', 'absent']),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=[['state', 'present', ['policy']]]
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

    try:
        region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
        iam = boto3_conn(module, conn_type='client', resource='iam',
                         region=region, endpoint=ec2_url, **aws_connect_kwargs)
    except (botocore.exceptions.NoCredentialsError, botocore.exceptions.ProfileNotFound) as e:
        module.fail_json(msg="Can't authorize connection. Check your credentials and profile.",
                         exceptions=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))

    p = get_policy_by_name(module, iam, name)
    if state == 'present':
        if p is None:
            # No Policy so just create one
            try:
                rvalue = iam.create_policy(PolicyName=name, Path='/',
                                           PolicyDocument=policy, Description=description)
            except:
                module.fail_json(msg="Couldn't create policy %s: %s" % (name, str(e)),
                                 exception=traceback.format_exc(),
                                 **camel_dict_to_snake_dict(e.response))

            module.exit_json(changed=True, policy=camel_dict_to_snake_dict(rvalue['Policy']))
        else:
            policy_version, changed = get_or_create_policy_version(module, iam, p, policy)
            changed = set_if_default(module, iam, p, policy_version, default) or changed
            changed = set_if_only(module, iam, p, policy_version, only) or changed
            # If anything has changed we needto refresh the policy
            if changed:
                try:
                    p = iam.get_policy(PolicyArn=p['Arn'])['Policy']
                except:
                    module.fail_json(msg="Couldn't get policy: %s" % str(e),
                                     exception=traceback.format_exc(),
                                     **camel_dict_to_snake_dict(e.response))

            module.exit_json(changed=changed, policy=camel_dict_to_snake_dict(p))
    else:
        # Check for existing policy
        if p:
            # Detach policy
            detach_all_entities(module, iam, p)
            # Delete Versions
            try:
                versions = iam.list_policy_versions(PolicyArn=p['Arn'])['Versions']
            except botocore.exceptions.ClientError as e:
                module.fail_json(msg="Couldn't list policy versions: %s" % str(e),
                                 exception=traceback.format_exc(),
                                 **camel_dict_to_snake_dict(e.response))
            for v in versions:
                if not v['IsDefaultVersion']:
                    try:
                        iam.delete_policy_version(PolicyArn=p['Arn'], VersionId=v['VersionId'])
                    except botocore.exceptions.ClientError as e:
                        module.fail_json(msg="Couldn't delete policy version %s: %s" % (v['VersionId'], str(e)),
                                         exception=traceback.format_exc(),
                                         **camel_dict_to_snake_dict(e.response))
            # Delete policy
            try:
                iam.delete_policy(PolicyArn=p['Arn'])
            except:
                module.fail_json(msg="Couldn't delete policy %s: %s" % (p['PolicyName'], str(e)),
                                 exception=traceback.format_exc(),
                                 **camel_dict_to_snake_dict(e.response))
            # This is the one case where we will return the old policy
            module.exit_json(changed=True, policy=camel_dict_to_snake_dict(p))
        else:
            module.exit_json(changed=False, policy=None)
# end main


# import module snippets
if __name__ == '__main__':
    main()

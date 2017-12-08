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
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: iam_policy
short_description: Manage IAM policies for users, groups, and roles
description:
     - Allows uploading or removing IAM policies for IAM users, groups or roles.
version_added: "2.0"
options:
  iam_type:
    description:
      - Type of IAM resource
    required: true
    default: null
    choices: [ "user", "group", "role"]
  iam_name:
    description:
      - Name of IAM resource you wish to target for policy actions. In other words, the user name, group name or role name.
    required: true
  policy_name:
    description:
      - The name label for the policy to create or remove.
    required: true
  policy_document:
    description:
      - The path to the properly json formatted policy file (mutually exclusive with C(policy_json))
    required: false
  policy_json:
    description:
      - A properly json formatted policy as string (mutually exclusive with C(policy_document),
        see https://github.com/ansible/ansible/issues/7005#issuecomment-42894813 on how to use it properly)
    required: false
  state:
    description:
      - Whether to create or delete the IAM policy.
    required: true
    default: null
    choices: [ "present", "absent"]
  skip_duplicates:
    description:
      - By default the module looks for any policies that match the document you pass in, if there is a match it will not make a new policy object with
        the same rules. You can override this by specifying false which would allow for two policy objects with different names but same rules.
    required: false
    default: "/"

notes:
  - 'Currently boto does not support the removal of Managed Policies, the module will not work removing/adding managed policies.'
author: "Jonathan I. Davila (@defionscode)"
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Create a policy with the name of 'Admin' to the group 'administrators'
tasks:
- name: Assign a policy called Admin to the administrators group
  iam_policy:
    iam_type: group
    iam_name: administrators
    policy_name: Admin
    state: present
    policy_document: admin_policy.json

# Advanced example, create two new groups and add a READ-ONLY policy to both
# groups.
task:
- name: Create Two Groups, Mario and Luigi
  iam:
    iam_type: group
    name: "{{ item }}"
    state: present
  with_items:
     - Mario
     - Luigi
  register: new_groups

- name: Apply READ-ONLY policy to new groups that have been recently created
  iam_policy:
    iam_type: group
    iam_name: "{{ item.created_group.group_name }}"
    policy_name: "READ-ONLY"
    policy_document: readonlypolicy.json
    state: present
  with_items: "{{ new_groups.results }}"

# Create a new S3 policy with prefix per user
tasks:
- name: Create S3 policy from template
  iam_policy:
    iam_type: user
    iam_name: "{{ item.user }}"
    policy_name: "s3_limited_access_{{ item.prefix }}"
    state: present
    policy_json: " {{ lookup( 'template', 's3_policy.json.j2') }} "
    with_items:
      - user: s3_user
        prefix: s3_user_prefix

'''
import json

try:
    import boto
    import boto.iam
    import boto.ec2
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import connect_to_aws, ec2_argument_spec, get_aws_connection_info, boto_exception
from ansible.module_utils.six import string_types
from ansible.module_utils.six.moves import urllib


def user_action(module, iam, name, policy_name, skip, pdoc, state):
    policy_match = False
    changed = False
    try:
        current_policies = [cp for cp in iam.get_all_user_policies(name).
                            list_user_policies_result.
                            policy_names]
        matching_policies = []
        for pol in current_policies:
            '''
            urllib is needed here because boto returns url encoded strings instead
            '''
            if urllib.parse.unquote(iam.get_user_policy(name, pol).
                                    get_user_policy_result.policy_document) == pdoc:
                policy_match = True
                matching_policies.append(pol)

        if state == 'present':
            # If policy document does not already exist (either it's changed
            # or the policy is not present) or if we're not skipping dupes then
            # make the put call.  Note that the put call does a create or update.
            if not policy_match or (not skip and policy_name not in matching_policies):
                changed = True
                iam.put_user_policy(name, policy_name, pdoc)
        elif state == 'absent':
            try:
                iam.delete_user_policy(name, policy_name)
                changed = True
            except boto.exception.BotoServerError as err:
                error_msg = boto_exception(err)
                if 'cannot be found.' in error_msg:
                    changed = False
                    module.exit_json(changed=changed, msg="%s policy is already absent" % policy_name)

        updated_policies = [cp for cp in iam.get_all_user_policies(name).
                            list_user_policies_result.
                            policy_names]
    except boto.exception.BotoServerError as err:
        error_msg = boto_exception(err)
        module.fail_json(changed=changed, msg=error_msg)

    return changed, name, updated_policies


def role_action(module, iam, name, policy_name, skip, pdoc, state):
    policy_match = False
    changed = False
    try:
        current_policies = [cp for cp in iam.list_role_policies(name).
                            list_role_policies_result.
                            policy_names]
    except boto.exception.BotoServerError as e:
        if e.error_code == "NoSuchEntity":
            # Role doesn't exist so it's safe to assume the policy doesn't either
            module.exit_json(changed=False, msg="No such role, policy will be skipped.")
        else:
            module.fail_json(msg=e.message)

    try:
        matching_policies = []
        for pol in current_policies:
            if urllib.parse.unquote(iam.get_role_policy(name, pol).
                                    get_role_policy_result.policy_document) == pdoc:
                policy_match = True
                matching_policies.append(pol)

        if state == 'present':
            # If policy document does not already exist (either it's changed
            # or the policy is not present) or if we're not skipping dupes then
            # make the put call.  Note that the put call does a create or update.
            if not policy_match or (not skip and policy_name not in matching_policies):
                changed = True
                iam.put_role_policy(name, policy_name, pdoc)
        elif state == 'absent':
            try:
                iam.delete_role_policy(name, policy_name)
                changed = True
            except boto.exception.BotoServerError as err:
                error_msg = boto_exception(err)
                if 'cannot be found.' in error_msg:
                    changed = False
                    module.exit_json(changed=changed,
                                     msg="%s policy is already absent" % policy_name)
                else:
                    module.fail_json(msg=err.message)

        updated_policies = [cp for cp in iam.list_role_policies(name).
                            list_role_policies_result.
                            policy_names]
    except boto.exception.BotoServerError as err:
        error_msg = boto_exception(err)
        module.fail_json(changed=changed, msg=error_msg)

    return changed, name, updated_policies


def group_action(module, iam, name, policy_name, skip, pdoc, state):
    policy_match = False
    changed = False
    msg = ''
    try:
        current_policies = [cp for cp in iam.get_all_group_policies(name).
                            list_group_policies_result.
                            policy_names]
        matching_policies = []
        for pol in current_policies:
            if urllib.parse.unquote(iam.get_group_policy(name, pol).
                                    get_group_policy_result.policy_document) == pdoc:
                policy_match = True
                matching_policies.append(pol)
                msg = ("The policy document you specified already exists "
                       "under the name %s." % pol)
        if state == 'present':
            # If policy document does not already exist (either it's changed
            # or the policy is not present) or if we're not skipping dupes then
            # make the put call.  Note that the put call does a create or update.
            if not policy_match or (not skip and policy_name not in matching_policies):
                changed = True
                iam.put_group_policy(name, policy_name, pdoc)
        elif state == 'absent':
            try:
                iam.delete_group_policy(name, policy_name)
                changed = True
            except boto.exception.BotoServerError as err:
                error_msg = boto_exception(err)
                if 'cannot be found.' in error_msg:
                    changed = False
                    module.exit_json(changed=changed,
                                     msg="%s policy is already absent" % policy_name)

        updated_policies = [cp for cp in iam.get_all_group_policies(name).
                            list_group_policies_result.
                            policy_names]
    except boto.exception.BotoServerError as err:
        error_msg = boto_exception(err)
        module.fail_json(changed=changed, msg=error_msg)

    return changed, name, updated_policies, msg


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        iam_type=dict(
            default=None, required=True, choices=['user', 'group', 'role']),
        state=dict(
            default=None, required=True, choices=['present', 'absent']),
        iam_name=dict(default=None, required=False),
        policy_name=dict(default=None, required=True),
        policy_document=dict(default=None, required=False),
        policy_json=dict(type='json', default=None, required=False),
        skip_duplicates=dict(type='bool', default=True, required=False)
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    state = module.params.get('state').lower()
    iam_type = module.params.get('iam_type').lower()
    state = module.params.get('state')
    name = module.params.get('iam_name')
    policy_name = module.params.get('policy_name')
    skip = module.params.get('skip_duplicates')

    if module.params.get('policy_document') is not None and module.params.get('policy_json') is not None:
        module.fail_json(msg='Only one of "policy_document" or "policy_json" may be set')

    if module.params.get('policy_document') is not None:
        with open(module.params.get('policy_document'), 'r') as json_data:
            pdoc = json.dumps(json.load(json_data))
            json_data.close()
    elif module.params.get('policy_json') is not None:
        pdoc = module.params.get('policy_json')
        # if its a string, assume it is already JSON
        if not isinstance(pdoc, string_types):
            try:
                pdoc = json.dumps(pdoc)
            except Exception as e:
                module.fail_json(msg='Failed to convert the policy into valid JSON: %s' % str(e))
    else:
        pdoc = None

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module)

    try:
        if region:
            iam = connect_to_aws(boto.iam, region, **aws_connect_kwargs)
        else:
            iam = boto.iam.connection.IAMConnection(**aws_connect_kwargs)
    except boto.exception.NoAuthHandlerFound as e:
        module.fail_json(msg=str(e))

    changed = False

    if iam_type == 'user':
        changed, user_name, current_policies = user_action(module, iam, name,
                                                           policy_name, skip, pdoc,
                                                           state)
        module.exit_json(changed=changed, user_name=name, policies=current_policies)
    elif iam_type == 'role':
        changed, role_name, current_policies = role_action(module, iam, name,
                                                           policy_name, skip, pdoc,
                                                           state)
        module.exit_json(changed=changed, role_name=name, policies=current_policies)
    elif iam_type == 'group':
        changed, group_name, current_policies, msg = group_action(module, iam, name,
                                                                  policy_name, skip, pdoc,
                                                                  state)
        module.exit_json(changed=changed, group_name=name, policies=current_policies, msg=msg)


if __name__ == '__main__':
    main()

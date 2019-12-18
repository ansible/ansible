#!/usr/bin/python
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: iam_policy
short_description: Manage inline IAM policies for users, groups, and roles
description:
    - Allows uploading or removing inline IAM policies for IAM users, groups or roles.
    - To administer managed policies please see M(iam_user), M(iam_role),
      M(iam_group) and M(iam_managed_policy)
version_added: "2.0"
options:
  iam_type:
    description:
      - Type of IAM resource.
    required: true
    choices: [ "user", "group", "role"]
    type: str
  iam_name:
    description:
      - Name of IAM resource you wish to target for policy actions. In other words, the user name, group name or role name.
    required: true
    type: str
  policy_name:
    description:
      - The name label for the policy to create or remove.
    required: true
    type: str
  policy_document:
    description:
      - The path to the properly json formatted policy file.
      - Mutually exclusive with I(policy_json).
      - This option has been deprecated and will be removed in 2.14.  The existing behavior can be
        reproduced by using the I(policy_json) option and reading the file using the lookup plugin.
    type: str
  policy_json:
    description:
      - A properly json formatted policy as string.
      - Mutually exclusive with I(policy_document).
      - See U(https://github.com/ansible/ansible/issues/7005#issuecomment-42894813) on how to use it properly.
    type: json
  state:
    description:
      - Whether to create or delete the IAM policy.
    choices: [ "present", "absent"]
    default: present
    type: str
  skip_duplicates:
    description:
      - When I(skip_duplicates=true) the module looks for any policies that match the document you pass in.  If there is a match it will not make
        a new policy object with the same rules.
      - The current default is C(true).  However, this behavior can be confusing and as such the default will change to C(false) in 2.14.  To maintain
        the existing behavior explicitly set I(skip_duplicates=true).
    type: bool

author:
  - "Jonathan I. Davila (@defionscode)"
  - "Dennis Podkovyrin (@sbj-ss)"
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Create a policy with the name of 'Admin' to the group 'administrators'
- name: Assign a policy called Admin to the administrators group
  iam_policy:
    iam_type: group
    iam_name: administrators
    policy_name: Admin
    state: present
    policy_document: admin_policy.json

# Advanced example, create two new groups and add a READ-ONLY policy to both
# groups.
- name: Create Two Groups, Mario and Luigi
  iam:
    iam_type: group
    name: "{{ item }}"
    state: present
  loop:
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
  loop: "{{ new_groups.results }}"

# Create a new S3 policy with prefix per user
- name: Create S3 policy from template
  iam_policy:
    iam_type: user
    iam_name: "{{ item.user }}"
    policy_name: "s3_limited_access_{{ item.prefix }}"
    state: present
    policy_json: " {{ lookup( 'template', 's3_policy.json.j2') }} "
    loop:
      - user: s3_user
        prefix: s3_user_prefix

'''
import json

try:
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    pass

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import compare_policies
from ansible.module_utils.six import string_types


class PolicyError(Exception):
    pass


class Policy:

    def __init__(self, client, name, policy_name, policy_document, policy_json, skip_duplicates, state, check_mode):
        self.client = client
        self.name = name
        self.policy_name = policy_name
        self.policy_document = policy_document
        self.policy_json = policy_json
        self.skip_duplicates = skip_duplicates
        self.state = state
        self.check_mode = check_mode
        self.changed = False

    @staticmethod
    def _iam_type():
        return ''

    def _list(self, name):
        return {}

    def list(self):
        return self._list(self.name).get('PolicyNames', [])

    def _get(self, name, policy_name):
        return '{}'

    def get(self, policy_name):
        return self._get(self.name, policy_name)['PolicyDocument']

    def _put(self, name, policy_name, policy_doc):
        pass

    def put(self, policy_doc):
        if not self.check_mode:
            self._put(self.name, self.policy_name, json.dumps(policy_doc, sort_keys=True))
        self.changed = True

    def _delete(self, name, policy_name):
        pass

    def delete(self):
        if self.policy_name not in self.list():
            self.changed = False
            return

        self.changed = True
        if not self.check_mode:
            self._delete(self.name, self.policy_name)

    def get_policy_text(self):
        try:
            if self.policy_document is not None:
                return self.get_policy_from_document()
            if self.policy_json is not None:
                return self.get_policy_from_json()
        except json.JSONDecodeError as e:
            raise PolicyError('Failed to decode the policy as valid JSON: %s' % str(e))
        return None

    def get_policy_from_document(self):
        try:
            with open(self.policy_document, 'r') as json_data:
                pdoc = json.load(json_data)
                json_data.close()
        except IOError as e:
            if e.errno == 2:
                raise PolicyError('policy_document {0:!r} does not exist'.format(self.policy_document))
            raise
        return pdoc

    def get_policy_from_json(self):
        if isinstance(self.policy_json, string_types):
            pdoc = json.loads(self.policy_json)
        else:
            pdoc = self.policy_json
        return pdoc

    def create(self):
        matching_policies = []
        policy_doc = self.get_policy_text()
        policy_match = False
        for pol in self.list():
            if not compare_policies(self.get(pol), policy_doc):
                matching_policies.append(pol)
                policy_match = True

        if (self.policy_name not in matching_policies) and not (self.skip_duplicates and policy_match):
            self.put(policy_doc)

    def run(self):
        if self.state == 'present':
            self.create()
        elif self.state == 'absent':
            self.delete()
        return {
            'changed': self.changed,
            self._iam_type() + '_name': self.name,
            'policies': self.list()
        }


class UserPolicy(Policy):

    @staticmethod
    def _iam_type():
        return 'user'

    def _list(self, name):
        return self.client.list_user_policies(UserName=name)

    def _get(self, name, policy_name):
        return self.client.get_user_policy(UserName=name, PolicyName=policy_name)

    def _put(self, name, policy_name, policy_doc):
        return self.client.put_user_policy(UserName=name, PolicyName=policy_name, PolicyDocument=policy_doc)

    def _delete(self, name, policy_name):
        return self.client.delete_user_policy(UserName=name, PolicyName=policy_name)


class RolePolicy(Policy):

    @staticmethod
    def _iam_type():
        return 'role'

    def _list(self, name):
        return self.client.list_role_policies(RoleName=name)

    def _get(self, name, policy_name):
        return self.client.get_role_policy(RoleName=name, PolicyName=policy_name)

    def _put(self, name, policy_name, policy_doc):
        return self.client.put_role_policy(RoleName=name, PolicyName=policy_name, PolicyDocument=policy_doc)

    def _delete(self, name, policy_name):
        return self.client.delete_role_policy(RoleName=name, PolicyName=policy_name)


class GroupPolicy(Policy):

    @staticmethod
    def _iam_type():
        return 'group'

    def _list(self, name):
        return self.client.list_group_policies(GroupName=name)

    def _get(self, name, policy_name):
        return self.client.get_group_policy(GroupName=name, PolicyName=policy_name)

    def _put(self, name, policy_name, policy_doc):
        return self.client.put_group_policy(GroupName=name, PolicyName=policy_name, PolicyDocument=policy_doc)

    def _delete(self, name, policy_name):
        return self.client.delete_group_policy(GroupName=name, PolicyName=policy_name)


def main():
    argument_spec = dict(
        iam_type=dict(required=True, choices=['user', 'group', 'role']),
        state=dict(default='present', choices=['present', 'absent']),
        iam_name=dict(required=True),
        policy_name=dict(required=True),
        policy_document=dict(default=None, required=False),
        policy_json=dict(type='json', default=None, required=False),
        skip_duplicates=dict(type='bool', default=None, required=False)
    )
    mutually_exclusive = [['policy_document', 'policy_json']]

    module = AnsibleAWSModule(argument_spec=argument_spec, mutually_exclusive=mutually_exclusive, supports_check_mode=True)

    skip_duplicates = module.params.get('skip_duplicates')

    if (skip_duplicates is None):
        module.deprecate('The skip_duplicates behaviour has caused confusion and'
                         ' will be disabled by default in Ansible 2.14',
                         version='2.14')
        skip_duplicates = True

    if module.params.get('policy_document'):
        module.deprecate('The policy_document option has been deprecated and'
                         ' will be removed in Ansible 2.14',
                         version='2.14')

    args = dict(
        client=module.client('iam'),
        name=module.params.get('iam_name'),
        policy_name=module.params.get('policy_name'),
        policy_document=module.params.get('policy_document'),
        policy_json=module.params.get('policy_json'),
        skip_duplicates=skip_duplicates,
        state=module.params.get('state'),
        check_mode=module.check_mode,
    )
    iam_type = module.params.get('iam_type')

    try:
        if iam_type == 'user':
            policy = UserPolicy(**args)
        elif iam_type == 'role':
            policy = RolePolicy(**args)
        elif iam_type == 'group':
            policy = GroupPolicy(**args)

        module.exit_json(**(policy.run()))
    except (BotoCoreError, ClientError) as e:
        module.fail_json_aws(e)
    except PolicyError as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

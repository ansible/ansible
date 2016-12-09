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

from __future__ import print_function

import json
import time
import inspect

from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

try:
    import boto3
    from botocore.exceptions import ClientError

    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: ecr
version_added: "2.3"
short_description: Manage Elastic Container Registry repositories
description:
    - Manage Elastic Container Registry repositories
options:
    name:
        description:
            - the name of the repository
        required: true
    policy:
        description:
            - dict that gets JSONified for policy_text
        required: false
    policy_text:
        description:
            - string for new policy text
            - setting to an empty string removes the repository's policy
        required: false
    delete_policy:
        description:
            - if yes, remove the policy from the repository
        required: false
        default: false
    state:
        description:
            - create or destroy the repository
        required: false
        choices: [present, absent]
        default: 'present'
author:
 - David M. Lee (@leedm777)
extends_documentation_fragment: aws
'''

EXAMPLES = '''
# Since neither policy nor policy_text are specified, existing policies on the
# repository are unchanged
- name: ecr-repo
  ecr: name=super/cool

- name: destroy-ecr-repo
  ecr: name=old/busted state=absent

- name: set-policy
  ecr:
    name: needs-policy
    policy:
      Version: '2008-10-17'
      Statement:
        - Sid: read-only
          Effect: Allow
          Principal:
            AWS: '{{ read_only_arn }}'
          Action:
            - ecr:GetDownloadUrlForLayer
            - ecr:BatchGetImage
            - ecr:BatchCheckLayerAvailability

- name: set-policy-text
  ecr:
    name: needs-policy
    policy_text: "{{ lookup('template', 'policy.json.j2') }}"
'''

RETURN = '''
created:
    type: boolean
    description: If true, the repository was created
    returned: "when state == 'present'"
repository:
    type: dict
    description: The created or updated repository
    returned: "when state == 'present'"
    sample:
        - createdAt: xxx

'''


class ECR:
    def __init__(self, module):
        region, ec2_url, aws_connect_kwargs = \
            get_aws_connection_info(module, boto3=True)

        self.ecr = boto3_conn(module, conn_type='client',
                              resource='ecr', region=region,
                              endpoint=ec2_url, **aws_connect_kwargs)
        self.check_mode = module.check_mode
        self.changed = False
        self.skipped = False

    def get_repository(self, name):
        try:
            res = self.ecr.describe_repositories(repositoryNames=[name])
            repos = res.get('repositories')
            return repos and repos[0]
        except ClientError as err:
            code = err.response['Error'].get('Code', 'Unknown')
            if code == 'RepositoryNotFoundException':
                return None
            raise

    def get_repository_policy(self, name):
        try:
            res = self.ecr.get_repository_policy(repositoryName=name)
            text = res.get('policyText')
            return text and json.loads(text)
        except ClientError as err:
            code = err.response['Error'].get('Code', 'Unknown')
            if code == 'RepositoryPolicyNotFoundException':
                return None
            raise

    def create_repository(self, name):
        if not self.check_mode:
            repo = self.ecr.create_repository(repositoryName=name).get(
                'repository')
            self.changed = True
            return repo

        self.skipped = True
        return dict(repositoryName=name)

    def set_repository_policy(self, name, policy_text):
        if not self.check_mode:
            policy = self.ecr.set_repository_policy(repositoryName=name,
                                                    policyText=policy_text)
            self.changed = True
            return policy

        self.skipped = True
        if self.get_repository(name) is None:
            # TODO: if does not exists, fail gracefully
            raise Error('TODO: handle this case')
        return

    def delete_repository(self, name):
        if not self.check_mode:
            repo = self.ecr.delete_repository(repositoryName=name)
            self.changed = True
            return repo

        repo = self.get_repository(name)
        if repo:
            self.skipped = True
            return repo
        return None

    def delete_repository_policy(self, name):
        if not self.check_mode:
            policy = self.ecr.delete_repository_policy(repositoryName=name)
            self.changed = True
            return policy

        policy = self.get_repository_policy(name)
        if policy:
            self.skipped = True
            return policy
        return None


def run(ecr, params, verbosity):
    result = {}
    try:
        name = params['name']
        state = params['state']
        policy = params['policy']
        policy_text = params['policy_text']
        delete_policy = params['delete_policy']

        try:
            if policy_text is not None:
                # policy_text given; parse it
                policy = json.loads(policy_text)
            elif policy is not None:
                # policy given; dump it
                policy_text = json.dumps(policy)
        except ValueError:
            result['msg'] = 'Invalid JSON given for policy_text'
            return False, result

        result['state'] = state
        result['created'] = False

        repo = ecr.get_repository(name)

        if state == 'present':
            result['created'] = False
            if not repo:
                repo = ecr.create_repository(name)
                result['changed'] = True
                result['created'] = True
            result['repository'] = repo

            if delete_policy:
                original_policy = ecr.get_repository_policy(name)

                if verbosity >= 2:
                    result['policy'] = None

                if verbosity >= 3:
                    result['original_policy'] = original_policy

                if original_policy:
                    ecr.delete_repository_policy(name)
                    result['changed'] = True

            elif policy is not None:
                try:
                    if verbosity >= 2:
                        result['policy'] = policy
                    original_policy = ecr.get_repository_policy(name)
                    if verbosity >= 3:
                        result['original_policy'] = original_policy

                    if original_policy != policy:
                        ecr.set_repository_policy(name, policy_text)
                        result['changed'] = True
                except:
                    # Some failure w/ the policy. It's helpful to know what the
                    # policy is.
                    result['policy'] = policy_text
                    raise

        elif state == 'absent':
            result['name'] = name
            if repo:
                ecr.delete_repository(name)
                result['changed'] = True

    except Exception as err:
        msg = str(err)
        if isinstance(err, ClientError):
            msg = boto_exception(err)
        result['msg'] = msg
        result['exception'] = traceback.format_exc()
        return False, result

    if ecr.skipped:
        result['skipped'] = True

    if ecr.changed:
        result['changed'] = True

    return True, result


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        state=dict(required=False, choices=['present', 'absent'],
                   default='present'),
        policy=dict(required=False, type='dict'),
        policy_text=dict(required=False)),
        delete_policy=dict(required=False, type='bool'))

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           mutually_exclusive=[
                               ['policy', 'policy_text', 'delete_policy']])

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    ecr = ECR(module)
    passed, result = run(ecr, module.params, module._verbosity)

    if passed:
        module.exit_json(**result)
    else:
        module.fail_json(**result)


if __name__ == '__main__':
    main()

#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: ecs_ecr
version_added: "2.3"
short_description: Manage Elastic Container Registry repositories
description:
    - Manage Elastic Container Registry repositories
requirements: [ boto3 ]
options:
    name:
        description:
            - the name of the repository
        required: true
    registry_id:
        description:
            - AWS account id associated with the registry.
            - If not specified, the default registry is assumed.
        required: false
    policy:
        description:
            - JSON or dict that represents the new policy
        required: false
    force_set_policy:
        description:
            - if no, prevents setting a policy that would prevent you from
              setting another policy in the future.
        required: false
        default: false
    delete_policy:
        description:
            - deprecated. Use I(purge_policy) instead. To be removed in
              Ansible 2.9
        required: false
        default: false
    purge_policy:
        description:
            - if yes, remove the policy from the repository
        required: false
        default: false
        version_added: '2.5'
    lifecycle_policy:
        description:
            - JSON or dict that represents the new lifecycle policy
        required: false
        version_added: '2.5'
    purge_lifecycle_policy:
        description:
            - if yes, remove the lifecycle policy from the repository
        required: false
        default: false
        version_added: '2.5'
    state:
        description:
            - create or destroy the repository
        required: false
        choices: [present, absent]
        default: 'present'
author:
 - David M. Lee (@leedm777)
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
# If the repository does not exist, it is created. If it does exist, would not
# affect any policies already on it.
- name: ecr-repo
  ecs_ecr: name=super/cool

- name: destroy-ecr-repo
  ecs_ecr: name=old/busted state=absent

- name: Cross account ecr-repo
  ecs_ecr: registry_id=999999999999 name=cross/account

- name: set-policy as object
  ecs_ecr:
    name: needs-policy-object
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

- name: set-policy as string
  ecs_ecr:
    name: needs-policy-string
    policy: "{{ lookup('template', 'policy.json.j2') }}"

- name: delete-policy
  ecs_ecr:
    name: needs-no-policy
    purge_policy: yes

- name: set-lifecycle-policy
  ecs_ecr:
    name: needs-lifecycle-policy
    lifecycle_policy:
      rules:
        - rulePriority: 1
          description: new policy
          selection:
            tagStatus: untagged
            countType: sinceImagePushed
            countUnit: days
            countNumber: 365
          action:
            type: expire

- name: delete-lifecycle-policy
  ecs_ecr:
    name: needs-no-lifecycle-policy
    purge_lifecycle_policy: yes
'''

RETURN = '''
state:
    type: string
    description: The asserted state of the repository (present, absent)
    returned: always
created:
    type: boolean
    description: If true, the repository was created
    returned: always
name:
    type: string
    description: The name of the repository
    returned: "when state == 'absent'"
repository:
    type: dict
    description: The created or updated repository
    returned: "when state == 'present'"
    sample:
        createdAt: '2017-01-17T08:41:32-06:00'
        registryId: '999999999999'
        repositoryArn: arn:aws:ecr:us-east-1:999999999999:repository/ecr-test-1484664090
        repositoryName: ecr-test-1484664090
        repositoryUri: 999999999999.dkr.ecr.us-east-1.amazonaws.com/ecr-test-1484664090
'''

import json
import traceback

try:
    from botocore.exceptions import ClientError
except ImportError:
    pass  # Taken care of by ec2.HAS_BOTO3

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import (HAS_BOTO3, boto3_conn, boto_exception, ec2_argument_spec,
                                      get_aws_connection_info, sort_json_policy_dict)


def build_kwargs(registry_id):
    """
    Builds a kwargs dict which may contain the optional registryId.

    :param registry_id: Optional string containing the registryId.
    :return: kwargs dict with registryId, if given
    """
    if not registry_id:
        return dict()
    else:
        return dict(registryId=registry_id)


class EcsEcr:
    def __init__(self, module):
        region, ec2_url, aws_connect_kwargs = \
            get_aws_connection_info(module, boto3=True)

        self.ecr = boto3_conn(module, conn_type='client',
                              resource='ecr', region=region,
                              endpoint=ec2_url, **aws_connect_kwargs)
        self.sts = boto3_conn(module, conn_type='client',
                              resource='sts', region=region,
                              endpoint=ec2_url, **aws_connect_kwargs)
        self.check_mode = module.check_mode
        self.changed = False
        self.skipped = False

    def get_repository(self, registry_id, name):
        try:
            res = self.ecr.describe_repositories(
                repositoryNames=[name], **build_kwargs(registry_id))
            repos = res.get('repositories')
            return repos and repos[0]
        except ClientError as err:
            code = err.response['Error'].get('Code', 'Unknown')
            if code == 'RepositoryNotFoundException':
                return None
            raise

    def get_repository_policy(self, registry_id, name):
        try:
            res = self.ecr.get_repository_policy(
                repositoryName=name, **build_kwargs(registry_id))
            text = res.get('policyText')
            return text and json.loads(text)
        except ClientError as err:
            code = err.response['Error'].get('Code', 'Unknown')
            if code == 'RepositoryPolicyNotFoundException':
                return None
            raise

    def create_repository(self, registry_id, name):
        if registry_id:
            default_registry_id = self.sts.get_caller_identity().get('Account')
            if registry_id != default_registry_id:
                raise Exception('Cannot create repository in registry {}.'
                                'Would be created in {} instead.'.format(
                                    registry_id, default_registry_id))
        if not self.check_mode:
            repo = self.ecr.create_repository(repositoryName=name).get('repository')
            self.changed = True
            return repo
        else:
            self.skipped = True
            return dict(repositoryName=name)

    def set_repository_policy(self, registry_id, name, policy_text, force):
        if not self.check_mode:
            policy = self.ecr.set_repository_policy(
                repositoryName=name,
                policyText=policy_text,
                force=force,
                **build_kwargs(registry_id))
            self.changed = True
            return policy
        else:
            self.skipped = True
            if self.get_repository(registry_id, name) is None:
                printable = name
                if registry_id:
                    printable = '{}:{}'.format(registry_id, name)
                raise Exception(
                    'could not find repository {}'.format(printable))
            return

    def delete_repository(self, registry_id, name):
        if not self.check_mode:
            repo = self.ecr.delete_repository(
                repositoryName=name, **build_kwargs(registry_id))
            self.changed = True
            return repo
        else:
            repo = self.get_repository(registry_id, name)
            if repo:
                self.skipped = True
                return repo
            return None

    def delete_repository_policy(self, registry_id, name):
        if not self.check_mode:
            policy = self.ecr.delete_repository_policy(
                repositoryName=name, **build_kwargs(registry_id))
            self.changed = True
            return policy
        else:
            policy = self.get_repository_policy(registry_id, name)
            if policy:
                self.skipped = True
                return policy
            return None

    def get_lifecycle_policy(self, registry_id, name):
        try:
            res = self.ecr.get_lifecycle_policy(
                repositoryName=name, **build_kwargs(registry_id))
            text = res.get('lifecyclePolicyText')
            return text and json.loads(text)
        except ClientError as err:
            code = err.response['Error'].get('Code', 'Unknown')
            if code == 'LifecyclePolicyNotFoundException':
                return None
            raise

    def put_lifecycle_policy(self, registry_id, name, policy_text):
        if not self.check_mode:
            policy = self.ecr.put_lifecycle_policy(
                repositoryName=name,
                lifecyclePolicyText=policy_text,
                **build_kwargs(registry_id))
            self.changed = True
            return policy
        else:
            self.skipped = True
            if self.get_repository(registry_id, name) is None:
                printable = name
                if registry_id:
                    printable = '{}:{}'.format(registry_id, name)
                raise Exception(
                    'could not find repository {}'.format(printable))
            return

    def delete_lifecycle_policy(self, registry_id, name):
        if not self.check_mode:
            policy = self.ecr.delete_lifecycle_policy(
                repositoryName=name, **build_kwargs(registry_id))
            self.changed = True
            return policy
        else:
            policy = self.get_lifecycle_policy(registry_id, name)
            if policy:
                self.skipped = True
                return policy
            return None


def run(ecr, params):
    # type: (EcsEcr, dict, int) -> Tuple[bool, dict]
    result = {}
    try:
        name = params['name']
        state = params['state']
        policy_text = params['policy']
        purge_policy = params['purge_policy'] or params['delete_policy']
        registry_id = params['registry_id']
        force_set_policy = params['force_set_policy']
        lifecycle_policy_text = params['lifecycle_policy']
        purge_lifecycle_policy = params['purge_lifecycle_policy']

        # Parse policies, if they are given
        try:
            policy = policy_text and json.loads(policy_text)
        except ValueError:
            result['policy'] = policy_text
            result['msg'] = 'Could not parse policy'
            return False, result

        try:
            lifecycle_policy = \
                lifecycle_policy_text and json.loads(lifecycle_policy_text)
        except ValueError:
            result['lifecycle_policy'] = lifecycle_policy_text
            result['msg'] = 'Could not parse lifecycle_policy'
            return False, result

        result['state'] = state
        result['created'] = False

        repo = ecr.get_repository(registry_id, name)

        if state == 'present':
            result['created'] = False
            if not repo:
                repo = ecr.create_repository(registry_id, name)
                result['changed'] = True
                result['created'] = True
            result['repository'] = repo

            if purge_lifecycle_policy:
                original_lifecycle_policy = \
                    ecr.get_lifecycle_policy(registry_id, name)

                result['lifecycle_policy'] = None

                if original_lifecycle_policy:
                    ecr.delete_lifecycle_policy(registry_id, name)
                    result['changed'] = True

            elif lifecycle_policy_text is not None:
                try:
                    lifecycle_policy = sort_json_policy_dict(lifecycle_policy)
                    result['lifecycle_policy'] = lifecycle_policy

                    original_lifecycle_policy = ecr.get_lifecycle_policy(
                        registry_id, name)

                    if original_lifecycle_policy:
                        original_lifecycle_policy = sort_json_policy_dict(
                            original_lifecycle_policy)

                    if original_lifecycle_policy != lifecycle_policy:
                        ecr.put_lifecycle_policy(registry_id, name,
                                                 lifecycle_policy_text)
                        result['changed'] = True
                except:
                    # Some failure w/ the policy. It's helpful to know what the
                    # policy is.
                    result['lifecycle_policy'] = lifecycle_policy_text
                    raise

            if purge_policy:
                original_policy = ecr.get_repository_policy(registry_id, name)

                result['policy'] = None

                if original_policy:
                    ecr.delete_repository_policy(registry_id, name)
                    result['changed'] = True

            elif policy_text is not None:
                try:
                    policy = sort_json_policy_dict(policy)
                    result['policy'] = policy

                    original_policy = ecr.get_repository_policy(
                        registry_id, name)
                    if original_policy:
                        original_policy = sort_json_policy_dict(original_policy)

                    if original_policy != policy:
                        ecr.set_repository_policy(
                            registry_id, name, policy_text, force_set_policy)
                        result['changed'] = True
                except:
                    # Some failure w/ the policy. It's helpful to know what the
                    # policy is.
                    result['policy'] = policy_text
                    raise

        elif state == 'absent':
            result['name'] = name
            if repo:
                ecr.delete_repository(registry_id, name)
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
        registry_id=dict(required=False),
        state=dict(required=False, choices=['present', 'absent'],
                   default='present'),
        force_set_policy=dict(required=False, type='bool', default=False),
        policy=dict(required=False, type='json'),
        delete_policy=dict(required=False, type='bool',
                           removed_in_version='2.9'),
        purge_policy=dict(required=False, type='bool'),
        lifecycle_policy=dict(required=False, type='json'),
        purge_lifecycle_policy=dict(required=False, type='bool')))

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           mutually_exclusive=[
                               ['policy', 'delete_policy', 'purge_policy'],
                               ['lifecycle_policy', 'purge_lifecycle_policy']])

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 required for this module')

    ecr = EcsEcr(module)
    passed, result = run(ecr, module.params)

    if passed:
        module.exit_json(**result)
    else:
        module.fail_json(**result)


if __name__ == '__main__':
    main()

#!/usr/bin/python
# -*- coding: utf-8 -*

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
    - Manage Elastic Container Registry repositories.
requirements: [ boto3 ]
options:
    name:
        description:
            - The name of the repository.
        required: true
        type: str
    registry_id:
        description:
            - AWS account id associated with the registry.
            - If not specified, the default registry is assumed.
        required: false
        type: str
    policy:
        description:
            - JSON or dict that represents the new policy.
        required: false
        type: json
    force_set_policy:
        description:
            - If I(force_set_policy=false), it prevents setting a policy that would prevent you from
              setting another policy in the future.
        required: false
        default: false
        type: bool
    purge_policy:
        description:
            - If yes, remove the policy from the repository.
            - Alias C(delete_policy) has been deprecated and will be removed in Ansible 2.14
        required: false
        default: false
        type: bool
        aliases: [ delete_policy ]
    image_tag_mutability:
        description:
            - Configure whether repository should be mutable (ie. an already existing tag can be overwritten) or not.
        required: false
        choices: [mutable, immutable]
        default: 'mutable'
        version_added: '2.10'
        type: str
    lifecycle_policy:
        description:
            - JSON or dict that represents the new lifecycle policy
        required: false
        version_added: '2.10'
        type: json
    purge_lifecycle_policy:
        description:
            - if yes, remove the lifecycle policy from the repository
        required: false
        default: false
        version_added: '2.10'
        type: bool
    state:
        description:
            - Create or destroy the repository.
        required: false
        choices: [present, absent]
        default: 'present'
        type: str
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

- name: create immutable ecr-repo
  ecs_ecr:
    name: super/cool
    image_tag_mutability: immutable

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

- name: purge-lifecycle-policy
  ecs_ecr:
    name: needs-no-lifecycle-policy
    purge_lifecycle_policy: true
'''

RETURN = '''
state:
    type: str
    description: The asserted state of the repository (present, absent)
    returned: always
created:
    type: bool
    description: If true, the repository was created
    returned: always
name:
    type: str
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
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import boto_exception, compare_policies, sort_json_policy_dict
from ansible.module_utils.six import string_types


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
        self.ecr = module.client('ecr')
        self.sts = module.client('sts')
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

    def create_repository(self, registry_id, name, image_tag_mutability):
        if registry_id:
            default_registry_id = self.sts.get_caller_identity().get('Account')
            if registry_id != default_registry_id:
                raise Exception('Cannot create repository in registry {0}.'
                                'Would be created in {1} instead.'.format(registry_id, default_registry_id))

        if not self.check_mode:
            repo = self.ecr.create_repository(
                repositoryName=name,
                imageTagMutability=image_tag_mutability).get('repository')
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
                    printable = '{0}:{1}'.format(registry_id, name)
                raise Exception(
                    'could not find repository {0}'.format(printable))
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

    def put_image_tag_mutability(self, registry_id, name, new_mutability_configuration):
        repo = self.get_repository(registry_id, name)
        current_mutability_configuration = repo.get('imageTagMutability')

        if current_mutability_configuration != new_mutability_configuration:
            if not self.check_mode:
                self.ecr.put_image_tag_mutability(
                    repositoryName=name,
                    imageTagMutability=new_mutability_configuration,
                    **build_kwargs(registry_id))
            else:
                self.skipped = True
            self.changed = True

        repo['imageTagMutability'] = new_mutability_configuration
        return repo

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
                    printable = '{0}:{1}'.format(registry_id, name)
                raise Exception(
                    'could not find repository {0}'.format(printable))
            return

    def purge_lifecycle_policy(self, registry_id, name):
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


def sort_lists_of_strings(policy):
    for statement_index in range(0, len(policy.get('Statement', []))):
        for key in policy['Statement'][statement_index]:
            value = policy['Statement'][statement_index][key]
            if isinstance(value, list) and all(isinstance(item, string_types) for item in value):
                policy['Statement'][statement_index][key] = sorted(value)
    return policy


def run(ecr, params):
    # type: (EcsEcr, dict, int) -> Tuple[bool, dict]
    result = {}
    try:
        name = params['name']
        state = params['state']
        policy_text = params['policy']
        purge_policy = params['purge_policy']
        registry_id = params['registry_id']
        force_set_policy = params['force_set_policy']
        image_tag_mutability = params['image_tag_mutability'].upper()
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
                repo = ecr.create_repository(registry_id, name, image_tag_mutability)
                result['changed'] = True
                result['created'] = True
            else:
                repo = ecr.put_image_tag_mutability(registry_id, name, image_tag_mutability)
            result['repository'] = repo

            if purge_lifecycle_policy:
                original_lifecycle_policy = \
                    ecr.get_lifecycle_policy(registry_id, name)

                result['lifecycle_policy'] = None

                if original_lifecycle_policy:
                    ecr.purge_lifecycle_policy(registry_id, name)
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
                except Exception:
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
                    # Sort any lists containing only string types
                    policy = sort_lists_of_strings(policy)

                    result['policy'] = policy

                    original_policy = ecr.get_repository_policy(
                        registry_id, name)
                    if original_policy:
                        original_policy = sort_lists_of_strings(original_policy)

                    if compare_policies(original_policy, policy):
                        ecr.set_repository_policy(
                            registry_id, name, policy_text, force_set_policy)
                        result['changed'] = True
                except Exception:
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
    argument_spec = dict(
        name=dict(required=True),
        registry_id=dict(required=False),
        state=dict(required=False, choices=['present', 'absent'],
                   default='present'),
        force_set_policy=dict(required=False, type='bool', default=False),
        policy=dict(required=False, type='json'),
        image_tag_mutability=dict(required=False, choices=['mutable', 'immutable'],
                                  default='mutable'),
        purge_policy=dict(required=False, type='bool', aliases=['delete_policy'],
                          deprecated_aliases=[dict(name='delete_policy', version='2.14')]),
        lifecycle_policy=dict(required=False, type='json'),
        purge_lifecycle_policy=dict(required=False, type='bool')
    )
    mutually_exclusive = [
        ['policy', 'purge_policy'],
        ['lifecycle_policy', 'purge_lifecycle_policy']]

    module = AnsibleAWSModule(argument_spec=argument_spec, supports_check_mode=True, mutually_exclusive=mutually_exclusive)

    ecr = EcsEcr(module)
    passed, result = run(ecr, module.params)

    if passed:
        module.exit_json(**result)
    else:
        module.fail_json(**result)


if __name__ == '__main__':
    main()

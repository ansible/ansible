#!/usr/bin/python
# -*- coding: utf-8 -*-
# Written by Riadh Hamdi <rhamdi@redhat.com> <ryadh.hamdi@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = '''
module: git_subtree
short_description: Ansible module that mimic git subtree add/pull in an idempotent way.
description:
    - This module mimics the functionality of the git subtree command by adding a subtree from a source repository to a subdirectory in the main repository.
version_added: "2.16"
author:
    - Riadh Hamdi (@riadhhamdi) (rhamdi@redhat.com)
options:
    source:
        description:
            - The source repository to pull the subtree from.
        required: true
        type: str
    ref:
        description:
            - The repository ref while adding or pulling subtree. Example a branch (main,develop..) of a specific tag
        required: true
        type: str
    prefix:
        description:
            - The prefix to use for the subtree directory in the main repository.
        required: true
        type: str
    squash:
        description:
            - A boolean flag indicating whether to squash the subtree history into a single commit in the main repository.
        type: bool
        default: false
    commit_message:
        description:
            - The commit message to use when committing the subtree changes to the main repository.
        default: ''
        type: str
    working_directory:
        description:
            - The working directory in which to execute the git command.
        default: null
        type: str
'''

EXAMPLES = '''
- name: Add/Pull a subtree to the main repository using http
  git_subtree:
    source: https://github.com/example/repo.git
    ref: main
    prefix: mydirectory
    squash: true
    commit_message: "Add subtree from example/repo"
    working_directory: /path/to/main/repository
- name: Add/Pull a subtree to the main repository using ssh
  git_subtree:
    source: git@github.com/example/repo.git
    ref: main
    prefix: mydirectory/somesubdirectory
    squash: true
    commit_message: "Add subtree from example/repo using ssd"
    working_directory: /path/to/main/repository
- name: Add/Pull a subtree to the main repository using http and disabling git password prompt
  git_subtree:
    source: https://github.com/example/repo.git
    ref: main
    prefix: mydirectory/somesubdirectory
    squash: true
    commit_message: "Add subtree from example/repo using ssd"
    working_directory: /path/to/main/repository
  environment:
    GIT_TERMINAL_PROMPT: 0
- name: Add/Pull multiple subtrees to the main repository using http and disabling git password prompt
  git_subtree:
    source: "{{item.source}}"
    ref: "{{item.ref}}"
    prefix: "{{item.prefix}}"
    squash: true
    commit_message: "Adding role {{item.prefix}} to the collection"
    working_directory: /path/to/main/collection_repository
  environment:
    GIT_TERMINAL_PROMPT: 0
  vars:
    roles_repositories:
      - source: https://github.com/example/role1.git
        squash: true
        ref: main
        prefix: roles/role1
      - source: https://github.com/example/role2.git
        squash: true
        ref: develop
        prefix: roles/role2
      - source: https://github.com/example/role3.git
        squash: true
        ref: 1.0.4
        prefix: roles/role3
- name: Add/Pull a subtree with authentication (read only token)
  git_subtree:
    source: https://0auth:ghp_2234xxxxxxxxxx5@github.com/example/repo.git
    ref: main
    prefix: mydirectory/somesubdirectory
    squash: true
    commit_message: "Add subtree from example/repo using ssd"
    working_directory: /path/to/main/repository
  environment:
    GIT_TERMINAL_PROMPT: 0
'''

RETURN = '''
msg:
  description: The response body content.
  returned: on success
  type: str
  sample: "{}"
'''

import os
from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            source=dict(required=True),
            ref=dict(required=True),
            prefix=dict(required=True),
            squash=dict(type='bool', default=False),
            commit_message=dict(default=''),
            working_directory=dict(default=None)
        ),
        supports_check_mode=False,
    )

    source = module.params['source']
    ref = module.params['ref']
    prefix = module.params['prefix']
    squash = module.params['squash']
    commit_message = module.params['commit_message']
    working_directory = module.params['working_directory']

    if not os.path.exists(os.path.join(working_directory, prefix)):
        command = ['git', 'subtree', 'add', '--prefix', prefix, source, ref]
        if squash:
            command.append('--squash')
        if commit_message:
            command.extend(['-m', commit_message])
        try:
            rc, stdout, stderr = module.run_command(command, cwd=working_directory, check_rc=True)
        except Exception as e:
            module.fail_json(msg="Error running command %s" % e.cmd, rc=e.returncode)
        mesg = stdout.strip()
        module.exit_json(
            changed=True,
            failed=False,
            msg='Added new subtree %s' % prefix,
            stdout=mesg,
            stderr='',
            rc=rc
        )
    else:
        # the subtree already exists, update it
        command = ['git', 'subtree', 'pull', '--prefix', prefix, source, ref]
        if squash:
            command.append('--squash')
        if commit_message:
            command.extend(['-m', commit_message])

        try:
            rc, stdout, stderr = module.run_command(command, cwd=working_directory, check_rc=True)
        except Exception as e:
            module.fail_json(msg="Error running command %s" % e.cmd, rc=e.returncode)
        if 'is already at commit' in stderr:
            mesg = stdout.strip()
            module.exit_json(
                changed=False,
                failed=False,
                msg="skipped since already at commit",
                stdout=mesg,
                stderr='',
                rc=rc
            )
        else:
            mesg = stdout.strip()
            module.exit_json(
                changed=True,
                msg='Updated existing subtree %s' % prefix,
                stdout=mesg,
                stderr='',
                rc=rc
            )
    return True


if __name__ == '__main__':
    main()
